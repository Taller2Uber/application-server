import os
import requests
from bson.json_util import dumps
from functools import wraps
from flask import Flask, request, json, Response
from flask_restful import reqparse, abort
from flask_restful.inputs import boolean
from flask_restplus import Resource, Api, fields
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from sharedServer.ss_api import SharedServer
from googleMaps.google_maps import GoogleMaps
from facebook.facebook import Facebook
from fcm.fcm import FCM
import sharedServer.ss_api
import googleMaps.google_maps
import logging
import datetime
import jwt
import json
import threading
import time
from math import sin, cos, sqrt, atan2, radians


# Configuracion de logs
logging.basicConfig(filename='application.log', level=logging.ERROR, format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'grupo7'

api = Api(app)

# Configuracion URI Mongo
MONGO_URL = os.getenv('MONGO_URL')
MODE = os.getenv('MODE')

logging.error('using mongo cofiguration on init: %s', MONGO_URL)

app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)

# Configuraciones Shared Server
app_token = sharedServer.ss_api.app_token
ss_url = sharedServer.ss_api.ss_url
google_token = googleMaps.google_maps.google_token

ALLOWED_DISTANCE = 0.25

coordinates = api.model('Google coordinates', {
    'latitude_origin': fields.String(required=True, description='Start point latitude'),
    'longitude_origin': fields.String(required=True, description='Start point longitude'),
    'latitude_destination': fields.String(required=True, description='End point latitude'),
    'longitude_destination': fields.String(required=True, description='End point longitude')
})

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

def encode_auth_token(user_id):
    """
    Generates the Auth Token
    :return: string
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=3600),
            'iat': datetime.datetime.utcnow(),
            'sub': str(user_id)
        }
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return e

def decode_auth_token(auth_token):
    """
    Decodes the auth token
    :param auth_token:
    :return: integer|string
    """
    try:
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'))
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

def check_auth(ss_id):
    """This function is called to check if ss_id is valid.
    """
    try: 
        ss_id = decode_auth_token(ss_id)
        user = mongo.db.passengers.find_one({'ss_id': int(ss_id)})
        if not user:
            user = mongo.db.drivers.find_one({'ss_id': int(ss_id)})
            if not user:
                return False

        return True
    except:
        return False
    

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return {'error': 'Log in and send token on header'}, 401, {'Content-type': 'application/json'}

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('authorization')
        if not auth or not check_auth(auth):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

########################
def ping():
    while True:
        global app_token
        ping_response = requests.post(ss_url + '/api/servers/ping', headers={'token': app_token})

        if ping_response.status_code == 200:
            app_token = json.loads(ping_response.content).get('token').get('token')
        time.sleep(180)

if MODE == "PRODUCTION":
    pingThread = threading.Thread(target=ping)
    pingThread.start()

#####################################
def km():
    while True:
        kmRoute()
        time.sleep(120)


def kmRoute():
    with app.app_context():
        routes_in_progress = json.loads(dumps(mongo.db.routes.find({"status": "IN_PROGRESS"})))
        if len(routes_in_progress) > 0:
            with app.app_context():
                for route in range(0, len(routes_in_progress) -1):
                    passenger = mongo.db.passengers.find({"ss_id": route.get('passeger_id')})
                    driver = mongo.db.drivers.find({"ss_id": route.get('driver_id')})
                    distance = calculateDistance(passenger.get("latitude"), passenger.get("longitude"), driver.get("latitude"), driver.get("longitude"))
                    if (distance > ALLOWED_DISTANCE):
                        notifySeparation(route)

def calculateDistance(lat1, lon1, lat2, lon2):
    R = 6373.0
    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def notifySeparation(route):
    try:
        with app.app_context():
            driver = mongo.db.drivers.find({"ss_id": route.get('driver_id')})
            result = FCM().sendNotification(driver.get('firebase_token'),"Acerquense muchachos." ,"separationNotif")
    except:
        logging.error('Separation notification failed for driver id: %s', driver['ss_id'])

    try:
        with app.app_context():
            passenger = mongo.db.passengers.find({"ss_id": route.get('passeger_id')})
            result = FCM().sendNotification(passenger.get('firebase_token'),"Acerquense muchachos." ,"separationNotif")
    except:
        logging.error('Separation notification failed for passenger id: %s', passenger.get('ss_id'))

if MODE == "PRODUCTION":
    kmThread = threading.Thread(target=km)
    kmThread.start()


########################

@api.route('/')
class index(Resource):
    def get(self):
        return "Hello world"

@api.route('/api/v1/drivers')
class DriversController(Resource):
    @api.response(200, 'Success')
    @requires_auth
    def get(self):
        try:
            args = driver_parser.parse_args()
            if args['available'] is None:
                db_drivers = dumps(mongo.db.drivers.find())
            else:
                db_drivers = dumps(mongo.db.drivers.find({'available': args['available']}))
            return json.loads(db_drivers), 200, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

    @api.expect(driver)
    def post(self):
        try:
            drivers = mongo.db.drivers
            fb_token = request.json.get('fb_token')
            user_name = request.json.get('user_name')
            password = request.json.get('password')
            firebase_token = request.json.get('firebase_token')
            fb_id = ''
            driver = None
            first_name = request.json.get('first_name')
            if fb_token:
                fb_response = Facebook().getUser(fb_token)
                fb_body = json.loads(fb_response)
                if 'error' not in fb_body:
                    fb_id = fb_body.get("id")
                    driver = drivers.find_one({'fb_id': fb_id})
                    first_name = fb_body.get('name')
                else:
                    return fb_body, 400
            elif user_name and password:
                driver = drivers.find_one({'user_name': user_name})
            else:
                return {'error': 'Bad parameters.'}, 400, {'Content-type': 'application/json'}
            if not driver:
                jsonBody={
                    'type': 'driver',
                    'username': user_name or 'default',
                    'password': password or 'default',
                    'fb': {'authToken': fb_token,
                           'userid': fb_id},
                    'firstname': first_name or 'default',
                    'lastname': request.json.get('last_name') or 'default',
                    'country': request.json.get('country') or 'default',
                    'email': request.json.get('email') or 'default',
                    'birthdate': request.json.get('birthday') or '09-09-1970'
                }
                ss_create_driver = SharedServer().createUser(jsonBody)
                if 201 == ss_create_driver.status_code:
                    json_response = json.loads(ss_create_driver.content)
                    created_driver = json_response.get('user')
                    driver_to_insert = {
                        'ss_id': created_driver.get('id'),
                        '_ref': created_driver.get('_ref'),
                        'fb_id': fb_id,
                        'firebase_token': firebase_token,
                        'user_name': created_driver.get('username'),
                        'first_name': created_driver.get('firstname'),
                        'last_name': created_driver.get('lastname'),
                        'email': created_driver.get('email'),
                        'country': created_driver.get('country'),
                        'gender': created_driver.get('gender'),
                        'latitude': request.json.get('latitude'),
                        'longitude': request.json.get('longitude'),
                        'birthday': created_driver.get('birthdate'),
                        'cars': [],
                        'available': True}
                    drivers.insert(driver_to_insert)
                    return json.loads(dumps(driver_to_insert)), ss_create_driver.status_code, {'Content-type': 'application/json'}
                else:
                    logging.error('Error communicating with shared-server, status: %s', ss_create_driver.status_code)
                    return {'error': 'Error communicating with Shared-Server', 'body': json.loads(ss_create_driver.content)}, ss_create_driver.status_code, {'Content-type': 'application/json'}
            else:
                logging.error('Driver already registered id: %s', driver['ss_id'])
                return {'error': 'Driver already registered'}, 400, {'Content-type': 'application/json'}
        except Exception as e:
            return {'error': 'Error inesperado ' + e.message}, 500, {'Content-type': 'application/json'}

@api.route('/api/v1/drivers/<string:driver_id>')
class DriverController(Resource):
    @requires_auth
    def get(self, driver_id):
        try:
            db_driver = mongo.db.drivers.find_one({'ss_id': int(driver_id)})
            if not db_driver:
                return {'error': 'Driver not found'}, 404, {'Content-type': 'application/json'}
            return json.loads(dumps(db_driver)), 200, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

    @api.expect(driver_update)
    @requires_auth
    def put(self, driver_id):
        try:
            db_driver = mongo.db.drivers.find_one({'ss_id': int(driver_id)})
            if not db_driver:
                return {'error': 'Driver not found'}, 404, {'Content-type': 'application/json'}
            mongo.db.drivers.update_one({'ss_id': int(driver_id)}, {'$set': request.get_json()})
            return json.loads(dumps(mongo.db.drivers.find_one({'ss_id': int(driver_id)}))), 200, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

@api.route('/api/v1/drivers/<string:driver_id>/cars')
class CarsController(Resource):
    @requires_auth
    def get(self, driver_id):
        try:
            db_driver = mongo.db.drivers.find_one({'ss_id': int(driver_id)})
            if not db_driver:
                return {'error': 'Driver not found'}, 404, {'Content-type': 'application/json'}
            return json.loads(dumps(db_driver['cars'])), 200, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

    @api.expect(car)
    @requires_auth
    def post(self, driver_id):
        try:
            db_driver = mongo.db.drivers.find_one({'ss_id': int(driver_id)})
            if not db_driver:
                return {'error': 'Driver not found'}, 404, {'Content-type': 'application/json'}
            ss_body = {
                "id": db_driver.get('ss_id'),
                "_ref": db_driver.get('_ref'),
                "owner": db_driver.get('firstname'),
                "properties": [
                    {
                        "name": "brand",
                        "value": request.json.get('brand')
                    },{
                        "name": "model",
                        "value": request.json.get('model')
                    },{
                        "name": "year",
                        "value": request.json.get('year')
                    },{
                        "name": "license_plate",
                        "value": request.json.get('license_plate')
                    },{
                        "name": "ac",
                        "value": request.json.get('ac')
                    }
                ]
            }
            ss_create_car = SharedServer().createCar(driver_id, ss_body)

            if ss_create_car.status_code == 201:
                db_driver['cars'].append({'brand': request.json.get('brand'),
                                           'model': request.json.get('model'),
                                           'year': request.json.get('year'),
                                           'license_plate': request.json.get('license_plate'),
                                           'ac': request.json.get('ac')})
                mongo.db.drivers.update_one({'ss_id': int(driver_id)}, {'$set': {'cars': db_driver['cars']}})
                return json.loads(dumps(db_driver)), ss_create_car.status_code, {'Content-type': 'application/json'}
            else:
                return json.loads(ss_create_car.content), ss_create_car.status_code, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

@api.route('/api/v1/passengers')
class PassengersController(Resource):
    @api.response(200, 'Success')
    @requires_auth
    def get(self):
        try:
            db_passengers = dumps(mongo.db.passengers.find())
            return json.loads(db_passengers), 200, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

    @api.expect(passenger)
    def post(self):
        try:
            passengers = mongo.db.passengers
            fb_token = request.json.get('fb_token')
            user_name = request.json.get('user_name')
            password = request.json.get('password')
            firebase_token = request.json.get('firebase_token')
            fb_id = ''
            first_name = request.json.get('first_name')
            passenger = None
            if fb_token:
                fb_response = Facebook().getUser(fb_token)
                fb_body = json.loads(fb_response)
                if 'error' not in fb_body:
                    fb_id = fb_body.get("id")
                    first_name = fb_body.get('name')
                    passenger = passengers.find_one({'fb_id': fb_id})
                else:
                    return fb_body, 400
            elif user_name and password:
                passenger = passengers.find_one({'user_name': user_name})
            else:
                return {'error': 'Bad parameters.'}, 400, {'Content-type': 'application/json'}
            if not passenger:
                jsonObject={
                    'type': 'passenger',
                    'username': user_name or 'default',
                    'password': password or 'default',
                    'fb': {'authToken': fb_token,
                           'userid': fb_id},
                    'firstname': first_name or 'default',
                    'lastname': request.json.get('last_name') or 'default',
                    'country': request.json.get('country') or 'default',
                    'email': request.json.get('email') or 'default',
                    'birthdate': request.json.get('birthday') or '09-09-1970'
                }
                ss_create_passenger = SharedServer().createUser(jsonObject)
                if 201 == ss_create_passenger.status_code:
                    json_response = json.loads(ss_create_passenger.content)
                    created_passenger = json_response.get('user')
                    passenger_to_insert = {
                        'ss_id': created_passenger.get('id'),
                        '_ref': created_passenger.get('_ref'),
                        'fb_id': fb_id,
                        'firebase_token': firebase_token,
                        'user_name': created_passenger.get('username'),
                        'first_name': created_passenger.get('firstname'),
                        'last_name': created_passenger.get('lastname'),
                        'email': created_passenger.get('email'),
                        'country': created_passenger.get('country'),
                        'gender': created_passenger.get('gender'),
                        'latitude': request.json.get('latitude'),
                        'longitude': request.json.get('longitude'),
                        'birthday': created_passenger.get('birthdate')
                        }
                    passengers.insert(passenger_to_insert)
                    return json.loads(dumps(passenger_to_insert)), ss_create_passenger.status_code, {
                        'Content-type': 'application/json'}
                else:
                    logging.error('Error communicating with shared-server, status: %s', ss_create_passenger.status_code)
                    return {'error': 'Error communicating with Shared-Server',
                            'body': json.loads(ss_create_passenger.content)}, ss_create_passenger.status_code, {
                               'Content-type': 'application/json'}
            else:
                logging.error('Passenger already registered id: %s', passenger['ss_id'])
                return {'error': 'Passenger already registered'}, 400, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

@api.route('/api/v1/passengers/<string:passenger_id>')
class PassengerController(Resource):
    @requires_auth
    def get(self, passenger_id):
        try:
            db_passenger = mongo.db.passengers.find_one({'ss_id': int(passenger_id)})
            if not db_passenger:
                return {'error': 'Passenger not found'}, 404, {'Content-type': 'application/json'}
            return json.loads(dumps(db_passenger)), 200, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

    @api.expect(passenger_update)
    @requires_auth
    def put(self, passenger_id):
        try:
            db_passenger = mongo.db.passengers.find_one({'ss_id': int(passenger_id)})
            if not db_passenger:
                return {'error': 'Passenger not found'}, 404, {'Content-type': 'application/json'}
            mongo.db.passengers.update_one({'ss_id': int(passenger_id)}, {'$set': request.get_json()})
            return json.loads(dumps(mongo.db.passengers.find_one({'ss_id': int(passenger_id)}))), 200, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

@api.route("/api/v1/users/login")
class UserLoginController(Resource):
    @api.expect(user_token)
    def post(self):
            fb_token = request.json.get('fb_token')
            username = request.json.get('user_name')
            password = request.json.get('password')
            if fb_token and not username and not password:
                body = {"facebookAuthToken": fb_token}
            elif not fb_token and username and password:
                body = {"username": username, "password": password}
            else:
                return {'error': 'Bad Request'}, 400
            ss_response = SharedServer().validateUser(body)
            if ss_response.status_code == 200 :
                user = json.loads(ss_response.content)
                response = {}
                auth_header = {}
                if user.get("user"):
                    id = user.get("user").get("id")
                    if id:
                        if user.get("user").get("type") == "passenger":
                            response = mongo.db.passengers.find_one({'ss_id': int(id)})
                        elif user.get("user").get("type") == "driver":
                            response = mongo.db.drivers.find_one({'ss_id': int(id)})
                        response["type"] = user.get("user").get("type")
                        auth_header = {'authorization' : encode_auth_token(id)}
                return json.loads(dumps(response)), ss_response.status_code, auth_header
            return json.loads(ss_response.content), ss_response.status_code



@api.route("/api/v1/users/<string:user_id>/debt")
class DebtController(Resource):
    @requires_auth
    def get(self, user_id):
        passenger = mongo.db.passengers.find_one({"ss_id": int(user_id)})
        driver = mongo.db.drivers.find_one({"ss_id": int(user_id)})
        if passenger or driver:
            ss_user = SharedServer().getDebt(user_id)

            if ss_user.status_code == 200:
                jlist = json.loads(ss_user.content).get("user").get("balance")
                balance = 0
                if (jlist):
                    for x in range(0, len(jlist)):
                            if (jlist[x].get("currency")) == "ARS":
                                balance = jlist[x].get("value")

                methods = SharedServer().getPayMethods()
                if methods.status_code == 200:
                    return {'paymethods': json.loads(methods.content).get("paymethods"), "balance": balance}, 200, {'Content-type': 'application/json'}
                else:
                    return json.loads(methods.content), 500, {'Content-type': 'application/json'}
            else:
                return json.loads(ss_user.content), 500, {'Content-type': 'application/json'}
        else:
            return {'error': 'Bad Request, user_id invalid.'}, 400, {'Content-type': 'application/json'}


@api.route("/api/v1/routes")
class RoutesController(Resource):
    @requires_auth
    def post(self):
            passenger_id = request.json.get('passenger_id')
            start_coord = request.json.get('latitude_origin') + ',' + request.json.get('longitude_origin')
            end_coord = request.json.get('latitude_destination') + ',' + request.json.get('longitude_destination')
            if passenger_id and start_coord and end_coord:
                google_routes = GoogleMaps().getRoutes(start_coord, end_coord)
                response = json.loads(google_routes.content)
                if google_routes.status_code == 200:
                    jsonObject={
                              "passenger": passenger_id,
                              "start": {
                                "address": {
                                  "location": {
                                    "lat": request.json.get('latitude_origin'),
                                    "lon": request.json.get('longitude_origin')
                                  }
                                },
                                "timestamp": 0
                              },
                              "end": {
                                "address": {
                                  "location": {
                                    "lat": request.json.get('latitude_destination'),
                                    "lon": request.json.get('longitude_destination')
                                  }
                                }
                              },
                              "cost": {
                                "currency": "ARS"
                              }
                        }
                    ss_estimated_price = SharedServer().estimatePrice(jsonObject)
                    if ss_estimated_price.status_code == 200:
                        response["estimated_price"] = json.loads(ss_estimated_price.content).get('cost').get('value')
                        return response, 200
                    elif ss_estimated_price.status_code == 402:
                        user_payment = SharedServer().getPaymentMethod(passenger_id)
                        if user_payment.status_code == 200:
                            jlist = json.loads(user_payment.content).get("user").get("balance")
                            balance = None
                            for x in range(0, len(jlist)):
                                if (jlist[x].get("currency")) == "ARS":
                                    balance = jlist[x].get("value")

                            return {'error':'Negative balance.', 'balance': balance}, 402, {'Content-type': 'application/json'}
                        else:
                            return json.loads(user_payment.content), user_payment.status_code
                    else:
                        return json.loads(ss_estimated_price.content), ss_estimated_price.status_code
                else:
                    return response, google_routes.status_code
            else:
                return {'error': 'Bad parameters, passenger, start and end needed'}, 400, {'Content-type': 'application/json'}


    @api.response(200, 'Success')
    @requires_auth
    def get(self):
        try:
            db_routes = dumps(mongo.db.routes.find())
            return json.loads(db_routes), 200, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}


@api.route("/api/v1/routes/confirm")
class ConfirmRoutesController(Resource):
    @requires_auth
    def post(self):
        try:
            route = request.json.get('route')
            passenger_id = request.json.get('passenger_id')
            if route and passenger_id:
                route_to_insert = {"route": route, "passenger_id": passenger_id, "driver_id": None, "status": "PENDING", "initTimeStamp": "", "finishTimeStamp": ""}
                mongo.db.routes.insert(route_to_insert)
                return json.loads(dumps(route_to_insert)), 200
            else:
                return {'error': 'Bad parameters, passenger_id and route needed'}, 400, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}


@api.route("/api/v1/routes/availables")
class AvailableRoutesController(Resource):
    @api.response(200, 'Success')
    @requires_auth
    def get(self):
        try:
            db_routes = dumps(mongo.db.routes.find({'status': "PENDING"}))
            return json.loads(db_routes), 200, {'Content-type': 'application/json'}
        except:
            return {'error': 'Error inesperado'}, 500, {'Content-type': 'application/json'}

@api.route("/api/v1/routes/request/<string:route_id>")
class RequestRoutesController(Resource):
    @requires_auth
    @api.expect(coordinates)
    def post(self, route_id):
        driver_id = request.json.get('driver_id')
        if driver_id:
            driver = mongo.db.drivers.find_one({'ss_id': int(driver_id)})
            if driver:
                route_to_request = mongo.db.routes.find_one({"_id" :  ObjectId(route_id)})
                if route_to_request:
                    mongo.db.routes.update_one({"_id" :  ObjectId(route_id)}, {'$set': {"driver_id": int(driver_id), "status": "WAITING_ACCEPTANCE"}})
                    #notificacion firebase a passenger
                    passenger_token = mongo.db.passengers.find_one({'ss_id': int(route_to_request.get('passenger_id'))}).get("firebase_token")
                    route_to_request = mongo.db.routes.find_one({"_id": ObjectId(route_id)})


                    result = FCM().sendNotification(passenger_token, route_id, "driverConfirmedRoute")

                    return json.loads(dumps(route_to_request)), 200
                else:
                    return {'error': 'Internal server error, no route found.'}, 500, {'Content-type': 'application/json'}
            else:
                return {'error': 'Conductor inexistente.'}, 500, {'Content-type': 'application/json'}
        else:
            return {'error': 'Bad parameters, driver_id needed'}, 400, {'Content-type': 'application/json'}

@api.route("/api/v1/routes/answerRequest/<string:route_id>")
class AnswerRoutesRequestController(Resource):
    @requires_auth
    def post(self, route_id):
        accepted = request.json.get('accepted')
        route_to_request = mongo.db.routes.find_one({"_id": ObjectId(route_id)})
        if route_to_request:
            if accepted != None:
                driver = mongo.db.drivers.find_one({'ss_id': route_to_request.get('driver_id')})
                if driver and passenger:
                    if accepted:
                        mongo.db.routes.update_one({"_id": ObjectId(route_id)}, {'$set': {"driver_id": route_to_request.get('driver_id'), "status": "ACCEPTED"}})
                        #notificacion firebase a passenger
                        result = FCM().sendNotification(driver.get('firebase_token'), route_id, "passengerConfirmedDriver") 
                        return {'message': 'Ruta confirmada con exito, aguarde al chofer.'}, 200, {'Content-type': 'application/json'}
                    else:
                        mongo.db.routes.update_one({"_id": ObjectId(route_id)}, {'$set': {"driver_id": None, "status": "PENDING"}})
                        result = FCM().sendNotification(driver.get('firebase_token'), route_id, "passengerRejectedDriver")
                        return {'message': 'Ruta rechazada con exito, aguarde a que otro chofer elija esta ruta.'}, 200, {'Content-type': 'application/json'}
                    return {'error': 'Not route found with those passenger and driver id.'}, 400, {'Content-type': 'application/json'}
                else:
                    return {'error': 'Internal server error, no route found.'}, 500, {'Content-type': 'application/json'}
        else:
            return {'error': 'Bad parameters, route not found.'}, 400, {'Content-type': 'application/json'}


@api.route("/api/v1/routes/start/<string:route_id>")
class StartRoutesController(Resource):
    @requires_auth
    def post(self, route_id):
            route_to_start = mongo.db.routes.find_one({"_id" :  ObjectId(route_id)})
            if route_to_start:
                passenger = mongo.db.passengers.find_one({'ss_id': int(route_to_start.get('passenger_id'))})
                driver = mongo.db.drivers.find_one({'ss_id': int(route_to_start.get('driver_id'))})
                distance = calculateDistance(passenger.get("latitude"), passenger.get("longitude"), driver.get("latitude"), driver.get("longitude") )
                if distance > ALLOWED_DISTANCE:
                    return {'error': 'No se puede comenzar ruta, el pasajero y el conductor deben estar cerca.'}, 500, {
                        'Content-type': 'application/json'}
                mongo.db.drivers.update_one({'ss_id': int(route_to_start.get('driver_id'))}, {'$set': {"available": False}})
                #Actualizo la ruta una vez pasado el check de distancia
                mongo.db.routes.update_one({"_id" :  ObjectId(route_id)}, {'$set': {"status": "IN_PROGRESS", "initTimeStamp": datetime.datetime.now()}})
                #notificacion firebase a passenger
                passenger_token = passenger.get("firebase_token")
                route_to_request = mongo.db.routes.find_one({"_id": ObjectId(route_id)})

                result = FCM().sendNotification(passenger_token, route_id, "driverStartedRoute")
                
                return json.loads(dumps(route_to_request)), 200
            else:
                return {'error': 'Internal server error, no route found.'}, 500, {'Content-type': 'application/json'}


@api.route("/api/v1/routes/<string:route_id>")
class SpecificRoutesController(Resource):
    @requires_auth
    def get(self, route_id):
        route = mongo.db.routes.find_one({"_id" :  ObjectId(route_id)})
        if route:
            return json.loads(dumps(route)), 200
        else:
            return {'error': 'Bad request, no route found.'}, 400, {'Content-type': 'application/json'}


@api.route("/api/v1/routes/finish/<string:route_id>")
class FinishRoutesController(Resource):
    @requires_auth
    def post(self, route_id):
        route_to_finish = mongo.db.routes.find_one({"_id" :  ObjectId(route_id)})
        if route_to_finish:
            jsonObject= {
                        "trip": {
                            "driver": route_to_finish.get("driver_id"),
                            "passenger": route_to_finish.get("passenger_id"),
                            "start": {
                                "address": {
                                    "location": {
                                        "lat": route_to_finish.get("route").get("legs")[0].get("start_location").get("lat"),
                                        "lon": route_to_finish.get("route").get("legs")[0].get("start_location").get("lng")
                                    }
                                },
                                "timestamp": 0
                            },
                            "end": {
                                "address": {
                                    "location": {
                                        "lat": route_to_finish.get("route").get("legs")[0].get(
                                            "end_location").get("lat"),
                                        "lon": route_to_finish.get("route").get("legs")[0].get(
                                            "end_location").get("lng")
                                    }
                                },
                                "timestamp": 0
                            }
                            ,
                            "totalTime": 0,
                            "waitTime": 0,
                            "totalTime": 0,
                            "distance": route_to_finish.get("route").get("legs")[0].get("distance").get("value"),
                            "route": [
                                {
                                    "location": {
                                        "lat": 0,
                                        "lon": 0
                                    },
                                    "timestamp": 0
                                }
                            ],
                            "cost": {
                                "currency": "ARS"
                            }
                        },
                        "paymethod": {}
                    }
            ss_trip = SharedServer().createTrip(jsonObject)
            if ss_trip.status_code == 201:
                mongo.db.routes.update_one({"_id":  ObjectId(route_id)}, {'$set': {"status": "FINISHED", "finishTimeStamp": datetime.datetime.now()}})
                mongo.db.drivers.update_one({'ss_id': int(route_to_finish.get('driver_id'))}, {'$set': {"available": True}})
                #notificacion firebase a passenger
                passenger_token = mongo.db.passengers.find_one({'ss_id': int(route_to_finish.get('passenger_id'))}).get("firebase_token")
                result = FCM().sendNotification(passenger_token, route_id, "driverFinishedRoute")
                return {'message': 'Viaje finalizado con exito.'}, 200
            else:
                return {'error': 'No se pudo terminar el viaje.'}, 500, {'Content-type': 'application/json'}
        else:
            return {'error': 'Bad Request, no route found.'}, 400, {'Content-type': 'application/json'}


@api.route("/api/v1/users/<string:user_id>/pay")
class UsersPayController(Resource):
    @requires_auth
    def post(self, user_id):
        passenger = mongo.db.passengers.find_one({"ss_id": int(user_id)})
        driver = mongo.db.drivers.find_one({"ss_id": int(user_id)})
        if passenger or driver:
            amount_to_pay = request.json.get('amount')
            users_trips = SharedServer().getTrips(user_id)
            if users_trips.status_code == 200:
                trips_list = json.loads(users_trips.content).get("trips")
                trip_id = trips_list[len(trips_list)-1].get("id")
                jsonObject={
                    "trip": trip_id,
                    "timestamp": 0,
                    "cost": {
                        "value": amount_to_pay,
                        "currency": "ARS"
                    },
                    "description": "pago",
                    "data": {},
                    "userid": user_id
                }
                user_payment = SharedServer().pay(jsonObject, user_id)
                if user_payment.status_code == 201:
                    return {'message': 'Su pago se ha registrado con exito!'}, 200, {'Content-type': 'application/json'}
                else:
                    return {'error': 'Su pago no se pudo registrar con exito.'}, 500, {'Content-type': 'application/json'}
            else:
                return {'error': 'Bad Request, amount parameter needed.'}, 400, {'Content-type': 'application/json'}
        else:
            return {'error': 'Bad Request, user_id invalid.'}, 400, {'Content-type': 'application/json'}


if __name__ == "__main__":
    app.run('192.168.122.1', debug=True)
