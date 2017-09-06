import os
from flask import Flask
import flask_restful
from flask_pymongo import PyMongo
from flask import make_response

MONGO_URL = os.environ.get('MONGO_URL')
if not MONGO_URL:
    MONGO_URL = "mongodb://root:qmsroot@ds115124.mlab.com:15124/llevame";

app = Flask(__name__)

app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)

@app.route('/')
def index():
    return '<h1> All Working </h1>'

if __name__ == "__main__":
    app.run()
