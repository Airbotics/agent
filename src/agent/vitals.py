import psutil
import shutil
import time
import threading
from agent.logger import AirLogger
import socket
import urllib.request

class AirVitals:

    vitals = {
        'cpu': 0,
        'ram': 0,
        'disk': 0,
        'battery': 0,
        'local_ip': '',
        'public_ip': '',        
    }

    def __init__(self, config, on_vitals) -> None:   	
        self.logger = AirLogger(__name__, config).logger
        self.on_vitals = on_vitals

        if config['enable_vitals']:
            self.logger.debug('vitals enabled')
            vitals_thread = threading.Thread(target=self.monitor_vitals, daemon=True)
            vitals_thread.start()
        else: 
            self.logger.debug('vitals disabled')

    
    def monitor_vitals(self):
        
        while True:

            self.vitals['cpu'] = psutil.cpu_percent()
            self.vitals['ram'] = psutil.virtual_memory().percent
            self.vitals['disk'] = round((shutil.disk_usage('/').used / shutil.disk_usage('/').total)*100, 2)

            if psutil.sensors_battery():
                self.vitals['battery'] = round(psutil.sensors_battery().percent, 2)
        
            try:
                self.vitals['local_ip'] = socket.gethostbyname(socket.gethostname())
            except socket.gaierror:
                self.logger.warning('unable to get local IP')

            try: 
                self.vitals['public_ip'] = urllib.request.urlopen('https://ident.me').read().decode('utf8')
            except: 
                self.logger.warning('unable to get public IP')

            self.on_vitals(self.vitals)
    
            time.sleep(1)

