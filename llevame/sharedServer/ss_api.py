import requests
import json

with open('ssconfig.json') as data_file:
    conf = json.load(data_file)
app_token = conf["as_token"]
ss_url = conf["ss_url"]

class SharedServer:

    def __init__(self):
        self.ss_url = ss_url
        
    def createUser(self, user):
        return requests.post(ss_url + '/api/users', json=user, headers={'token': app_token})