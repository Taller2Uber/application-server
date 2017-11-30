#from pyfcm import FCMNotification


class FCM:

    def __init__(self):
        #self.push_service = FCMNotification(api_key="AAAAc3lcLr8:APA91bEjf0y6NSLjfjvPmbDT0kyadEtyu3KK7TLZ9QHG97LpIr9mhdmuE1DHlzkF_8MzPjNJSwNCilfYBkUgoBkQJUBYssqzJMeI0KYBzR0UbgHbAdJxZWEH-dCGxRodFzQtEwjtdV5-")
        return
    def sendNotification(self, passenger_token, route_id, message):
        return self.push_service.notify_single_device(registration_id=passenger_token, message_title="Llevame", message_body= {"type": message, "content": route_id})