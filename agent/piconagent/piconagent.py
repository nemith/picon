import traceback
from .utils import *
from time import sleep
import logging
import math
import asyncio, asyncssh, sys

class PiConAgent():
    def __init__(self,endpoint='http://localhost/api/',headers={'content-type': 'application/json'},holdtime=300,interval=60,tunnel=False):
        # requests is too noisy for INFO
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('requests').setLevel(logging.WARN)
        self.endpoint = endpoint
        self.headers = headers
        self.holdtime = holdtime
        self.interval = interval
        self.tunnel = tunnel
    def register(self):
        body = {}
        body['hostname'] = getHostname()
        body['sn'] = getSerial()
        try:
            body['interfaces'] = getInterfaces()
        except Exception as e:
            logging.error('Skipping this registration attempt because:  ' + str(e))
            logging.error("%d failed attempts in a row will result in the server declaring us dead (holdtime: %d, registration interval: %d)" % (math.ceil(self.holdtime/self.interval),self.holdtime,self.interval))
            return False
        body['ports'] = getPorts()
        body['holdtime'] = self.holdtime
        jsonbody = json.dumps(body,sort_keys=True,indent=2)
        try:
            requests.post(self.endpoint+'register', data = jsonbody, headers = self.headers,timeout=2)
        except Exception as e:
            logging.error('PiCon registration attempt failed: ' + str(e))
            return False
        else:
            logging.info('Successfully registered with endpoint ' + self.endpoint+'register')
            logging.debug('Sent JSON in POST body:' + "\n" +  jsonbody)
            return True

    def run(self):
        while True:
            self.register()
            if self.tunnel:
                self.openSSHChannel()
            sleep(self.interval)

    @asyncio.coroutine
    def runAsyncSSHClient(self):
        with (yield from asyncssh.connect('199.187.219.251')) as conn:
            listener = yield from conn.forward_remote_port('', 2222, 'localhost', 22)
            yield from listener.wait_closed()

        yield from conn.wait_closed()

    def openSSHChannel(self):
        try:
            asyncio.get_event_loop().run_until_complete(self.runAsyncSSHClient())
        except (OSError, asyncssh.Error) as exc:
            sys.exit('SSH connection failed: ' + str(exc))

def main():
    # create an agent and register
    a = PiConAgent('http://199.187.221.170:5000/api/')
    a.register()
    sys.stderr.write(PiConAgent.jsonbody)

if __name__ == "__main__":
    main()

