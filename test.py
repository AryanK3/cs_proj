from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import mysql.connector
from twilio.rest import Client
import uuid
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your email server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = False  # Set to True if using SSL
app.config['MAIL_USERNAME'] = 'hax0037@gmail.com'
app.config['MAIL_PASSWORD'] = 'vpfuoxewyljbhodo'
mail = Mail(app)

# Twilio configuration
account_sid = 'AC3a9d689753868d8e1a34cb74d698b597'
auth_token = '120694c5c18ead86f116c6fa3df8ef31'
client = Client(account_sid, auth_token)

service = client.verify.v2.services.create(
        friendly_name='My First Verify Service'
        )

# MySQL configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="#2819Thor",
    database="serv"
)
cursor = db.cursor()

class CompanyForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    submit = SubmitField('Create Company')

def send_email_verification(email, verification_token):
    try:
        msg = Message('Verify Your Email - Company Creation',
                      sender='your_email@example.com',
                      recipients=[email])
        msg.body = f"Click the following link to verify your email: {url_for('verify_email', token=verification_token, _external=True)}"
        mail.send(msg)
        return True  # Email sent successfully
    except Exception as e:
        print(f"Error sending email verification: {e}")
        return False  # Email not sent

def send_sms_verification(phone_number, verification_token):
    try:
        message = client.messages.create(
            body=f"Your verification code: {verification_token}",
            from_='+919148297706',
            to=phone_number
        )
        return True  # SMS sent successfully
    except Exception as e:
        print(f"Error sending SMS verification: {e}")
        return False  # SMS not sent

@app.route('/', methods=['GET', 'POST'])
def index():
    form = CompanyForm()

    if form.validate_on_submit():
        company_name = form.company_name.data
        email = form.email.data
        phone_number = form.phone_number.data
        company_id = str(uuid.uuid4())
        email_verification_token = str(uuid.uuid4())
        sms_verification_token = str(uuid.uuid4())

        # Send email and SMS verifications
        email_verification_success = send_email_verification(email, email_verification_token)
        sms_verification_success = send_sms_verification(phone_number, sms_verification_token)

        if email_verification_success and sms_verification_success:
            try:
                cursor.execute("INSERT INTO companies (id, name, email, phone) VALUES (%s, %s, %s, %s)",
                               (company_id, company_name, email, phone_number))
                db.commit()

                flash('Company created successfully! Check your email and phone for verification.')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f"Error creating company: {e}")

        flash('Email or SMS verification failed. Please try again.')
        return redirect(url_for('index'))

    return render_template('index.html', form=form)

@app.route('/verify_email/<token>', methods=['GET'])
def verify_email(token):
    return "Email verified successfully"


if __name__ == '__main__':
    app.run(debug=True)
