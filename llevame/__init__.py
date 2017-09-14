import os
from flask import Flask, jsonify
import flask_restful
from flask_pymongo import PyMongo
from flask import make_response
import logging

logging.basicConfig(filename='example.log',level=logging.ERROR,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

app = Flask(__name__)

MONGO_URL = os.environ.get('MONGO_URL')
#if not MONGO_URL:
#    MONGO_URL = "mongodb://root:qmsroot@ds115124.mlab.com:15124/llevame";


logging.error('using mongo cofiguration on init: %s', MONGO_URL)
#app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)

@app.route('/')
def index():
    return '<h1> All Working </h1>'


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
    app.run()
