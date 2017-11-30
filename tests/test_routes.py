import unittest
import json
import flask
import llevame
from unittest.mock import MagicMock
from unittest import mock
from unittest.mock import Mock
from sharedServer.ss_api import SharedServer
from googleMaps.google_maps import GoogleMaps
import sharedServer.ss_api
from requests.models import Response

class DriverMock(object):
    data = ""
    status_code = 500

    def __init__(self, data, status_code):
        self.content = json.dumps(data)
        self.status_code = status_code

class RoutesMock(object):
    data = ""
    status_code = 500

    def __init__(self, data, status_code):
        self.content = json.dumps(data)
        self.status_code = status_code

class RoutesTestCase(unittest.TestCase):

    def login(self):
        passenger = {'ss_id': 1, 'username': 'test', 'password': 'test', 'cars': []}
        with llevame.app.app_context():
            llevame.mongo.db.passengers.delete_many({})
            llevame.mongo.db.passengers.insert(passenger)
        test_route = RoutesMock({'user_name': 'test', 'password': 'test'}, 200)
        the_response = Mock(spec=Response)
        the_response.content = json.dumps({'user': {'id': '1', "type": 'driver'}})
        the_response.status_code = 200
        SharedServer.validateUser = MagicMock(return_value=the_response)
        return self.app.post('/api/v1/users/login', data=test_route.content, content_type='application/json')
    """Initialize empty drivers db."""
    def setUp(self):
        """Set up test variables."""
        self.app = llevame.app.test_client()
        self.app.testing = True
        llevame.sharedServer.ss_api.ss_url = 'http://localhost:8000'
        with llevame.app.app_context():
            # within this block, current_app points to app.
            llevame.mongo.db.routes.delete_many({})

    def test_get_available_routes(self):
        """Test case for obtaining routes """
        token = self.login()
        test_route = RoutesMock({'passenger_id': 1, "latitude_origin": "-34.56699", "longitude_origin": "-58.47636", "latitude_destination": "-34.616789", "longitude_destination": "-58.362139", 'cost': { "value":"250"}}, 201)
        the_response = Mock(spec=Response)
        the_response.content = test_route.content
        the_response.status_code = 200
        SharedServer.createUser = MagicMock(return_value=the_response)
        balance_response = Mock(spec=Response)
        balance_response.content = json.dumps({'user': { 'balance': [{ 'currency': 'ARS', 'value': 0}]}})
        balance_response.status_code = 200
        SharedServer.getPaymentMethod = MagicMock(return_value=balance_response)
        estimate_response = Mock(spec=Response)
        estimate_response.content = test_route.content
        estimate_response.status_code = 200
        SharedServer.estimatePrice = MagicMock(return_value=estimate_response)
        google_response = Mock(spec=Response)
        google_response.content = json.dumps({})
        google_response.status_code = 200
        GoogleMaps.getRoutes = MagicMock(return_value=google_response)
        res = self.app.post('/api/v1/routes', data=test_route.content, headers={ 'authorization' : token.headers.get('authorization')}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
