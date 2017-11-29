import unittest
import json
import flask
import llevame
from unittest.mock import MagicMock
from unittest import mock
from unittest.mock import Mock
from llevame.sharedServer.ss_api import SharedServer
import llevame.sharedServer.ss_api
from requests.models import Response

class DriverMock(object):
    data = ""
    status_code = 500

    def __init__(self, data, status_code):
        self.content = json.dumps({'user': { "username":"fncaldora","password":"yoursister","firstname":"Facundo","lastname":"Caldora","country":"Argentina","email":"facundo.caldoragmail.com","birthdate":"26/02/1990"}})
        self.status_code = 201


class AuthTestCase(unittest.TestCase):
    """Test case for the authentication blueprint."""
    def setUp(self):
        """Set up test variables."""
        self.app = llevame.app.test_client()
        self.app.testing = True
        llevame.sharedServer.ss_api.ss_url = 'http://localhost:8000'
        with llevame.app.app_context():
            # within this block, current_app points to app.
            llevame.mongo.db.drivers.delete_many({})

    def test_getDrivers(self):
        res = self.app.get('/api/v1/drivers')
        result = json.loads(res.data.decode())
        self.assertEqual(
            result, {'error': 'Log in and send token on header'})   
        self.assertEqual(res.status_code, 401)

    def test_createDriver(self):
        test_driver = DriverMock("", 201)
        #the_response = Response()
        #the_response.code = "expired"
        #the_response.error_type = "expired"
        #the_response.status_code = 400
        #the_response._content = b'{ "key" : "a" }'
        the_response = Mock(spec=Response)
        the_response.content = test_driver.content
        the_response.status_code = 201
        ss = SharedServer
        ss.createUser = MagicMock(return_value=the_response)
        res = self.app.post('/api/v1/drivers', data=test_driver.content, content_type='application/json')
        self.assertEqual(res.status_code, 201)