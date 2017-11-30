import unittest
import json
import flask
import llevame
from unittest.mock import MagicMock
from unittest import mock
from unittest.mock import Mock
from sharedServer.ss_api import SharedServer
import sharedServer.ss_api
from requests.models import Response

class DriverMock(object):
    data = ""
    status_code = 500

    def __init__(self, data, status_code):
        self.content = json.dumps(data)
        self.status_code = status_code

class CarMock(object):
    data = ""
    status_code = 500

    def __init__(self, data, status_code):
        self.content = json.dumps(data)
        self.status_code = status_code

class DriversTestCase(unittest.TestCase):

    def login(self):
        driver = {'ss_id': 1, 'username': 'test', 'password': 'test', 'cars': []}
        with llevame.app.app_context():
            llevame.mongo.db.drivers.delete_many({})
            llevame.mongo.db.drivers.insert(driver)
        test_driver = DriverMock({'user_name': 'test', 'password': 'test'}, 200)
        the_response = Mock(spec=Response)
        the_response.content = json.dumps({'user': {'id': '1', "type": 'driver'}})
        the_response.status_code = 200
        SharedServer.validateUser = MagicMock(return_value=the_response)
        return self.app.post('/api/v1/users/login', data=test_driver.content, content_type='application/json')
    """Initialize empty drivers db."""
    def setUp(self):
        """Set up test variables."""
        self.app = llevame.app.test_client()
        self.app.testing = True
        llevame.sharedServer.ss_api.ss_url = 'http://localhost:8000'
        with llevame.app.app_context():
            # within this block, current_app points to app.
            llevame.mongo.db.drivers.delete_many({})

    def test_get(self):
        token = self.login()
        """Test case for obtaining drivers """
        res = self.app.get('/api/v1/drivers', headers={ 'authorization' : token.headers.get('authorization')})
        result = json.loads(res.data.decode())
        self.assertEqual(res.status_code, 200)

    def test_get_by_id(self):
        token = self.login()
        res = self.app.get('/api/v1/drivers/1', headers={ 'authorization' : token.headers.get('authorization')})
        self.assertEqual(res.status_code, 200)

    def test_create(self):
        """Test case for creating a driver """
        test_driver = DriverMock({'user': { "username":"fncaldora","password":"yoursister","firstname":"Facundo","lastname":"Caldora","country":"Argentina","email":"facundo.caldoragmail.com","birthdate":"26/02/1990"}}, 201)
        the_response = Mock(spec=Response)
        the_response.content = test_driver.content
        the_response.status_code = 201
        SharedServer.createUser = MagicMock(return_value=the_response)
        driverToCreate = json.dumps({'user_name': 'fncaldora', 'password': 'yoursister'})
        res = self.app.post('/api/v1/drivers', data=driverToCreate, content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_get_cars(self):
        """Test case for creating a car for a driver"""
        token = self.login()
        res = self.app.get('/api/v1/drivers/1/cars', headers={ 'authorization' : token.headers.get('authorization')})
        self.assertEqual(res.status_code, 200)

    def test_create_car(self):
        token = self.login()
        """Test case for creating a car """
        test_car = CarMock({'brand': 'MB','model': '4P','year': '1990','license_plate': 'AAA999','ac': True}, 201)
        the_response = Mock(spec=Response)
        the_response.content = test_car.content
        the_response.status_code = 201
        SharedServer.createCar = MagicMock(return_value=the_response)
        res = self.app.post('/api/v1/drivers/1/cars', data=test_car.content, content_type='application/json')
