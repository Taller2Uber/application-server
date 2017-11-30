import requests
import json

with open('config.json') as data_file:
    conf = json.load(data_file)
google_token = conf["google_token"]

class GoogleMaps:

    def __init__(self):
        self.google_token = google_token

    def getRoutes(self, start_coord, end_coord):
        return requests.get('https://maps.googleapis.com/maps/api/directions/json?origin=' + start_coord + '&destination=' + end_coord + '&alternatives=true&key=' + google_token)
        