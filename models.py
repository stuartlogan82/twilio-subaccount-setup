from app import db
from twilio.rest import Client
import os
from pprint import pprint

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')

class Customer(db.Model):
    __tablename__ = 'customer'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    phone_number = db.Column(db.String())
    street_address = db.Column(db.String())
    city = db.Column(db.String())
    post_code = db.Column(db.String())
    email_address = db.Column(db.String(), unique=True)
    twilio_account_sid = db.Column(db.String())
    twilio_auth_token = db.Column(db.String())
    twilio_phone_number = db.Column(db.String())
    sendgrid_account_sid = db.Column(db.String())
    sendgrid_auth_token = db.Column(db.String())
    sendgrid_from_address = db.Column(db.String())

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
        twilio_bits = {"twilio_account_sid": cust_twilio_sid, "twilio_auth_token": cust_twilio_auth}
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
        twilio_phone_number = client.incoming_phone_numbers.create(phone_number=fetch_a_number[0].phone_number)
        print(twilio_phone_number.phone_number)
        self.add_attrs(twilio_phone_number=twilio_phone_number.phone_number)

    def send_sms(self, message):
        client = Client(self.twilio_account_sid, self.twilio_auth_token)

        client.api.account.messages.create(
            to=self.phone_number,
            from_=self.twilio_phone_number,
            body=message
        )

    def add_attrs(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f'<id: {self.id} / twilio sid: {self.twilio_account_sid}>'
