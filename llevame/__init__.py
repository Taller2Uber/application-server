import requests
from bson.json_util import dumps
from flask import Flask, request, json
from flask_restful import reqparse
from flask_restful.inputs import boolean
from flask_restplus import Resource, Api, fields
from flask_pymongo import PyMongo
import logging
import json
from werkzeug.contrib.cache import SimpleCache

# Configuro el cache
cache = SimpleCache()
# Configuracion de logs
logging.basicConfig(filename='application.log', level=logging.ERROR, format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

app = Flask(__name__)
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

def get_cache(str):
    var = cache.get(str)
    if not var:
        return "NOT_SET_YET"
    return var

########################


@api.route('/api/v1/drivers')
class DriversController(Resource):
    @api.response(200, 'Success')
    def get(self):
        args = driver_parser.parse_args()
        if args['available'] is None:
            db_drivers = dumps(mongo.db.drivers.find())
        else:
            db_drivers = dumps(mongo.db.drivers.find({'available': args['available']}))
        return json.loads(db_drivers), 200, {'Content-type': 'application/json'}

    @api.expect(driver)
    def post(self):
        drivers = mongo.db.drivers
        fb_token = request.json.get('fb_token')
        user_name = request.json.get('user_name')
        password = request.json.get('password')
        fb_id = ''
        driver = None
        if fb_token:
            fb_response = requests.get(
                'https://graph.facebook.com/me?access_token=' + fb_token + '&fields=name').content
            fb_body = json.loads(fb_response)
            if 'error' not in fb_body:
                fb_id = fb_body.get("id")
                driver = drivers.find_one({'fb_id': fb_id})
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
                'firstname': request.json.get('first_name') or 'default',
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
                    'firstname': created_driver.get('firstname'),
                    'lastname': created_driver.get('lastname'),
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

@api.route('/api/v1/drivers/<string:driver_id>')
class DriverController(Resource):
    def get(self, driver_id):
        db_driver = mongo.db.drivers.find_one({'ss_id': int(driver_id)})
        if not db_driver:
            return {'error': 'Driver not found'}, 404, {'Content-type': 'application/json'}
        return json.loads(dumps(db_driver)), 200, {'Content-type': 'application/json'}

    @api.expect(driver_update)
    def put(self, driver_id):
        db_driver = mongo.db.drivers.find_one({'ss_id': int(driver_id)})
        if not db_driver:
            return {'error': 'Driver not found'}, 404, {'Content-type': 'application/json'}
        mongo.db.drivers.update_one({'ss_id': int(driver_id)}, {'$set': request.get_json()})
        return json.loads(dumps(mongo.db.drivers.find_one({'ss_id': int(driver_id)}))), 200, {'Content-type': 'application/json'}

@api.route('/api/v1/drivers/<string:driver_id>/cars')
class CarsController(Resource):
    def get(self, driver_id):
        db_driver = mongo.db.drivers.find_one({'ss_id': int(driver_id)})
        if not db_driver:
            return {'error': 'Driver not found'}, 404, {'Content-type': 'application/json'}
        return json.loads(dumps(db_driver['cars'])), 200, {'Content-type': 'application/json'}

    @api.expect(car)
    def post(self, driver_id):
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

@api.route('/api/v1/passengers')
class PassengersController(Resource):
    @api.response(200, 'Success')
    def get(self):
        db_passengers = dumps(mongo.db.passengers.find())
        return json.loads(db_passengers), 200, {'Content-type': 'application/json'}

    @api.expect(passenger)
    def post(self):
        passengers = mongo.db.passengers
        fb_token = request.json.get('fb_token')
        user_name = request.json.get('user_name')
        password = request.json.get('password')
        fb_id = ''
        passenter = None
        if fb_token:
            fb_response = requests.get(
                'https://graph.facebook.com/me?access_token=' + fb_token + '&fields=name').content
            fb_body = json.loads(fb_response)
            if 'error' not in fb_body:
                fb_id = fb_body.get("id")
                passenger = passengers.find_one({'fb_id': fb_id})
            else:
                return fb_body, 400
        if fb_token:
            passenger = passengers.find_one({'fb_id': fb_id})
        else:
            passenger = passengers.find_one({'user_name': user_name, 'password': password})
        if not passenger:
            ss_create_passenger = requests.post(ss_url + '/api/users', json={
                'type': 'passenger',
                'username': user_name or 'default',
                'password': password or 'default',
                'fb': {'authToken': fb_id,
                       'userid': fb_id},
                'firstname': request.json.get('first_name') or 'default',
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
                    'firstname': created_passenger.get('firstname'),
                    'lastname': created_passenger.get('lastname'),
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


@api.route('/api/v1/passengers/<string:passenger_id>')
class PassengerController(Resource):

    def get(self, passenger_id):
        db_passenger = mongo.db.passengers.find_one({'ss_id': int(passenger_id)})

        if not db_passenger:
            return {'error': 'Passenger not found'}, 404, {'Content-type': 'application/json'}
        return json.loads(dumps(db_passenger)), 200, {'Content-type': 'application/json'}

    @api.expect(passenger_update)
    def put(self, passenger_id):
        db_passenger = mongo.db.passengers.find_one({'ss_id': int(passenger_id)})
        if not db_passenger:
            return {'error': 'Passenger not found'}, 404, {'Content-type': 'application/json'}
        mongo.db.passengers.update_one({'ss_id': int(passenger_id)}, {'$set': request.get_json()})
        return json.loads(dumps(mongo.db.passengers.find_one({'ss_id': int(passenger_id)}))), 200, {'Content-type': 'application/json'}


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
        ss_response = requests.post(ss_url + '/api/users/validate',
                                    json=body,
                                    headers={'token': app_token})
        if ss_response.status_code == 200 :
            user = json.loads(ss_response.content)
            response = {}
            if user.get("user"):
                id = user.get("user").get("id")
                if id:
                    if user.get("user").get("type") == "passenger":
                        response = mongo.db.passengers.find_one({'ss_id': int(id)})
                    elif user.get("user").get("type") == "driver":
                        response = mongo.db.drivers.find_one({'ss_id': int(id)})
                    response["type"] = user.get("user").get("type")
            return json.loads(dumps(response)), ss_response.status_code
        return json.loads(ss_response.content), ss_response.status_code

@api.route("/api/v1/routes")
class RoutesController(Resource):
    @api.expect(coordinates)
    def post(self):
        start_coord = request.json.get('latitude_origin') + ',' + request.json.get('longitude_origin')
        end_coord = request.json.get('latitude_destination') + ',' + request.json.get('longitude_destination')
        if start_coord and end_coord:
            google_routes = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin=' + start_coord + '&destination=' + end_coord + '&alternatives=true&key=' + google_token)
            return json.loads(google_routes.content), google_routes.status_code
        else:
            return {'error': 'Bad parameters, start and end needed'}, 400, {'Content-type': 'application/json'}


if __name__ == "__main__":
    app.run(debug=True)
