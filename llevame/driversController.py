from flask_restful import Resource
from flask import request
import settings

class DriversController(Resource):

    def get(self,fb_token=None):
        if not fb_token:
            return {"error": "No esta el parametro fb_token"}, 400
        driver = settings.mongo.db.driver.find_one({'fb_token': fb_token})
        if driver:
            response = {"fb_token": driver.get('fb_token'), "name": driver.get('name')}
            return response, 201, {'Content-type': 'application/json'}
        else:
            return {"error":  "no se encontro conductor con dicho token"}, 500

    def post(self):
        data = request.get_json()
        if not data:
            data = {"response": "Request sin body"}
            return data, 400
        else:
            fb_token = data.get('fb_token')
            if fb_token:
                if settings.mongo.db.driver.find_one({"fb_token": fb_token}):
                    return {"error": "driver already exists."}, 500
                else:
                    settings.mongo.db.driver.insert(data)
                    response = {"fb_token": data.get('fb_token'), "name": data.get('name')}
                    return response, 201
            else:
                return {"error": "No se puede crear conductor sin fb_token"}, 400


    def put(self):
        data = request.get_json()
        if not data:
            data = {"response": "Request sin body"}
            return data, 400
        else:
            fb_token = data.get('fb_token')
            if fb_token:
                settings.mongo.db.driver.update({'fb_token': data.get('fb_token')}, {'$set': data})
                updatedDriver = settings.mongo.db.driver.find_one({"fb_token": data.get('fb_token')})
                response = {"fb_token": updatedDriver.get('fb_token'), "name": updatedDriver.get('name')}
                return response, 200
            else:
                return {"error": "No existe el campo fb_token, Que usuario actualizamos?"}, 400

    def delete(self):
        data = request.get_json()
        if not data:
            data = {"error": "Request sin body"}
            return data, 400
        else:
            fb_token = data.get('fb_token')
            if fb_token:
                settings.mongo.db.driver.remove({'fb_token': fb_token})
                return {"response": "usuario eliminado"}, 200
            else:
                return {"error": "No existe el campo fb_token, Que usuario borramos?"}
