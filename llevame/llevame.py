from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/api/user/create", methods=['POST'])
def createUser():
    user = {
        'nombre': 'Agustin',
        'apellido': 'Perrotta',
        'email': 'aperrotta@gmail.com', 
        'fbAccount': 'test',
        'gmail' : 'suga92@gmail.com'
    }

    return jsonify(user), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0')
