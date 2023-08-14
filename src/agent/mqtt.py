from datetime import datetime
import sys
import json
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
from agent.logger import AirLogger
from agent import MQTT_API_VERSION, AGENT_VERSION



class AirMqtt:

    cloud_to_bot_topics = [
        'commands/send',
        'containers/config',
        'logs/config',
        'data/config',
        'vitals/config'
    ]

    bot_to_cloud_topics = {
        'presence': 'presence',
        'cmd_confirm': 'commands/confirm',
        'container_confirm': 'containers/confirm',
        'logs_ingest': 'logs/ingest',
        'vitals_ingest': 'vitals/ingest',
        'data_ingest': 'data/ingest'
    }


    def __init__(self, config, on_msg) -> None:
    	
        self.config = config
        self.on_msg = on_msg
        self.logger = AirLogger(__name__, config).logger
        
        # config client
        mqtt_uname = f"{self.config['tenant_uuid']}-{self.config['robot_id']}"
        self.mqtt_client = mqtt.Client(client_id=mqtt_uname, protocol=mqtt.MQTTv5)
        self.mqtt_client.username_pw_set(mqtt_uname, self.config['token'])

        # configure tls
        if self.config['mqtt']['host'] != '127.0.0.1':
            self.mqtt_client.tls_set()


        # Set user properties
        self.properties = Properties(PacketTypes.PUBLISH)
        self.properties.UserProperty = [('air-mqtt-version', MQTT_API_VERSION)]

        # config last will and testament
        will_topic = f"{self.config['tenant_uuid']}/{self.config['robot_id']}/{self.bot_to_cloud_topics['presence']}"
        will_payload = json.dumps(self.presence_payload(False))
        self.mqtt_client.will_set(will_topic, will_payload, 0, properties=self.properties)

        # set callbacks
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_connect_fail = self.on_connect_fail
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_message = self.on_message
        
        # Attempt connection
        try:
            self.logger.debug(f"attempting to connect to {self.config['mqtt']['host']}:{self.config['mqtt']['port']}")
            self.mqtt_client.connect(self.config['mqtt']['host'], int(self.config['mqtt']['port']), self.config['mqtt']['keep_alive'])
        except:
            self.logger.exception("exception while connecting to the mqtt broker")
            
        # start thread to process network traffic
        self.mqtt_client.loop_start()

  
    def on_connect(self, client, userdata, flags, rc, properties=None):
        self.logger.info("connected to mqtt broker")
        
        for topic in self.cloud_to_bot_topics:
            self.mqtt_client.subscribe(f"{self.config['tenant_uuid']}/{self.config['robot_id']}/{topic}", 0)
        
        self.pub(self.bot_to_cloud_topics['presence'], self.presence_payload(True), 0)
        

    def on_connect_fail(self, client, userdata):
        self.logger.warning("failed connection to mqtt broker")


    def on_disconnect(self, client, userdata, rc, properties=None):
        self.logger.warning(f"disconnected from mqtt broker with rc: {mqtt.error_string(rc)}")


    def on_message(self, client, userdata, msg):
        self.logger.info(f"received message")
        # strip out the <tenant_uuid>/<robot_id>
        short_topic = '/'.join(msg.topic.split('/')[2:])
        data = None
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except:
            self.logger.exception("could not json load mqtt message")
            return
        
        return self.on_msg(short_topic, data)
        

    def pub(self, short_topic, payload, qos):
        topic = f"{self.config['tenant_uuid']}/{self.config['robot_id']}/{short_topic}"
        self.mqtt_client.publish(topic, json.dumps(payload), qos, properties=self.properties)
        self.logger.debug(f'published message on {short_topic}')

    
    def presence_payload(self, online: bool):
        return { 
            'online': online,
            'agent_version': AGENT_VERSION
        }
