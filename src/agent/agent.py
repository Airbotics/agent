import datetime
from rosidl_runtime_py import message_to_ordereddict
from agent.logger import AirLogger
from agent.json_message_converter import convert_ros_message_to_json
from agent.mqtt import AirMqtt
from agent.config import AirConfig
from agent.containers import AirContainers
from agent.ros.humble import AirRosHumble
from jsonschema import validate, ValidationError
from agent.schemas import command_schema, container_update_schema
from agent.vitals import AirVitals


class AirAgent:

    def __init__(self, daemonize: bool, debug: bool) -> None:
        self.config = AirConfig(daemonize, debug).config
        self.containers = AirContainers(self.config)
        self.ros = AirRosHumble(self.config, self.on_log)
        self.mqtt = AirMqtt(self.config, self.on_mqtt_msg)
        self.vitals = AirVitals(self.config, self.on_vitals)
        self.logger = AirLogger(__name__, self.config).logger
        self.collect_logs = False
        self.collect_vitals = False
        self.data_subscriptions = {}


    def spin(self):
        self.ros.spin()


    # Callback handler for mqtt msg
    def on_mqtt_msg(self, topic, data):
        if topic == 'commands/send': 
            result = self.handle_cmd(data)
            result['uuid'] = data['uuid']
            self.mqtt.pub(self.mqtt.bot_to_cloud_topics['cmd_confirm'], result, 0)
        
        elif topic == 'containers/config':
            result = self.handle_container_update(data)
            result['uuid'] = data['uuid']
            self.mqtt.pub(self.mqtt.bot_to_cloud_topics['container_confirm'], result, 0)
        
        elif topic == 'logs/config':
            should_collect = data['enabled']
            self.logger.info(f'updating log configuration to {should_collect}')
            self.collect_logs = should_collect
        
        elif topic == 'vitals/config':
            should_collect = data['enabled']
            self.logger.info(f'updating vitals configuration to {should_collect}')
            self.collect_vitals = should_collect

        elif topic == 'data/config':
            self.ros.clear_data_subscriptions()
            self.data_subscriptions = {}
            
            for stream in data:
                source = stream['source']
                msg_type = stream['type']
                hz = stream['hz']
                self.data_subscriptions[source] = {
                    'msg_type': source,
                    'hz': hz,
                    'last_sent': None
                }
                self.ros.subscribe(source, msg_type, lambda msg, source=source: self.on_data_callback(msg, source))
                self.logger.info(f'subscribing to {source}') 

            self.logger.info(f'updating data configuration')

        else:
            self.logger.error(f"unhandled mqtt msg for topic: {topic}")


    def on_data_callback(self, msg, source):

        last_sent = self.data_subscriptions[source]['last_sent']
        now = datetime.datetime.now()
        send = False

        if not last_sent:
            self.data_subscriptions[source]['last_sent'] = now
            send = True
        
        diff = (now - self.data_subscriptions[source]['last_sent']).total_seconds()*1000
        period = (1 / self.data_subscriptions[source]['hz'])*1000

        if diff > period:
            self.data_subscriptions[source]['last_sent'] = datetime.datetime.now()
            send = True

        if send:
            stamp = datetime.datetime.now().isoformat() + 'Z'

            try:
                data = message_to_ordereddict(msg)
            except:
                self.logger.exception('cannot parse ros message')
                return

            payload = {
                "sent_at": stamp,
                "source": source,
                "payload": data
            }

            self.mqtt.pub(self.mqtt.bot_to_cloud_topics['data_ingest'], payload, 1)


    # Callback handler for ros log msg
    def on_log(self, msg):

        def ros_level(level: int):
            if level==10: return 'debug'
            elif level==20: return 'info'
            elif level==30: return 'warn'
            elif level==40: return 'error'
            if level==50: return 'fatal'

        stamp = datetime.datetime.utcfromtimestamp(msg.stamp._sec).isoformat() + 'Z'

        log_msg = {
            'msg': msg.msg,
            'level': ros_level(msg.level),
            'name': msg.name,
            'file': msg.file,
            'function': msg.function,
            'line': msg.line,
            'stamp': stamp
        }
        self.logger.debug(log_msg)
        
        if self.collect_logs:
            self.mqtt.pub(self.mqtt.bot_to_cloud_topics['logs_ingest'], log_msg, 1)
        

    def on_vitals(self, vitals):
        if self.collect_vitals:
            self.mqtt.pub(self.mqtt.bot_to_cloud_topics['vitals_ingest'], vitals, 0)
    

    def handle_cmd(self, data):
        
        try:
            validate(instance=data, schema=command_schema)
        except ValidationError as e:
            self.logger.exception("invalid command schema")
            return { 'success': False, 'failure_reason': 'unknown_error' }
        
        if data['interface'] == 'topic':
            return self.ros.pub_topic(data['name'], data['type'], data['payload'])

        elif data['interface'] == 'service':
            return self.ros.call_service(data['name'], data['type'], data['payload'])

        elif data['interface'] == 'action_send_goal':
            return self.ros.action_send_goal(data['name'], data['type'], data['payload'])
        

    def handle_container_update(self, data):
        try:
            validate(instance=data, schema=container_update_schema)
        except ValidationError as e:
            self.logger.exception("invalid container_update_schema")
            return { 'success': False, 'failure_reason': 'unknown_error' }
        
        if data['compose'] == None:
            return self.containers.remove_compose()
        
        else:
            return self.containers.put_compose(data['compose'])
        
