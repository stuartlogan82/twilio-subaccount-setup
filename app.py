import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required, Email
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests
import json

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)


from models import Customer, User

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# User Session management setup
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth2 Client Setup
o_client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id_=user_id).first()


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[Required()])
    phone_number = StringField('Phone', validators=[Required()])
    email_address = StringField('Email', validators=[Required(), Email()])
    street_address = StringField('Street Address', validators=[Required()])
    city = StringField('City', validators=[Required()])
    post_code = StringField('Post Code', validators=[Required()])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        if not current_user.twilio_sid:
            return render_template('twilio-connect.html')
        form = CustomerForm()
        if form.validate_on_submit():
            customer = Customer.query.filter_by(
                name=form.email_address.data).first()
            if customer is None:
                customer = Customer(name=form.name.data, phone_number=form.phone_number.data, email_address=form.email_address.data,
                                    street_address=form.street_address.data,
                                    city=form.city.data,
                                    post_code=form.post_code.data)
                customer.create_twilio_subaccount()
                customer.create_messaging_service()
                db.session.add(customer)
                db.session.commit()
                customer.send_sms(
                    f"{customer.name}, your account has been created! Welcome to Twilio")
                flash(f"Customer, {customer.name} added! Their Twilio Account SID is: {customer.twilio_account_sid} and their new Twilio messaging Service is {customer.message_service_sid }")
                flash(f"Confirmation SMS sent to {customer.phone_number}")
            return redirect(url_for('index'))
        return render_template('customers.html', form=form, pic=current_user.profile_pic, name=current_user.name)
    else:
        return render_template('index.html')


@app.route("/login")
def login():
    # Find which URL to hit for Google Login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use Library to costruct the request for Google login and provide
    # scopes to retrieve user profile
    request_uri = o_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get Authorization code that google sent
    code = request.args.get("code")

    # Find URL to hit to get tokens to ask for things on behalf of user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens
    token_url, headers, body = o_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse tokens
    o_client.parse_request_body_response(json.dumps(token_response.json()))

    # Now we have the tokens, find and hit URL from Google that gives
    # user profile info
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = o_client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Make sure email is verified by Google
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        user = User(id_=unique_id, name=users_name,
                    email=users_email, profile_pic=picture)
        db.session.add(user)
        db.session.commit()

    # Begin user session by logging in user
    login_user(user)

    # Send User back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/twilio_connect", methods=['GET', 'POST'])
def twilio_connect():
    account_sid = request.args.get('AccountSid', None)
    current_user.twilio_sid = account_sid
    print(current_user)
    db.session.commit()

    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run()
