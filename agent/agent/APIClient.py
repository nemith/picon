from .utils import *

class APIClient():
    def __init__(self,endpoint='http://localhost/api/',headers={'content-type': 'application/json'}):
        self.endpoint = endpoint
        self.headers = headers
    def register(self):
        body = {}
        body['hostname'] = getHostname()
        body['sn'] = getSerial()
        body['interfaces'] = getInterfaces()
        body['ports'] = getPorts()
        jsonbody = json.dumps(body,sort_keys=True,indent=2)
        print(self.endpoint+'register')
        requests.post(self.endpoint+'register', data = jsonbody, headers = self.headers)


def main():
    # create an agent and register
    a = APIClient('http://199.187.221.170:5000/api/')
    a.register()
    sys.stderr.write(APIClient.jsonbody)
if __name__ == "__main__":
    main()

