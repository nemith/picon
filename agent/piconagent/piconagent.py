from .utils import *
from time import sleep

class PiConAgent():
    def __init__(self,endpoint='http://localhost/api/',headers={'content-type': 'application/json'},holdtime=300,delay=60):
        self.endpoint = endpoint
        self.headers = headers
        self.holdtime = holdtime
        self.delay = delay
    def register(self):
        body = {}
        body['hostname'] = getHostname()
        body['sn'] = getSerial()
        body['interfaces'] = getInterfaces()
        body['ports'] = getPorts()
        body['holdtime'] = self.holdtime
        jsonbody = json.dumps(body,sort_keys=True,indent=2)
        print(self.endpoint+'register')
        requests.post(self.endpoint+'register', data = jsonbody, headers = self.headers)
    def run(self):
        while True:
            self.register()
            sleep(self.delay)

def main():
    # create an agent and register
    a = PiConAgent('http://199.187.221.170:5000/api/')
    a.register()
    sys.stderr.write(PiConAgent.jsonbody)

if __name__ == "__main__":
    main()

