import Card

new_user = api.model('New user', {
    'fb_token': fields.String(description='User\'s facebook token'),
    'latitude': fields.Integer(default=0),
    'longitude': fields.Integer(default=0),
    'card': fields.Card()
})

@api.route('/api/v1/user')
class UserController(Resource):
    "Creates a new User"
    @api.expect(new_user)
    def post(self):
        return "good", 200
