from flask_restplus import Resource, Api, fields
from llevame import app

api = Api(app)

card = api.model('Card', {
    'card_number': fields.String(description='Card number'),
    'expiration_date': fields.DateTime,
    'model': fields.String(description='Card model')
})