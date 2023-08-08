#!/usr/bin/env python3
import os
import daemon
import daemon.pidfile
import pyfiglet
from datetime import datetime
from argparse import ArgumentParser, Namespace
from agent import AGENT_VERSION, MQTT_API_VERSION, AIR_PATH
from agent.agent import AirAgent


def main() -> None:
    """
    Entry point into the agent
    """
    parser = ArgumentParser()

    parser.add_argument(
        "--daemonize",
        dest="daemonize",
        help="daemonize the agent",
        default=False,
        action="store_true"
    )

    parser.add_argument(
        "--debug",
        dest="debug",
        help="Run the agent in debug mode",
        default=False,
        action="store_true"
    )

    args: Namespace = parser.parse_args()

    if not os.path.exists(AIR_PATH):
        os.makedirs(AIR_PATH)
    
    print(pyfiglet.figlet_format("Airbotics"))
    print("The Airbotics agent")
    print(f"Copyright Airbotics Inc. {datetime.now().year}")
    print(f"Agent Version: {AGENT_VERSION}, MQTT API Version {MQTT_API_VERSION}")
    print("Read the docs at: https://docs.airbotics.io")
    
    if args.daemonize == False:
        try:
            agent = AirAgent(args.daemonize, args.debug)
            agent.spin()
        except KeyboardInterrupt:
            print("agent killed by keyboard interrupt")
    else:
        pid_file = os.path.join(AIR_PATH, "airboticsd.pid")
        print(f"This will process disassociate from terminal, check {pid_file} for pid")
        with daemon.DaemonContext(pidfile=daemon.pidfile.PIDLockFile(pid_file)):
            agent = AirAgent(args.daemonize, args.debug)
            agent.spin()



if __name__ == "__main__":
	main() 