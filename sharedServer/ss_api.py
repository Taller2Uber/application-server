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

    def validateUser(self, user):
        return requests.post(ss_url + '/api/users/validate', json=user, headers={'token': app_token})

    def createCar(self, driver_id, car):
        return requests.post(ss_url + '/api/users/' + driver_id + '/cars', json=car, headers={'token': app_token})

    def estimatePrice(self, route):
        return requests.post(ss_url + '/api/trips/estimate', json=route, headers={'token': app_token})

    def getPaymentMethod(self, passenger_id):
        return requests.get(ss_url + "/api/users/" + str(passenger_id), headers={'token': app_token})