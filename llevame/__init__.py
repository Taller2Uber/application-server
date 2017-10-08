from flask import Flask
from flask_restful import Api
import logging
from flask_pymongo import PyMongo
import settings

from driversController import DriversController


app = Flask(__name__)

# Configuracion de logs
logging.basicConfig(filename='example.log',level=logging.ERROR,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Configuracion URI Mongo
MONGO_URL = "mongodb://root:qmsroot@ds115124.mlab.com:15124/llevame";
logging.info('using mongo cofiguration on init: %s', MONGO_URL)
app.config['MONGO_URI'] = MONGO_URL
settings.mongo = PyMongo(app)


#definicion de rutas api
api = Api(app)
api.add_resource(DriversController, "/api/drivers", endpoint="drivers")
api.add_resource(DriversController, "/api/driver/<string:fb_token>", endpoint="driver")


if __name__ == "__main__":
    settings.app.run(debug=True)
