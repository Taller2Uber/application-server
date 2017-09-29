from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/user/create", methods=['POST'])
def createUser():
    """Creacion de usuarios.

    .. :quickref: El usuario se loguea con fb en la app mobile, y recibimos el token de fb como parametro y los datos en el body.

    **Example request**:

    .. sourcecode:: http

      POST /api/user/create HTTP/1.1
      Host: http://localhost:5000/api/user/create
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 201 CREATED
      Vary: Accept

      Content-Type: application/json
      {
        'nombre': 'Agustin',
        'apellido': 'Perrotta',
        'email': 'aperrotta@gmail.com', 
        'fbAccount': 'test',
        'gmail' : 'suga92@gmail.com'
      }

    :resheader Content-Type: application/json
    :status 201: user created succesfully
    :returns: :class:`myapp.objects.user`
    """
    user = {
        'userId': {userId},
        'name': 'Agustin',
        'surname': 'Perrotta',
        'email': 'aperrotta@gmail.com', 
        'fbAccount': 'test',
        'gmail' : 'suga92@gmail.com',
        'isDriver': true
    }

    return jsonify(user), 200

@app.route("/api/user/login", methods=['POST'])
def loginUser():
    """Logueo de usuarios. El usuario se loguea con fb en la app mobile, y recibimos el token de fb y mail para matchear con el usuario en la base de datos.
    
    **Example request**:
    
    .. sourcecode:: http
    
      POST /api/user/login HTTP/1.1
      Accept: application/json
      Content-Type: application/json
      {
        "email":"aperrotta@gmail.com",
        "token" : "{token}"
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
        'email': 'aperrotta@gmail.com', 
        'fbAccount': 'test',
        'gmail' : 'suga92@gmail.com',
        'isDriver': true
      }
    
    :resheader Content-Type: application/json
    :statuscode 200: Logueo exitoso
    :statuscode 401: Acceso denegado
    """
    user = {
        'userId': {userId},
        'name': 'Agustin',
        'surname': 'Perrotta',
        'email': 'aperrotta@gmail.com', 
        'fbAccount': 'test',
        'gmail' : 'suga92@gmail.com',
        'isDriver': true
    }

    return jsonify(user), 200

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
        "isDriver" : false
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
        'isDriver': false
      }
    
    :resheader Content-Type: application/json
    :statuscode 200: Usuario actualizado con exito
    :statuscode 500: Error actualizando usuario
    """
    user = {
        'userId': {userId},
        'name': 'Agustin',
        'surname': 'Perrotta',
        'email': 'agustinperrotta@gmail.com', 
        'fbAccount': 'test',
        'gmail' : 'suga92@gmail.com',
        'isDriver': false
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
        "routes" : [{},{},{}]
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
        'userId' :  {userId},
        "actualPosition" : {
          "lat" : -34.588412, 
          "long" : -58.420596
        }
    }

    return jsonify(user), 200
