import unittest
import json
import flask
import llevame

class AuthTestCase(unittest.TestCase):
    """Test case for the authentication blueprint."""

    def setUp(self):
        """Set up test variables."""
        self.app = llevame.app.test_client()
        self.app.testing = True
        #self.app.config.update(
        #    MONGO_URI="mongodb://root:qmsroot@ds147681.mlab.com:47681/llevame_test"
        #)

    def test_registration(self):
        """Test user registration works correcty."""
        res = self.app.get('/api/v1/drivers')
        result = json.loads(res.data.decode())
        self.assertEqual(
            result, {'error': 'Log in and send token on header'})
        self.assertEqual(res.status_code, 401)
