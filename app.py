import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required, Email


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

from models import Customer

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
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer.query.filter_by(name=form.email_address.data).first()
        if customer is None:
            customer = Customer(name=form.name.data, phone_number=form.phone_number.data, email_address=form.email_address.data,
            street_address=form.street_address.data,
            city=form.city.data,
            post_code=form.post_code.data)
            customer.create_twilio_subaccount()
            customer.get_twilio_number()
            db.session.add(customer)
            db.session.commit()
            customer.send_sms(f"{customer.name}, your account has been created! Welcome to Twilio")
            flash(f"Customer, {customer.name} added! Their Twilio Account SID is: {customer.twilio_account_sid} and their new Twilio number is {customer.twilio_phone_number}")
            flash(f"Confirmation SMS sent to {customer.phone_number}")
        else:
            pass
        return redirect(url_for('index'))

    return render_template('customers.html', form=form)


if __name__ == '__main__':
    app.run()
