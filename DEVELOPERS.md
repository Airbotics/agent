# Airbotics Agent

The agent is designed to run as a background service that is responsible for maintaining communications with:

1. Communicate with the MQTT broker in the airbotics cloud.
2. Communicate with the docker engine to on the host machine.
3. Communicate with ROS on the host machine.


## Dev environment setup
Ensure you follow these steps to get things set up in your dev environment.

* Run the ROS setup script or add it to your bashrc:


* Ensure MQTT broker is running locally, see backend README for latest info. 

* Ensure [config](#config) is set in either `config.toml` or ENV

* Create a python virtual environment

```
virtualenv venv
source venv/bin/activate
```

* Install the agent locally
```
pip3 install -e .
```

* Run the agent in [debug](#debug-flag) mode:
```
airbotics --debug
```



## Config
Config can be set from:
1. [TOML](#toml-file) in `~/.airbotics/config.toml`
2. [ENV](#env-variables) variables

Any config values set from ENV variables will overwrite values in the `config.toml`.

The following config can be set:

| Option | Default | Description| 
|--------|---------|------------|
| `AIR_ROBOT_ID`| | The ID of robot |
| `AIR_TENANT_UUID`|  | The ID of the tenant who owns the robot  |
| `AIR_TOKEN`|  | Auth token for robot to authenticate with |
| `AIR_ENABLE_CONTAINERS`| `true` | Connect agent to the docker daemon |
| `AIR_ROS_DISTRO`| `humble` | ROS distro |
| `AIR_MQTT_HOST`| `127.0.0.1` | The MQTT host |
| `AIR_MQTT_PORT`| `1883` | The MQTT port  |
| `AIR_MQTT_KEEP_ALIVE`| `60` | The MQTT keep alive in seconds |
| `AIR_CONTAINER_REGISTRY_URL`| `https://index.docker.io/v1/` | Private container registry url |
| `AIR_CONTAINER_REGISTRY_USERNAME`|  | Private container registry username |
| `AIR_CONTAINER_REGISTRY_PASSWORD`|  | Private container registry password |



### TOML file
To set configuration with a `config.toml` in the same directory as `airbotics`:
```
robot_id = "test-bot"
tenant_uuid = "0000"
token = "art_1234"
enable_containers = true

[ros]
distro = "humble"

[mqtt]
host = "127.0.0.1"
port = 1883
keep_alive = 60

[container_registry]
url = 'https://registry.hub.docker.com'
username = 'test'
password = 'test'
```

### ENV variables
To set configuration with environment variables:
```
AIR_ROBOT_ID = '1234'
AIR_TENANT_UUID = '1234'
AIR_TOKEN = '1234'
AIR_ENABLE_CONTAINERS = false

AIR_ROS_DISTRO = 'humble'

AIR_MQTT_HOST = '127.0.0.1'
AIR_MQTT_PORT = 1883
AIR_MQTT_KEEP_ALIVE = 60

AIR_CONTAINER_REGISTRY_URL = 'https://registry.hub.docker.com'
AIR_CONTAINER_REGISTRY_USERNAME = 'test'
AIR_CONTAINER_REGISTRY_PASSWORD = 'test'
```


## `debug` and `daemonize` flags
When running with `--debug` flag, the agent will log at the *debug* level and up, otherwise, it will log at *info* and above.

When `--daemonize` is set, the agent will be daemonized and will detatch itself from the terminal. The log output is written to `~/.airbotics/airboticsd.log`. 

A PID file will be written to `~/.airbotics/airboticsd.pid`.

To stop the daemonized agent run:
```
kill $(cat ~/.airbotics/airboticsd.pid)
```

<!--

## MQTT Topics

All topics follow the format: 
```
<api-version>/<team-id>/<bot-id>/<topic>
```

So for example a robot with the id `0000` in team `0000` publishing to the `diagnosis` topic on version `v1` of the API  would publish to the following:

```
v1/0000/0000/diagnosis
```

### Subscribed topics

| Topic | Description | Payload | QoS | 
|-------|-------------|---------|-----|
| `cmd`   | Publish to a ROS topic OR start a ROS action OR start a ROS service | `{ "key": "value1", "key2": "value2" }`  | 0 |
|  | *coming soon* | *coming soon*  | 0 |



## Testing

Publish mqtt message
```
mosquitto_pub -h localhost -t <api_version>/<teanant_id>/<bot_id>/<topic> 

mosquitto_pub -h localhost -t v0/11111111-1111-1111-1111-111111111111/violet/test -m 'test' -u air-backend -P pass

```

## Running in container
** Not worried about running in a container fow now! **

```
# build for noetic
docker build -t airbotics/agent-noetic .

# start the container
docker run -it --name agent --rm --network=host \
    -v /var/run/docker.sock:/var/run/docker.sock \
    airbotics/agent-noetic

# run the agent
python3 airboticsd.py -d -r noetic
```
-->







