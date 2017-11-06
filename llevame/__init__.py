from builtins import staticmethod

import requests
from bson.json_util import dumps
from flask import Flask, request, json
from flask_restful import reqparse, abort
from flask_restful.inputs import boolean
from flask_restplus import Resource, Api, fields
from flask_pymongo import PyMongo
import logging
from flask_api import status
from werkzeug.contrib.cache import SimpleCache

# Configuro el cache
from llevame.lib.itsdangerous import Serializer, SignatureExpired, BadSignature

cache = SimpleCache()
# Configuracion de logs
logging.basicConfig(filename='example.log', level=logging.ERROR, format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

app = Flask(__name__)
api = Api(app)


# Configuracion URI Mongo
MONGO_URL = "mongodb://root:qmsroot@ds115124.mlab.com:15124/llevame"

logging.error('using mongo cofiguration on init: %s', MONGO_URL)

app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)

# Configuraciones Shared Server
SS_URL = 'http://172.20.10.3:3000'
app_body = { 'id': 1 }

user_token = api.model('User token', {
    'fb_token': fields.String(required=True, description='User\s facebook token')
})

card = api.model('Card', {
    'number': fields.String(required=True),
    'expiration_date': fields.DateTime(required=True),
    'company': fields.String(required=True)
})

car = api.model('Car', {
    'model': fields.String(required=True),
    'brand': fields.String(required=True),
    'year': fields.Integer(required=True),
    'license_plate': fields.String(required=True),
    'ac': fields.Boolean(required=True)})

driver = api.model('Driver', {
    'latitude': fields.Integer(),
    'longitude': fields.Integer(),
    'cars': fields.List(fields.Nested(car),required=True),
    'fb_id': fields.String(),
    'fb_token': fields.String(required=True, description='User\s facebook token'),
    'name': fields.String(),
    'gender': fields.String(),
    'email': fields.String(),
    'available': fields.Boolean(default=True)
})

passenger = api.model('Passenger', {
    'latitude': fields.Integer(),
    'longitude': fields.Integer(),
    'card': fields.Nested(card, required=True),
    'fb_id': fields.String(),
    'fb_token': fields.String(required=True, description='User\s facebook token'),
    'name': fields.String(),
    'gender': fields.String(),
    'email': fields.String()
})

passenger_update = api.model('Passenger for update', {
    'latitude': fields.Integer(),
    'longitude': fields.Integer(),
    'card': fields.Nested(card),
    'fb_id': fields.String(required=True),
    'fb_token': fields.String()
})

driver_update = api.model('Driver for update', {
    'latitude': fields.Integer(),
    'longitude': fields.Integer(),
    'cars': fields.List(fields.Nested(car)),
    'fb_id': fields.String(required=True),
    'fb_token': fields.String(),
    'available': fields.Boolean()
})

driver_parser = reqparse.RequestParser()
# Look only in the querystring
driver_parser.add_argument('available', type=boolean, location='args')

### HELPER FUNCTIONS ##

def get_cache(str):
    var = cache.get(str)
    if not var:
        return "NOT_SET_YET"
    return var

def validate_auth():
	auth = request.authorization
	if not auth:  # no header set
		abort(401)
	user = UserModel.query.filter_by(username=auth.username).first()
	if user is None or user.password != auth.password:
		abort(401)
########################

@api.route('/api/v1/ss/init')
class SSController(Resource):

    def post(self):
        # Agarro el id del body
        as_id = request.json['id']
        if not as_id:
            return {'error': 'Server not initialized'}, 400, {'Content-type': 'application/json'}
        else:
            # Request a facebook
            body = {'id': as_id}
            ss_response = requests.post(SS_URL + '/servers/ping', data=body)
            ss_body_response = ss_response.json()
            if ss_body_response['token']:
                AS_SS_ID = as_id
                SS_TOKEN = ss_body_response['token']
                print SS_TOKEN
            return {'message': 'App-Server initialized correctly'}, 200, {'Content-type': 'application/json'}


@api.route('/api/v1/drivers')
class DriversController(Resource):
    @api.response(200, 'Success')
    def get(self):
        args = driver_parser.parse_args()
        if args:
            db_drivers = dumps(mongo.db.drivers.find({'available': args['available']}))
        else:
            db_drivers = dumps(mongo.db.drivers.find())
        return json.loads(db_drivers), 200, {'Content-type': 'application/json'}

    @api.expect(driver, validate=True)
    def post(self):
        fb_token = request.json.get('fb_token')
        ss_response = requests.post(SS_URL + '/users/validate', json={'facebookAuthToken': fb_token}, headers={'ApplicationToken': cache.get('app-token')})
        if 401 == ss_response.status_code:
            logging.error('Aplicacion desautorizada, intentando loguearse ...')
            ss_ping = requests.post(SS_URL + '/servers/ping', json=app_body, headers={'ApplicationToken': cache.get('app-token')})
            if 200 == ss_ping.status_code:
                logging.info('Aplicacion logueada correctamente')
                ss_app_data = json.loads(ss_ping.content)
                cache.set('app-token', ss_app_data['token'])
                ss_response = requests.post(SS_URL + '/users/validate', json={'facebookAuthToken': fb_token},headers={'ApplicationToken': cache.get('app-token')})
            else:
                return {'error': 'Error comunicating with Shared-Server'}, ss_ping.status_code, {'Content-type': 'application/json'}

        ss_body = json.loads(ss_response.content)
        if 'error' not in ss_body:
            drivers = mongo.db.drivers
            driver = drivers.find_one({'fb_id': ss_body['id']})
            if not driver:
                ss_create_driver = requests.post(SS_URL + '/users', json={
                    'type': 'driver',
                    'username': 'default',
                    'password': 'default',
                    'fb': { 'userId': ss_body['id'], 'authToken': fb_token},
                    'firstname': ss_body['name'],
                    'lastname': 'default',
                    'country': 'default',
                    'email': 'default',
                    'birthdate': '1992-09-15'
                }, headers={'ApplicationToken': cache.get('app-token')})
                if 201 == ss_create_driver.status_code:
                    driver_to_insert = {'fb_id':ss_body['id'], 'fb_token': fb_token,
                        'name': ss_body.get('name'),
                        'gender': ss_body.get('gender'),
                        'latitude': request.json.get('latitude'),
                        'longitude': request.json.get('longitude'),
                        'cars': request.json.get('cars'),
                        'available': True}
                    drivers.insert(driver_to_insert)
                    return json.loads(dumps(driver_to_insert)), 201, {'Content-type': 'application/json'}
                else:
                    logging.error('Error comunicating with shared-server, status: %s', ss_create_driver.status_code)
                    return {'error': 'Error comunicating with Shared-Server'}, ss_create_driver.status_code, {'Content-type': 'application/json'}
            else:
                logging.error('Driver already registered id: %s', ss_body['id'])
                return {'error': 'Driver already registered'}, 400, {'Content-type': 'application/json'}
        # Devuelvo el error de ss.
        return ss_body, 400

@api.route('/api/v1/drivers/<string:driver_id>')
class DriverController(Resource):
    def get(self, driver_id):
        db_driver = mongo.db.drivers.find_one({'fb_id': driver_id})
        if not db_driver:
            return {'error': 'Driver not found'}, 404, {'Content-type': 'application/json'}
        return json.loads(dumps(db_driver)), 200, {'Content-type': 'application/json'}

    @api.expect(driver_update)
    def put(self, driver_id):
        db_driver = mongo.db.drivers.find_one({'fb_id': driver_id})
        if not db_driver:
            return {'error': 'Driver not found'}, 404, {'Content-type': 'application/json'}
        mongo.db.drivers.update_one({'fb_id': driver_id}, {'$set': request.get_json()})
        return json.loads(dumps(mongo.db.drivers.find_one({'fb_id': driver_id}))), 200, {'Content-type': 'application/json'}


@api.route('/api/v1/passengers')
class PassengersController(Resource):
    @api.response(200, 'Success')
    def get(self):
        db_passengers = dumps(mongo.db.passengers.find())
        return json.loads(db_passengers), 200, {'Content-type': 'application/json'}

    @api.expect(passenger, validate=True)
    def post(self):
        # Me quedo con el token
        fb_token = request.json['fb_token']
        # Request a facebook
        fb_response = requests.get(
            'https://graph.facebook.com/me?access_token=' + fb_token + '&fields=name,gender').content
        fb_body = json.loads(fb_response)
        if 'error' not in fb_body:
            ss_body = {
                'username': fb_body.get('name'),
                "password": "password",
                "facebookAuthToken": request.json['fb_token']
            }
            #ss_request = requests.post(
            #    SS_URL + '/users/validate', data = ss_body)
            #ss_response = ss_request.json()
            passengers = mongo.db.passengers
            passenger = passengers.find_one({'fb_id': fb_body['id']})
            if not passenger:
                passenger_to_insert = {'fb_id': fb_body['id'], 'fb_token': fb_token,
                                             'name': fb_body.get('name'),
                                             'gender': fb_body.get('gender'),
                                    'latitude': request.json.get('latitude'),
                                    'longitude': request.json.get('longitude'),
                                    'card': request.json.get('card')}
                passengers.insert(passenger_to_insert)
                return json.loads(dumps(passenger_to_insert)), 201, {'Content-type': 'application/json'}
            else:
                return {'error': 'Passenger already registered'}, 400, {'Content-type': 'application/json'}
        # Devuelvo el error de fb.
        return fb_body, 400

@api.route('/api/v1/passengers/<string:passenger_id>')
class PassengerController(Resource):

    def get(self, passenger_id):
        db_passenger = mongo.db.passengers.find_one({'fb_id': passenger_id})
        if not db_passenger:
            return {'error': 'Passenger not found'}, 404, {'Content-type': 'application/json'}
        return json.loads(dumps(db_passenger)), 200, {'Content-type': 'application/json'}

    @api.expect(passenger_update)
    def put(self, passenger_id):
        db_passenger = mongo.db.passengers.find_one({'fb_id': passenger_id})
        if not db_passenger:
            return {'error': 'Passenger not found'}, 404, {'Content-type': 'application/json'}
        mongo.db.drivers.update_one({'fb_id': passenger_id}, {'$set': request.get_json()})
        return json.loads(dumps(mongo.db.drivers.find_one({'fb_id': passenger_id}))), 200, {'Content-type': 'application/json'}


@api.route("/api/v1/users/login")
class UserLoginController(Resource):
    @api.expect(user_token, validate=True)
    def post(self):
        # Me quedo con el token
        fb_token = request.json['fb_token']
        if not fb_token:
            return 'Token not found', 400
        # Request a facebook
        fb_response = requests.get('https://graph.facebook.com/me?access_token=' + fb_token).content
        fb_body = json.loads(fb_response)
        if 'error' not in fb_body:
            passengers = mongo.db.passengers
            passenger = passengers.find_one({'fb_id': fb_body['id']})
            if not passenger:
                drivers = mongo.db.drivers
                driver = drivers.find_one({'fb_id': fb_body['id']})
                if not driver:
                    return 'User not registered', 400
                else:
                    return json.loads(dumps(driver)), 200, {'Content-type': 'application/json'}
            else:
                return json.loads(dumps(passenger)), 200, {'Content-type': 'application/json'}
        # Devuelvo error de facebook.
        return fb_body, 400

class User:
    def __init__(self):
        pass

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': 'llevame'})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user

if __name__ == "__main__":
    app.run(debug=True)
