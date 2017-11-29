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


class DriversTestCase(unittest.TestCase):
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
        driver = {'ss_id': 1, 'username': 'test', 'password': 'test'}
        with llevame.app.app_context():
            llevame.mongo.db.drivers.insert(driver)
        the_response = Mock(spec=Response)
        the_response.content = {"user": {"id": "1","type": "driver"}}
        the_response.status_code = 200
        SharedServer.validateUser = MagicMock(return_value=the_response)
        token = self.app.post('/api/v1/users/login', data=json.dumps({'user_name': 'test', 'password': 'test'}))
        """Test case for obtaining drivers """
        res = self.app.get('/api/v1/drivers', headers={ 'authorization' : token.headers.get('authorization')})
        result = json.loads(res.data.decode())
        self.assertEqual(res.status_code, 200)

    def test_get_by_id(self):
        driver = {'ss_id': 1, 'username': 'test', 'password': 'test'}
        with llevame.app.app_context():
            llevame.mongo.db.drivers.insert(driver)
        test_driver = DriverMock({'user_name': 'test', 'password': 'test'}, 200)
        the_response = Mock(spec=Response)
        the_response.content = json.dumps({'user': {'id': '1', "type": 'driver'}})
        the_response.status_code = 200
        SharedServer.validateUser = MagicMock(return_value=the_response)
        token = self.app.post('/api/v1/users/login', data=test_driver.content, content_type='application/json')
        res = self.app.get('/api/v1/drivers/1', headers={ 'authorization' : token.headers.get('authorization')})
        self.assertEqual(res.status_code, 200)

    def test_creat(self):
        """Test case for creating a driver """
        test_driver = DriverMock({'user': { "username":"fncaldora","password":"yoursister","firstname":"Facundo","lastname":"Caldora","country":"Argentina","email":"facundo.caldoragmail.com","birthdate":"26/02/1990"}}, 201)
        the_response = Mock(spec=Response)
        the_response.content = test_driver.content
        the_response.status_code = 201
        SharedServer.createUser = MagicMock(return_value=the_response)
        res = self.app.post('/api/v1/drivers', data=test_driver.content, content_type='application/json')
        self.assertEqual(res.status_code, 201)