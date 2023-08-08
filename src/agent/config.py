from os import environ, path
from agent.logger import AirLogger
from agent import AIR_PATH
import toml
import sys

class AirConfig:
    """
    Config is read in this order from the following
            1) config.toml
            2) env variables on the host
    
    Config set in environment variables will overwrite config.toml
    """

    config = {
        'debug': False,
        'daemonize': False,
        'robot_id': '',
        'tenant_uuid': '',
        'token': '',
        'enable_containers': True,
        'enable_vitals': True,
        'ros': {
            'distro': ''
        },
        'mqtt': {
            'host': 'o526e215.eu-central-1.emqx.cloud',
            'port': 15603,
            'keep_alive': 60
        },
        'container_registry': {
            'url': 'https://index.docker.io/v1/',
            'username': '',
            'password': ''
        }
    }

    def __init__(self, daemonize, debug) -> None:
        self.config['daemonize'] = daemonize
        self.config['debug'] = debug
        self.logger = AirLogger(__name__, self.config).logger
        self.parse_toml()
        self.parse_env()
        self.ensure_creds()


    def parse_toml(self):
        try:
            toml_config = toml.load(path.join(AIR_PATH, 'config.toml'))
            for parent_key, parent_val in toml_config.items():
                if isinstance(parent_val, dict):
                    for child_key, child_val in parent_val.items():
                        self.config[parent_key][child_key] = child_val
                else: 
                    self.config[parent_key] = parent_val
            self.logger.debug('parsed config.toml')
        except:
            self.logger.warning('No config.toml found')



    def parse_env(self):
        for parent_key in self.config:
            env_key = f'AIR_{parent_key.upper()}'
            if env_key in environ:
                self.config[parent_key] = self.check_for_bool(environ.get(env_key))
            elif isinstance(self.config[parent_key], dict):
                for child_key in self.config[parent_key]:
                    env_key = f"AIR_{parent_key.upper()}_{child_key.upper()}"
                    if env_key in environ:
                        self.config[parent_key][child_key] = self.check_for_bool(environ.get(env_key))
        self.logger.debug('parsed env config')


    def ensure_creds(self):
        if not self.config['robot_id'] or not self.config['tenant_uuid'] or not self.config['token']:
            self.logger.critical('ROBOT_ID, TENANT_UUID and TOKEN must be set in your environment')
            sys.exit(1)


    def check_for_bool(self, val):
        if val in ('True', 'true', 1):
            return True
        elif val in ('False', 'false', 0):
            return False
        return val