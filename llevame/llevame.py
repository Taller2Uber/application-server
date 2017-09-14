from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/api/user/create", methods=['POST'])
def createUser():
    """Documentation example.

    .. :quickref: Description.

    **Example request**:

    .. sourcecode:: http

      POST / HTTP/1.1
      Host: http://localhost:5000/api/user/create
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        'nombre': 'Agustin',
        'apellido': 'Perrotta',
        'email': 'aperrotta@gmail.com', 
        'fbAccount': 'test',
        'gmail' : 'suga92@gmail.com'
      }

    :query q: full text search query
    :resheader Content-Type: application/json
    :status 201: user created succesfully
    :returns: :class:`myapp.objects.user`
    """
    user = {
        'nombre': 'Agustin',
        'apellido': 'Perrotta',
        'email': 'aperrotta@gmail.com', 
        'fbAccount': 'test',
        'gmail' : 'suga92@gmail.com'
    }

    return jsonify(user), 201

