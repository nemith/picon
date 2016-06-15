import traceback
import piconagent.sshchannelthread as sshchannelthread
import piconagent.utils as utils
from time import sleep
import logging
import math
import json,requests

class PiConAgent():
    def __init__(self,endpoint='http://localhost/api/',headers={'content-type': 'application/json'},holdtime=300,interval=60,tunnel=False,tunnelserver=None,tunnelport=None):
        # requests is too noisy for INFO
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('requests').setLevel(logging.WARN)
        self.endpoint = endpoint
        self.headers = headers
        self.holdtime = holdtime
        self.interval = interval
        self.tunnel = tunnel
        self.tunnelserver = tunnelserver
        self.tunnelport = tunnelport
        self.sshChannelThread = None
    def register(self):
        body = {}
        body['hostname'] = utils.getHostname()
        body['sn'] = utils.getSerial()
        try:
            body['interfaces'] = utils.getInterfaces()
        except Exception as e:
            logging.error('Skipping this registration attempt because:  ' + str(e))
            logging.error("%d failed attempts in a row will result in the server declaring us dead (holdtime: %d, registration interval: %d)" % (math.ceil(self.holdtime/self.interval),self.holdtime,self.interval))
            return False
        body['ports'] = utils.getPorts()
        body['holdtime'] = self.holdtime
        jsonbody = json.dumps(body,sort_keys=True,indent=2)
        try:
            r = requests.post(self.endpoint+'register', data = jsonbody, headers = self.headers,timeout=2)
        except Exception as e:
            logging.error('PiCon registration attempt failed: ' + str(e))
            return False
        else:
            logging.info('Successfully registered with endpoint ' + self.endpoint+'register')
            logging.debug('Sent JSON in POST body:' + "\n" +  jsonbody)
            logging.debug('Received JSON in POST response:' + "\n" +  r.text)
            rjson = r.json()
            if rjson is not None and 'tunnel' in rjson  and 'server' in rjson['tunnel']:
                self.tunnelserver=rjson['tunnel']['server']
            if rjson is not None and 'tunnel' in rjson  and 'port' in rjson['tunnel']:
                self.tunnelport=rjson['tunnel']['port']
            return True

    def run(self):
        while True:
            self.register()
            if (not self.sshChannelThread or not self.sshChannelThread.is_alive()) and self.tunnel:
                if self.sshChannelThread is None:
                    self.sshChannelThread=sshchannelthread.sshChannelThread(tunnelserver=self.tunnelserver,tunnelport=2222)
                    self.sshChannelThread.start()
                else:
                    logging.error("SSH tunnel connection closed unexpectedly, restarting...")
                    self.sshChannelThread=sshchannelthread.sshChannelThread(tunnelserver=self.tunnelserver,tunnelport=2222)
                    self.sshChannelThread.start()
            sleep(self.interval)

def main():
    # create an agent and register
    a = PiConAgent('http://199.187.221.170:5000/api/')
    a.register()
    sys.stderr.write(PiConAgent.jsonbody)

if __name__ == "__main__":
    main()

