from agent.logger import AirLogger
from typing import Callable, List, Dict
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rcl_interfaces.msg import Log
import importlib
import sys
import distro
from agent.ros import SUPPORTED_DISTRO_ID, SUPPORTED_DISTRO_VER
from agent import message_converter


class AgentNode(Node):

    def __init__(self):
        super().__init__("airbotics_agent")



class AirRosHumble:

    primitives = ('bool', 'byte', 'char', 'float32', 'float64', 'float',
              'int', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'double',
              'uint32', 'int64', 'uint64', 'string', 'wstring')
    
    float_types = ('float32', 'float64', 'float', 'double')
    

    def __init__(self, config, on_log):
        self.logger = AirLogger(__name__, config).logger
        self.check_distro()
        self.on_log = on_log
        rclpy.init(args=None)
        self.node = AgentNode()
        self.rosout_sub = self.node.create_subscription(Log, '/rosout', self.log_callback, 1)
        self.data_subscriptions = []


    def spin(self):
        rclpy.spin(self.node)


    def check_distro(self):
        if distro.id() != SUPPORTED_DISTRO_ID or distro.version() != SUPPORTED_DISTRO_VER:
            self.logger.critical(f'Incompatible distro, Airbotics only supports {SUPPORTED_DISTRO_ID}: {SUPPORTED_DISTRO_VER}')
            sys.exit(1)
        else:
            self.logger.debug('linux Distro OK')

    # LOGS
    def log_callback(self, msg):
        self.on_log(msg)

    
    # DATA
    def subscribe(self, topic, msg_type, callback):

        try:
            mod_name = msg_type.split('/')[0]
            class_name = msg_type.split('/')[2]
            mod = importlib.import_module(mod_name + '.msg')
            msg_class = getattr(mod, class_name)
            sub = self.node.create_subscription(msg_class, topic, callback, 1)
            self.data_subscriptions.append(sub)

        except ImportError as e:
            self.logger.error(e)

        except AttributeError as e:
            self.logger.error(e)
        
        except KeyError as e:
            self.logger.error(e)

        except:
            self.logger.exception(f'topic subscription failed for: {topic}')
    

    def clear_data_subscriptions(self):
        for sub in self.data_subscriptions:
            self.node.destroy_subscription(sub)
        self.data_subscriptions = []
    
    # TOPICS
    def pub_topic(self, topic:str, msg_type:str, msg_args:dict) -> dict:
     
        try:
            msg = message_converter.convert_dictionary_to_ros_message(msg_type, msg_args)
            publisher = self.node.create_publisher(msg.__class__, topic, 10)
            publisher.publish(msg)
            self.logger.info(f'published to ROS topic: {topic}')
            return { 'success': True, 'error_code': None }
        
        except ImportError as e:
            self.logger.error(e)
            return { 'success': False, 'error_code': 'invalid_type' }

        except AttributeError as e:
            self.logger.error(e)
            return { 'success': False, 'error_code': 'invalid_type' }
        
        except KeyError as e:
            self.logger.error(e)
            return { 'success': False, 'error_code': 'invalid_payload' }

        except:
            self.logger.exception(f'call topic failed: {topic}')
            return { 'success': False, 'error_code': 'unknown_error' }


    # SERVICES
    def call_service(self, srv_name:str, srv_type:str, srv_args:dict) -> dict:
    
        try:
            mod_name = srv_type.split('/')[0]
            class_name = srv_type.split('/')[2]
            mod = importlib.import_module(mod_name + '.srv')
            srv_class = getattr(mod, class_name)

            srv_req = message_converter.convert_dictionary_to_ros_message(srv_type, srv_args, kind='request')
   
            client = self.node.create_client(srv_class, srv_name)
    
            if client.service_is_ready():
                future = client.call_async(srv_req)
                future.add_done_callback(self.service_callback)
                self.logger.info(f'called service {srv_name}')
                return { 'success': True, 'error_code': None }
            
            else:
                self.logger.error(f'call service failed: {srv_name} is not ready')
                return { 'success': False, 'error_code': 'service_not_ready' }
        

        except ImportError as e:
            self.logger.error(e)
            return { 'success': False, 'error_code': 'invalid_type' }

        except AttributeError as e:
            self.logger.error(e)
            return { 'success': False, 'error_code': 'invalid_type' }
        
        except KeyError as e:
            self.logger.error(e)
            return { 'success': False, 'error_code': 'invalid_payload' }

        except:
            self.logger.exception(f'call service failed: {srv_name}')
            return { 'success': False, 'error_code': 'unknown_error' }



    def service_callback(self, future):
        try:
            result = future.result()
            self.logger.info('service call succeeded')
        except:
            self.logger.exception('service call failed')

    
    # ACTIONS
    def action_send_goal(self, act_name:str, act_type:str, act_args:dict):
        try:

            mod_name = act_type.split('/')[0]
            class_name = act_type.split('/')[2]

            # dynamically import module service module depending on payload
            mod = importlib.import_module(mod_name + '.action')
            action_class = getattr(mod, class_name)
            client = ActionClient(self.node, action_class, act_name)

            goal_msg = action_class.Goal()
            
            # Use the helper to populate the Goal with values from json
            self.derserialize_json(goal_msg, 'action', act_args)
            
            if client.server_is_ready():
                server_res_future = client.send_goal_async(goal_msg, self.action_feedback_callback)
                server_res_future.add_done_callback(self.action_response_callback)
                self.logger.info('sent goal to action server')
                return { 'success': True, 'error_code': None }
            else:
                self.logger.error('action server is not ready')
                return { 'success': False, 'error_code': 'action_server_not_ready' }

        except ImportError as e:
            self.logger.error(e)
            return { 'success': False, 'error_code': 'invalid_type' }

        except AttributeError as e:
            self.logger.error(e)
            return { 'success': False, 'error_code': 'invalid_type' }
        
        except KeyError as e:
            self.logger.error(e)
            return { 'success': False, 'error_code': 'invalid_payload' }

        except:
            self.logger.exception(f'action send goal failed: {act_name}')
            return { 'success': False, 'error_code': 'unknown_error' }
    
    
    def action_response_callback(self, server_res):
        self.logger.debug('action response callback')
        result = server_res.result()
        if result.accepted == True:
            self.logger.debug('action server accepted the request')
            action_res_future = result.get_result_async()
            action_res_future.add_done_callback(self.action_result_callback)
            # NOTE potentially send mqtt feedback
        else:
            self.logger.debug('action server did not accept')
            # NOTE potentially send mqtt feedback

    
    def action_feedback_callback(self, feedback_msg):
        self.logger.debug('action feedback callback')
        

    def action_result_callback(self, future):
        self.logger.debug('action result callback')

    

    # HELPERS
    def derserialize_json(self, ros_obj, ros_inter, json_args):
        '''
        Given a ROS Msg type and a corresponding json_args, this function will populate
        the RosMsg fields with the json_args. It will recursively call itself when it 
        encouters a RosMsg field that is not a primitive.
        '''

        if ros_obj._fields_and_field_types.keys() != json_args.keys():
            raise KeyError(f"payload does not contain correct keys for {ros_obj.__class__.__name__}")

        for field, field_type in ros_obj._fields_and_field_types.items():
               
            is_sequence = False
            
            # Is the field type a sequence, if so extract type from angle brackets
            if field_type.startswith("sequence"):
                field_type = field_type.split('sequence')[1][1:-1]
                is_sequence = True
            
            # If the field is a primative we can set it directly from the json
            if field_type in self.primitives:
                if not is_sequence and field_type in self.float_types:
                    json_args[field] = float(json_args[field])
                ros_obj.__setattr__(field, json_args[field])
            
            # If not we need to dynamically load the non primitive field type
            else:
                field_module_name, field_class_name = field_type.split("/")
                field_module = importlib.import_module(f'{field_module_name}.{ros_inter}')
                nested_msg = getattr(field_module, field_class_name)()

                # If not a sequence, we set the field to the result of the recursion
                if is_sequence == False:
                    ros_obj.__setattr__(field, self.derserialize_json(nested_msg, ros_inter, json_args[field]))
                

                # If it is a sequence, we set the field to the result of the list of recursions
                else:
                    nested_msgs = []
                    for elem in json_args[field]:
                        nested_msgs.append(self.derserialize_json(nested_msg, ros_inter, elem))
                    ros_obj.__setattr__(field, nested_msgs)
        
        return ros_obj