#! /usr/bin/env python3
from piconagent.piconagent import PiConAgent
import argparse
from daemonize import Daemonize
import logging


parser = argparse.ArgumentParser(description = 'Run a PiCon agent')
parser.add_argument('endpoint',type=str, help='Base URL of the PiCon server API, e.g. http://picon.example.com/api/')
parser.add_argument('--daemonize',dest='daemonize',action='store_true',help='Run in background [default: run in foreground]')
parser.add_argument('--holdtime',type=int,help='Hold time: seconds for the server to wait before declaring this device unavailable [default: 300]', default=300)
parser.add_argument('--interval',type=int,help='Interval: seconds between registrations [default: 60]',default=60)
parser.add_argument('--pidfile',type=str,help='PID File: PID file location, used only if daemonizing [default: /tmp/picon-agent.pid]',default='/tmp/picon-agent.pid')

args = parser.parse_args()

def main():
    a = PiConAgent(args.endpoint,holdtime=args.holdtime,interval=args.interval)
    a.run()


if args.daemonize:
    daemon = Daemonize(app='picon-agent', pid=args.pidfile, action=main)
    daemon.start()
    logging.info("Daemonized, PID can be found at %s" % args.pidfile)
else:
    main()



