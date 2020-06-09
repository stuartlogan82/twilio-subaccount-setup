import os
from twilio.rest import Client
from flask_login import UserMixin
from pprint import pprint
from app import db
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')


class User(db.Model, UserMixin):
    __tablename__ = 'subaccount_user'

    id_ = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String())
    email = db.Column(db.String(), unique=True)
    profile_pic = db.Column(db.String())
    twilio_sid = db.Column(db.String(), unique=True)
    subaccounts = db.relationship('Customer', backref='parent', lazy='dynamic')

    def __init__(self, id_, name, email, profile_pic):
        self.id_ = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.twilio_sid = twilio_sid

    @staticmethod
    def get(user_id):
        user = User.query.filter_by(
            id_=str(user_id)).first()
        if not user:
            return None

        return user

    def get_id(self):
        return (self.id_)

    def __repr__(self):
        return f'<id: {self.id_} / twilio sid: {self.twilio__sid}>'


class Customer(db.Model):
    __tablename__ = 'subaccount_customer'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    phone_number = db.Column(db.String())
    street_address = db.Column(db.String())
    city = db.Column(db.String())
    post_code = db.Column(db.String())
    email_address = db.Column(db.String())
    twilio_account_sid = db.Column(db.String())
    twilio_auth_token = db.Column(db.String())
    message_service_sid = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # TODO add twilio_phone_number and make messaging service optional

    def __init__(self, name, phone_number, street_address, city, post_code, email_address):
        self.name = name
        self.phone_number = phone_number
        self.street_address = street_address
        self.city = city
        self.post_code = post_code
        self.email_address = email_address

    def create_twilio_subaccount(self):
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        account = client.api.accounts.create(friendly_name=self.email_address)
        cust_twilio_sid = account.sid
        cust_twilio_auth = account.auth_token
        twilio_bits = {"twilio_account_sid": cust_twilio_sid,
                       "twilio_auth_token": cust_twilio_auth}
        self.add_attrs(**twilio_bits)

    def query_twilio_subaccount(self):
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        accounts = client.api.accounts.list(friendly_name=self.name)
        for record in accounts:
            pprint(vars(record))

    def get_twilio_number(self):
        client = Client(self.twilio_account_sid, self.twilio_auth_token)
        fetch_a_number = client.available_phone_numbers('GB').mobile.list(sms_enabled=True,
                                                                          voice_enabled=True,
                                                                          exclude_all_address_required=True,
                                                                          limit=1)
        twilio_phone_number = client.incoming_phone_numbers.create(
            phone_number=fetch_a_number[0].phone_number)
        print(twilio_phone_number.phone_number)
        return twilio_phone_number
        # self.add_attrs(twilio_phone_number=twilio_phone_number.phone_number)

    def create_messaging_service(self):
        client = Client(self.twilio_account_sid, self.twilio_auth_token)
        service = client.messaging.services.create(
            friendly_name="Demo Messaging Service")
        service_sid = service.sid
        for i in range(3):
            new_number = self.get_twilio_number()
            print(f'{new_number.sid} = {new_number.phone_number}')

            client.messaging \
                .services(service_sid) \
                .phone_numbers \
                .create(
                    phone_number_sid=new_number.sid
                )
        self.add_attrs(message_service_sid=service_sid)

    def send_sms(self, message):
        client = Client(self.twilio_account_sid, self.twilio_auth_token)

        client.api.account.messages.create(
            to=self.phone_number,
            messaging_service_sid=self.message_service_sid,
            body=message
        )

    def add_attrs(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    # TODO set up inbound message webhooks

    def __repr__(self):
        return f'<id: {self.id} / twilio sid: {self.twilio_account_sid}>'
