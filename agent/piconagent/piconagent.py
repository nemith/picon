import traceback
from .utils import *
from time import sleep
import logging

class PiConAgent():
    def __init__(self,endpoint='http://localhost/api/',headers={'content-type': 'application/json'},holdtime=300,interval=60):
        # requests is too noisy for INFO
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('requests').setLevel(logging.WARN)
        self.endpoint = endpoint
        self.headers = headers
        self.holdtime = holdtime
        self.interval = interval
    def register(self):
        body = {}
        body['hostname'] = getHostname()
        body['sn'] = getSerial()
        body['interfaces'] = getInterfaces()
        body['ports'] = getPorts()
        body['holdtime'] = self.holdtime
        jsonbody = json.dumps(body,sort_keys=True,indent=2)
        try:
            requests.post(self.endpoint+'register', data = jsonbody, headers = self.headers,timeout=2)
        except Exception as e:
            logging.error('PiCon registration attempt failed: ' + str(e))
        else:
            logging.debug("Using registration endpoint %s, send JSON %s" % (self.endpoint+'register',jsonbody))

    def run(self):
        while True:
            self.register()
            sleep(self.interval)

def main():
    # create an agent and register
    a = PiConAgent('http://199.187.221.170:5000/api/')
    a.register()
    sys.stderr.write(PiConAgent.jsonbody)

if __name__ == "__main__":
    main()

