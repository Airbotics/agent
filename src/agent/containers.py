import sys
import os
import threading
import docker
from docker.models.images import Image
from docker.models.containers import Container
from agent import AIR_PATH
from agent.logger import AirLogger
import subprocess
import json

class AirContainers:

    # AIR_DEV_REPOSITORY = "airbotics/agent"
    COMPOSE_PATH = os.path.join(AIR_PATH, "docker-compose.json")


    def __init__(self, config) -> None:

        self.logger = AirLogger(__name__, config).logger

        if config['enable_containers'] == False:
            self.logger.info('containers not enabled')
            return
        
        if config['container_registry']['password'] != '':
            res_login = subprocess.run(['docker', 'login', config['container_registry']['url'], 
                            '-u', config['container_registry']['username'], 
                            '-p', config['container_registry']['password']], 
                            capture_output=True, text=True)
            if res_login.returncode != 0:
                self.logger.error('unable to log into private container registry')
            else:
                self.logger.info('logged into private container registry')
                

        try:
            self.docker_client = docker.from_env()
            self.logger.debug("docker client connected")
        except:
            self.logger.exception("unable to connect to docker client")
            sys.exit(1)

        self.start_containers()

        # Start a background thread to listen for docker events
        # event_thread = threading.Thread(target=self.listen_for_events, daemon=True)
        # event_thread.start()


    def start_containers(self) -> dict:
        
        # If there's a docker-compose present, try and up it 
        if os.path.exists(self.COMPOSE_PATH):
            self.logger.info(f'attempting docker compose up')
            up_res= subprocess.run(['docker', 'compose', '-f', self.COMPOSE_PATH, 'up', '-d'], capture_output=True, text=True)
            if up_res.returncode != 0:
                self.logger.error(up_res.stderr)
                return { 'state': 'error', 'error_code': 'compose_up' }
            return { 'state': 'up', 'error_code': None }
    
        else:
            self.logger.info('no containers to start')
            return { 'state': 'down', 'error_code': None }


    
    def put_compose(self, compose_json) -> dict:
        
        # If theres already a docker-compose, attempt to down it
        remove_res = self.remove_compose()

        if(remove_res['state'] == 'error'):
            return remove_res
        
        # write or overwrite the new compose
        with open(self.COMPOSE_PATH, 'w') as compose_file:
            json.dump(compose_json, compose_file)

        return self.start_containers()

    def remove_compose(self) -> dict:
        if os.path.exists(self.COMPOSE_PATH):
            self.logger.info(f'attempting docker compose down')
            down_res = subprocess.run(["docker", "compose", "-f", self.COMPOSE_PATH, "down", "--rmi", "all"], capture_output=True, text=True)
            if down_res.returncode != 0:
                self.logger.error(down_res.stderr)
                return { 'state': 'error', 'error_code': 'compose_down' }
            else:
                os.remove(self.COMPOSE_PATH)
                return { 'state': 'down', 'error_code': None }
        return { 'state': 'down', 'error_code': None }


    def list_containers(self):
        containers = []
        for container in self.docker_client.containers.list(filters={"status": "running"}):
            containers.append({ 'name': container.name, 'image': container.image, 'status': container.status })
        # self.docker_client.containers.list(all=True)
        
        self.logger.info("attempting to pull image")

    
    # def list_images(self):
    #     def get_tag(image: Image):
    #         return image.tags[0] if image.tags else image.id

    #     try:
    #         images = self.docker_client.images.list()
    #         return list(map(get_tag, images))

    #     except:
    #         self.logger.exception("unable to list images")
    #         return []

    
    # def pull_image(self, repo, image, tag):
    #     self.logger.info("attempting to pull image")

    
    # def delete_image(self, repo, image, tag):
    #     self.logger.info("attempting to pull image")

    
    # def delete_image(self, repo, image, tag):
    #     self.logger.info("attempting to pull image")

    
    # def listen_for_events(self):
    #     for event in self.docker_client.events(decode=True):
    #         if event["Type"] == "container":
    #             self.logger.info(f"container event received")
    #         else:
    #             self.logger.debug(f"docker event type {event['Type']}, ignored")


    '''
    If agent is running in a container, this can check for a single instance

    def ensure_single_instance(self):
        try:
            # Check if this container is already running on the host
            running_containers = self.docker_client.containers.list(
                filters={"status": "running", "ancestor": self.AIR_DEV_REPOSITORY}
            )
            if len(running_containers) > 1:
                self.logger.critical(
                    f"A container from the {self.AIR_DEV_REPOSITORY} image is already running!"
                )
                sys.exit(1)
            self.logger.debug("single instance ensured")
        except:
            self.logger.exception("could not verify container single instance")
            sys.exit(1)
    '''