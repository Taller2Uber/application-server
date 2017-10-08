import os
import requests
from bson.json_util import dumps
from flask import Flask, jsonify, request, json
from bson import ObjectId
from flask_restplus import Resource, Api, fields
from flask_pymongo import PyMongo
import logging

# Configuracion de logs
logging.basicConfig(filename='example.log', level=logging.ERROR, format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

app = Flask(__name__)
api = Api(app)

# Configuracion URI Mongo
MONGO_URL = "mongodb://root:qmsroot@ds115124.mlab.com:15124/llevame";

logging.error('using mongo cofiguration on init: %s', MONGO_URL)

app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


user_token = api.model('User token', {
    'fb_token': fields.String(required=True, description='User\s facebook token')
})

card = api.model('Card', {
    'number': fields.String(required=True),
    'expiration_date': fields.DateTime(required=True),
    'company': fields.String(required=True)
})

user = api.model('User', {
    'fb_token': fields.String(required=True, description='User\s facebook token'),
    'latitude': fields.Integer(required=True, default=0),
    'longitude': fields.Integer(required=True, default=0),
    'card': fields.Nested(card)
})


@api.route('/api/v1/users')
class UserController(Resource):
    @api.response(200, 'Success')
    def get(self):
        db_users = dumps(mongo.db.users.find())
        return json.loads(db_users), 200, {'Content-type': 'application/json'}

    @api.expect(user, validate=True)
    def post(self):
        # Me quedo con el token
        fb_token = request.json['fb_token']
        if not fb_token:
            return 'Token not found', 400
        # Request a facebook
        #fb_response = requests.get(
         #   'https://graph.facebook.com/me?access_token=' + fb_token + '&fields=name,gender,email').content
        #fb_body = json.loads(fb_response)
        fb_body = {'id': 15}
        if 'error' not in fb_body:
            users = mongo.db.users
            user = users.find_one({'user_id': fb_body['id']})
            if not user:
                users.insert(request.json)
                return json.loads(dumps(request.json)), 201, {'Content-type': 'application/json'}
            else:
                return 'User already registered', 400
        # Devuelvo el error de fb.
        return fb_body, 400


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
            users = mongo.db.users
            user = users.find_one({'user_id': fb_body['id']})
            if not user:
                drivers = mongo.db.drivers
                driver = drivers.find_one({'user_id': fb_body['id']})
                if not driver:
                    return 'User not registered', 400
                else:
                    return JSONEncoder().encode(driver), 200, {'Content-type': 'application/json'}
            else:
                return JSONEncoder().encode(user), 200, {'Content-type': 'application/json'}
        # Devuelvo user.
        return fb_response, 400


@app.route("/api/user/update", methods=['PUT'])
def updateUser():
    """Actualizacion de usuarios. El usuario se loguea con fb en la app mobile, y recibimos el token de fb, mail y campos a actualizar

    **Example request**:

    .. sourcecode:: http

      PUT /api/user/update HTTP/1.1
      Accept: application/json
      Content-Type: application/json
      {
        "email":"agustinperrotta@gmail.com",
        "token" : "{token}",
        "isDriver" : False
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept

      Content-Type: application/json
      {
        'userId': {userId},
        'name': 'Agustin',
        'surname': 'Perrotta',
        'email': 'agustinperrotta@gmail.com',
        'fbAccount': 'test',
        'gmail' : 'suga92@gmail.com',
        'isDriver': False
      }

    :resheader Content-Type: application/json
    :statuscode 200: Usuario actualizado con exito
    :statuscode 500: Error actualizando usuario
    """
    user = {
        'userId': 'userId',
        'name': 'Agustin',
        'surname': 'Perrotta',
        'email': 'agustinperrotta@gmail.com',
        'fbAccount': 'test',
        'gmail': 'suga92@gmail.com',
        'isDriver': False
    }

    return jsonify(user), 200


@app.route("/api/route/options", methods=['POST'])
def calculateRoutesOptions():
    """Obtencion de posibles caminos para llegar de punto A a punto B del mapa.

    **Example request**:

    .. sourcecode:: http

      POST /api/routes/options HTTP/1.1
      Accept: application/json
      Content-Type: application/json
      {
        "origin" : {
          "lat" : -34.588412,
          "long" : -58.420596
        },
        "destination" : {
          "lat" : -34.573036,
          "long" : -58.488967
        }
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept

      Content-Type: application/json
      {
        "routes" : [{},{},{}]
      }

    :resheader Content-Type: application/json
    :statuscode 200: Rutas calculadas correctamente
    :statuscode 500: Error calculando rutas
    """
    options = {
        "routes": [{}, {}, {}]
    }

    return jsonify(options), 200


@app.route("/api/route/user/confirm", methods=['POST'])
def confirmUserRoute():
    """Confirmacion de camino elegido para llegar de punto A a punto B del mapa.

    **Example request**:

    .. sourcecode:: http

      POST /api/route/confirm HTTP/1.1
      Accept: application/json
      Content-Type: application/json
      {
        'userId' : {userId},
        'route' : {}
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept

    :resheader Content-Type: application/json
    :statuscode 200: Ruta confirmada correctamente
    :statuscode 500: Error confirmando ruta
    """
    return "", 200


@app.route("/api/drivers/available", methods=['POST'])
def indexAvailableDrivers():
    """Choferes disponibles cerca mio

    **Example request**:

    .. sourcecode:: http

      POST /api/drivers/available HTTP/1.1
      Accept: application/json
      Content-Type: application/json
      {
        "myPosition" : {
          "lat" : -34.588412,
          "long" : -58.420596
        }
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept

      Content-Type: application/json
      {
        "drivers" : [{
          'nombre': 'Agustin',
          'apellido': 'Perrotta',
          'email': 'aperrotta@gmail.com',
          'position' : {
                        "lat" : -34.588412,
                        "long" : -58.420596
                      }},
                      {
          'nombre': 'Facundo',
          'apellido': 'Caldora',
          'email': 'fncaldora@gmail.com',
          'position' : {
                        "lat" : -33.365984,
                        "long" : -58.405789
                      }}]
      }

    :resheader Content-Type: application/json
    :statuscode 200: Choferes obtenidos correctamente
    :statuscode 500: Error obteniendo choferes
    """
    drivers = {
        "drivers": [{
            'nombre': 'Agustin',
            'apellido': 'Perrotta',
            'email': 'aperrotta@gmail.com',
            'position': {
                "lat": -34.588412,
                "long": -58.420596
            }},
            {
                'nombre': 'Facundo',
                'apellido': 'Caldora',
                'email': 'fncaldora@gmail.com',
                'position': {
                    "lat": -33.365984,
                    "long": -58.405789
                }}]
    }

    return jsonify(drivers), 200


@app.route("/api/routes/available", methods=['POST'])
def indexAvailableConfirmedRoutes():
    """Choferes cerca mio

    **Example request**:

    .. sourcecode:: http

      POST /api/route/available HTTP/1.1
      Accept: application/json
      Content-Type: application/json
      {
        "myPosition" : {
          "lat" : -34.588412,
          "long" : -58.420596
        }
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept

      Content-Type: application/json
      {
        "confirmedRoutes" : [{
            'name': 'Agustin',
            'surname': 'Perrotta',
            'route' : {}
          },
          {
            'name': 'Facundo',
            'surname': 'Caldora',
            'route' : {}
          }]
      }

    :resheader Content-Type: application/json
    :statuscode 200: Recorridos confirmados obtenidos correctamente
    :statuscode 500: Error obteniendo recorridos confirmados
    """
    confirmedRoutes = {
        "confirmedRoutes": [{
            'name': 'Agustin',
            'surname': 'Perrotta',
            'route': {}
        },
            {
                'name': 'Facundo',
                'surname': 'Caldora',
                'route': {}
            }]
    }

    return jsonify(confirmedRoutes), 200


@app.route("/api/route/driver/confirm", methods=['POST'])
def confirmDriverRoute():
    """Chofer confirma el viaje

    **Example request**:

    .. sourcecode:: http

      POST /api/route/confirm HTTP/1.1
      Accept: application/json
      Content-Type: application/json
      {
        'routeId' : {routeId},
        'driverId' : {driverId}
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept

    :resheader Content-Type: application/json
    :statuscode 200: Recorrido confirmado correctamente
    :statuscode 500: Error confirmando recorrido
    """
    return "", 200


@app.route("/api/route/start", methods=['POST'])
def startRoute():
    """Chofer comienza el viaje

    **Example request**:

    .. sourcecode:: http

      POST /api/route/start HTTP/1.1
      Accept: application/json
      Content-Type: application/json
      {
        'userId' : {userId}
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept

    :resheader Content-Type: application/json
    :statuscode 200: Recorrido comenzando correctamente
    :statuscode 500: Error al comenzar recorrido
    """
    return "", 200


@app.route("/api/user/position", methods=['PUT'])
def updateUserPosition():
    """Actualizo posicion actual de usuario

    **Example request**:

    .. sourcecode:: http

      PUT /api/user/position HTTP/1.1
      Accept: application/json
      Content-Type: application/json
      {
        'userId' :  {userId},
        "actualPosition" : {
          "lat" : -34.588412,
          "long" : -58.420596
        }
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept

    .. sourcecode:: json

      Content-Type: application/json
      {
        'userId' :  {userId}
        "actualPosition" : {
          "lat" : -34.588412,
          "long" : -58.420596
        }
      }

    :resheader Content-Type: application/json
    :statuscode 200: Ubicacion actualizada correctamente
    :statuscode 500: Error actualizando ubicacion
    """
    user = {
        'userId': 1,
        "actualPosition": {
            "lat": -34.588412,
            "long": -58.420596
        }
    }

    return jsonify(user), 200


if __name__ == "__main__":
    app.run(debug=True)
