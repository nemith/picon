#! /usr/bin/env python3
from piconagent.piconagent import PiConAgent
import argparse
from daemonize import Daemonize
import logging

parser = argparse.ArgumentParser(description = 'Run a PiCon agent')
parser.add_argument('endpoint',type=str, help='Base URL of the PiCon server API, e.g. http://picon.example.com/api/')
parser.add_argument('--daemonize',action='store_true',help='Run in background [default: False]')
parser.add_argument('--tunnel',action='store_true',help='Open a reverse SSH tunnel to the server [default: False]')
parser.add_argument('--holdtime',type=int,help='Hold time: seconds for the server to wait before declaring this device unavailable [default: 300]', default=300)
parser.add_argument('--interval',type=int,help='Interval: seconds between registrations [default: 60]',default=60)
parser.add_argument('--pidfile',type=str,help='PID File: PID file location, used only if daemonizing [default: /tmp/picon-agent.pid]',default='/tmp/picon-agent.pid')
parser.add_argument('--logfile',type=str,help='Log File: log file location, [default: None]',default=None)
parser.add_argument('-d',dest='debug',action='store_true',help='Debug: Maximum verbosity (overrides -v)')
parser.add_argument('-v',dest='verbose',action='count',help='Verbose Level: Repeat up to 3 times')

args = parser.parse_args()

def loggingLevelFromVerboseCount(vcount):
    if vcount is None:
        return logging.ERROR
    elif vcount == 1:
        return logging.WARNING
    elif vcount == 2:
        return logging.INFO
    elif vcount >= 3:
        return logging.DEBUG
    else:
        logger.critical('Undefined Verbosity Level: '+vcount)
        return logging.ERROR

def main():
    logLevel = loggingLevelFromVerboseCount(args.verbose)
    if args.debug:
        logLevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',level=logLevel,filename=args.logfile)
    logging.info('Starting PiCon Agent...')
    a = PiConAgent(args.endpoint,holdtime=args.holdtime,interval=args.interval,tunnel=args.tunnel)
    logging.info("Using endpoint %ss, holdtime %ss, reporting interval %s" % (args.endpoint,a.holdtime,a.interval))
    a.run()


if args.daemonize:
    daemon = Daemonize(app='picon-agent', pid=args.pidfile, action=main)
    daemon.start()
    logging.info("Daemonized, PID (%s) can be found at %s" % args.pidfile)
else:
    main()



