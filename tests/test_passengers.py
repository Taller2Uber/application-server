import unittest
import json
import flask
import llevame
from unittest.mock import MagicMock
from unittest import mock
from unittest.mock import Mock
from sharedServer.ss_api import SharedServer
from facebook.facebook import Facebook
import sharedServer.ss_api
from requests.models import Response

class PassengerMock(object):
    data = ""
    status_code = 500

    def __init__(self, data, status_code):
        self.content = json.dumps(data)
        self.status_code = status_code


class PassengersTestCase(unittest.TestCase):

    def login(self):
        passenger = {'ss_id': 1, 'username': 'test', 'password': 'test'}
        with llevame.app.app_context():
            llevame.mongo.db.passengers.insert(passenger)
        test_passenger = PassengerMock({'user_name': 'test', 'password': 'test'}, 200)
        the_response = Mock(spec=Response)
        the_response.content = json.dumps({'user': {'id': '1', "type": 'passenger'}})
        the_response.status_code = 200
        SharedServer.validateUser = MagicMock(return_value=the_response)
        return self.app.post('/api/v1/users/login', data=test_passenger.content, content_type='application/json')
    """Initialize empty passengers db."""
    def setUp(self):
        """Set up test variables."""
        self.app = llevame.app.test_client()
        self.app.testing = True
        llevame.sharedServer.ss_api.ss_url = 'http://localhost:8000'
        with llevame.app.app_context():
            # within this block, current_app points to app.
            llevame.mongo.db.passengers.delete_many({})

    def test_get(self):
        token = self.login()
        """Test case for obtaining passengers """
        res = self.app.get('/api/v1/passengers', headers={ 'authorization' : token.headers.get('authorization')})
        result = json.loads(res.data.decode())
        self.assertEqual(res.status_code, 200)

    def test_get_by_id(self):
        token = self.login()
        res = self.app.get('/api/v1/passengers/1', headers={ 'authorization' : token.headers.get('authorization')})
        self.assertEqual(res.status_code, 200)

    def test_create(self):
        """Test case for creating a passenger """
        test_passenger = PassengerMock({'user': { "username":"fncaldora","password":"yoursister","firstname":"Facundo","lastname":"Caldora","country":"Argentina","email":"facundo.caldoragmail.com","birthdate":"26/02/1990"}}, 201)
        the_response = Mock(spec=Response)
        the_response.content = test_passenger.content
        the_response.status_code = 201
        SharedServer.createUser = MagicMock(return_value=the_response)
        passengerToCreate = json.dumps({'user_name': 'fncaldora', 'password': 'yoursister'})
        res = self.app.post('/api/v1/passengers', data=passengerToCreate, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        passengerToCreate = json.dumps({'fb_token': 'testtoken'})
        facebook_response = Mock(spec=Response)
        facebook_response.content = json.dumps({'id': 1, 'name': 'Johnny'})
        facebook_response.status_code = 200
        Facebook.getUser = MagicMock(return_value=facebook_response.content)
        res = self.app.post('/api/v1/passengers', data=passengerToCreate, content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_passenger_update(self):
        token = self.login()
        passengerToUpdate = json.dumps({'latitude': '25'})
        res = self.app.put('/api/v1/passengers/1', data=passengerToUpdate,headers={ 'authorization' : token.headers.get('authorization')}, content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_passenger_pay(self):
        token = self.login()
        toPay = json.dumps({'amount': 50, 'paymethod': {}})
        trips_response = Mock(spec=Response)
        trips_response.content = json.dumps({'trips': [{ 'id': 1}]})
        trips_response.status_code = 200
        SharedServer.getTrips = MagicMock(return_value=trips_response)

        pay_response = Mock(spec=Response)
        pay_response.content = json.dumps({'trips': [{ 'id': 1}]})
        pay_response.status_code = 201
        SharedServer.pay = MagicMock(return_value=pay_response)

        res = self.app.post('/api/v1/users/1/pay', data=toPay,headers={ 'authorization' : token.headers.get('authorization')}, content_type='application/json')
        self.assertEqual(res.status_code, 200)