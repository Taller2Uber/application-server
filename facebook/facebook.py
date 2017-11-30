import requests
import json

class Facebook:

    def __init__(self):
        return

    def getUser(self, fb_token):
        return requests.get('https://graph.facebook.com/me?access_token=' + fb_token + '&fields=name').content