import requests
from bson.json_util import dumps
from functools import wraps
from flask import Flask, request, json, Response
from flask_restful import reqparse, abort
from flask_restful.inputs import boolean
from flask_restplus import Resource, Api, fields
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from pyfcm import FCMNotification
import logging
import datetime
import jwt
import json

# Configuracion de logs
logging.basicConfig(filename='application.log', level=logging.ERROR, format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'grupo7'

api = Api(app)

# Configuracion URI Mongo
MONGO_URL = "mongodb://root:qmsroot@ds115124.mlab.com:15124/llevame"

logging.error('using mongo cofiguration on init: %s', MONGO_URL)

app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)

# Configuraciones Shared Server
with open('config.json') as data_file:
    conf = json.load(data_file)
app_token = conf["as_token"]
ss_url = conf["ss_url"]
google_token =  conf["google_token"]

push_service = FCMNotification(api_key="AAAAc3lcLr8:APA91bEjf0y6NSLjfjvPmbDT0kyadEtyu3KK7TLZ9QHG97LpIr9mhdmuE1DHlzkF_8MzPjNJSwNCilfYBkUgoBkQJUBYssqzJMeI0KYBzR0UbgHbAdJxZWEH-dCGxRodFzQtEwjtdV5-")


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

def get_cache(str):
    var = cache.get(str)
    if not var:
        return "NOT_SET_YET"
    return var


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


@api.route('/api/v1/drivers')
class DriversController(Resource):
    @api.response(200, 'Success')
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
                fb_response = requests.get(
                    'https://graph.facebook.com/me?access_token=' + fb_token + '&fields=name').content
                fb_body = json.loads(fb_response)
                if 'error' not in fb_body:
                    fb_id = fb_body.get("id")
                    driver = drivers.find_one({'fb_id': fb_id})
                    first_name = fb_body.get('name')
                else:
                    return fb_body, 400
            else:
                driver = drivers.find_one({'user_name': user_name, 'password': password})
            if not driver:
                ss_create_driver = requests.post(ss_url + '/api/users', json={
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
                }, headers={'token': app_token})
                if 201 == ss_create_driver.status_code:
                    json_response = json.loads(ss_create_driver.content)
                    created_driver = json_response.get('user')
                    driver_to_insert = {
                        'ss_id': created_driver.get('id'),
                        '_ref': created_driver.get('_ref'),
                        'fb_id': fb_id,
                        'firebase_token': firebase_token,
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
            ss_create_car = requests.post(ss_url + '/api/users/' + driver_id + '/cars', json=ss_body, headers={'token': app_token})

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
                fb_response = requests.get(
                    'https://graph.facebook.com/me?access_token=' + fb_token + '&fields=name').content
                fb_body = json.loads(fb_response)
                if 'error' not in fb_body:
                    fb_id = fb_body.get("id")
                    first_name = fb_body.get('name')
                    passenger = passengers.find_one({'fb_id': fb_id})
                else:
                    return fb_body, 400
            else:
                passenger = passengers.find_one({'user_name': user_name, 'password': password})
            if not passenger:
                ss_create_passenger = requests.post(ss_url + '/api/users', json={
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
                }, headers={'token': app_token})
                if 201 == ss_create_passenger.status_code:
                    json_response = json.loads(ss_create_passenger.content)
                    created_passenger = json_response.get('user')
                    passenger_to_insert = {
                        'ss_id': created_passenger.get('id'),
                        '_ref': created_passenger.get('_ref'),
                        'fb_id': fb_id,
                        'firebase_token': firebase_token,
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
        try:
            fb_token = request.json.get('fb_token')
            username = request.json.get('user_name')
            password = request.json.get('password')
            if fb_token and not username and not password:
                body = {"facebookAuthToken": fb_token}
            elif not fb_token and username and password:
                body = {"username": username, "password": password}
            else:
                return {'error': 'Bad Request'}, 400
            ss_response = requests.post(ss_url + '/api/users/validate',
                                        json=body,
                                        headers={'token': app_token})
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
        except Exception as e:
            return {'error': 'Error inesperado ' + e.message}, 500, {'Content-type': 'application/json'}

@api.route("/api/v1/routes")
class RoutesController(Resource):
    @requires_auth
    def post(self):
            passenger_id = request.json.get('passenger_id')
            start_coord = request.json.get('latitude_origin') + ',' + request.json.get('longitude_origin')
            end_coord = request.json.get('latitude_destination') + ',' + request.json.get('longitude_destination')
            if passenger_id and start_coord and end_coord:
                google_routes = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin=' + start_coord + '&destination=' + end_coord + '&alternatives=true&key=' + google_token)
                response = json.loads(google_routes.content)
                if google_routes.status_code == 200:
                    ss_estimated_price = requests.post(ss_url + '/api/trips/estimate', json={
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
                        }, headers={'token': app_token})
                    if ss_estimated_price.status_code == 200:
                        response["estimated_price"] = json.loads(ss_estimated_price.content).get('cost').get('value')
                        return response, 200
                    elif ss_estimated_price.status_code == 402:
                        user_payment = requests.get(ss_url + "/api/users/" + str(passenger_id), headers={'token': app_token})
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
    @api.expect(coordinates)
    @requires_auth
    def post(self, route_id):
        driver_id = request.json.get('driver_id')
        if driver_id:
            driver = mongo.db.drivers.find_one({'ss_id': driver_id})
            if driver:
                route_to_request = mongo.db.routes.find_one({"_id" :  ObjectId(route_id)})
                if route_to_request:
                    mongo.db.routes.update_one({"_id" :  ObjectId(route_id)}, {'$set': {"driver_id": driver_id, "status": "WAITING_ACCEPTANCE"}})
                    #notificacion firebase a passenger
                    passenger_token = mongo.db.passengers.find_one({'ss_id': int(route_to_request.get('passenger_id'))}).get("firebase_token")
                    route_to_request = mongo.db.routes.find_one({"_id": ObjectId(route_id)})

                    message_title = "Llevame"
                    message_body = "Tu viaje ha sido elegido por un conductor."
                    result = push_service.notify_single_device(registration_id=passenger_token, message_title=message_title, message_body=message_body, data_message=json.loads(dumps(route_to_request)))

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
                        message_title = "Llevame"
                        message_body = "Tu viaje ha sido confirmado por el pasajero."
                        result = push_service.notify_single_device(registration_id=driver.get('firebase_token'), data_message=json.loads(dumps(route_to_request)))
                        return {'message': 'Ruta confirmada con exito, aguarde al chofer.'}, 200, {'Content-type': 'application/json'}
                    else:
                        mongo.db.routes.update_one({"_id": ObjectId(route_id)}, {'$set': {"driver_id": route_to_request.get('driver_id'), "status": "PENDING"}})
                        message_title = "Llevame"
                        message_body = "Tu viaje ha sido rechazado por el pasajero."
                        result = push_service.notify_single_device(registration_id=driver.get('firebase_token'))
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
                mongo.db.routes.update_one({"_id" :  ObjectId(route_id)}, {'$set': {"status": "IN_PROGRESS", "initTimeStamp": datetime.datetime.now()}})
                #notificacion firebase a passenger
                passenger_token = mongo.db.passengers.find_one({'ss_id': int(route_to_start.get('passenger_id'))}).get("firebase_token")
                route_to_request = mongo.db.routes.find_one({"_id": ObjectId(route_id)})

                message_title = "Llevame"
                message_body = "Tu viaje ha comenzado."
                result = push_service.notify_single_device(registration_id=passenger_token, message_title=message_title, message_body=message_body)

                return json.loads(dumps(route_to_request)), 200
            else:
                return {'error': 'Internal server error, no route found.'}, 500, {'Content-type': 'application/json'}


@api.route("/api/v1/routes/finish/<string:route_id>")
class FinishRoutesController(Resource):
    @requires_auth
    def post(self, route_id):
        route_to_request = mongo.db.routes.find_one({"_id" :  ObjectId(route_id)})
        if route_to_request:
            mongo.db.routes.update_one({"_id" :  ObjectId(route_id)}, {'$set': {"status": "FINISHED", "finishTimeStamp": datetime.datetime.now()}})
            #notificacion firebase a passenger
            passenger_token = mongo.db.passengers.find_one({'ss_id': int(route_to_request.get('passenger_id'))}).get("firebase_token")
            route_to_request = mongo.db.routes.find_one({"_id": ObjectId(route_id)})

            message_title = "Llevame"
            message_body = "Tu viaje ha finalizado."
            result = push_service.notify_single_device(registration_id=passenger_token, message_body=message_body, data_message=json.loads(dumps(route_to_request)))

            return json.loads(dumps(route_to_request)), 200
        else:
            return {'error': 'Bad Request, no route found.'}, 400, {'Content-type': 'application/json'}


@api.route("/api/v1/users/<string:user_id>/pay")
class UsersPayController(Resource):
    def post(self, user_id):
        passenger = mongo.db.passengers.find_one({"ss_id": int(user_id)})
        driver = mongo.db.drivers.find_one({"ss_id": int(user_id)})
        if passenger or driver:
            amount_to_pay = request.json.get('amount')
            users_trips = requests.get(ss_url + "/api/users/" + user_id + "/trips", headers={'token': app_token})
            if users_trips.status_code == 200:
                trips_list = json.loads(users_trips.content).get("trips")
                trip_id = trips_list[len(trips_list)-1].get("id")
                user_payment = requests.post(ss_url + "/api/users/" + user_id + "/transactions", headers={'token': app_token}, json=
                {
                    "trip": trip_id,
                    "timestamp": 0,
                    "cost": {
                        "value": amount_to_pay,
                        "currency": "ARS"
                    },
                    "description": "pago",
                    "data": {},
                    "userid": user_id
                })
                if user_payment.status_code == 201:
                    return {'message': 'Su pago se ha registrado con exito!'}, 200, {'Content-type': 'application/json'}
                else:
                    return {'error': 'Su pago no se pudo registrar con exito.'}, 500, {'Content-type': 'application/json'}
            else:
                return {'error': 'Bad Request, amount parameter needed'}, 400, {'Content-type': 'application/json'}
        else:
            return {'error': 'Bad Request, user_id invalid.'}, 400, {'Content-type': 'application/json'}

@api.route("/api/v1/notif")
class Notifs(Resource):
    def get(self):
        #notificacion firebase a passenger


        result = push_service.notify_single_device(registration_id="dFUsCR3KbKw:APA91bGCf9XOniAWV-MblDvnTvi_vYuLMBCquNnSCmfVWsTN3yM-lSeE_sxtBFfc92Bk2GI3PNA46eeAiFqAilh4h39BvK-fP20u7dekMSPHCHe-NmXhxVg8nuZVGA8lUjw5z9PcGFfF", message_title = "Llevame", message_body={"type":"no-chat","content": {"driver":"juan"}})

        return "notif", 200


if __name__ == "__main__":
    app.run(debug=True)
