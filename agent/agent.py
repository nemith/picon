#! /usr/bin/env python3
from agent import APIClient
import argparse
from daemonize import Daemonize
#import logger

HOLDTIME=60
DELAY=5

pid = "/tmp/picon-agent.pid"

parser = argparse.ArgumentParser(description = 'Run a PiCon agent')
parser.add_argument('-d',dest='daemonize',action='store_true',help="Run in background [default: run in foreground]")

args = parser.parse_args()


def main():
    a = APIClient.APIClient('http://199.187.221.170:5000/api/',holdtime=HOLDTIME,delay=DELAY)
    a.run()


if args.daemonize:
    daemon = Daemonize(app="picon-agent", pid=pid, action=main)
    daemon.start()
else:
    main()



