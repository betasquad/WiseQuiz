import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_oauthlib.client import OAuth

# Initialize the Flask app
app = Flask(__name__)

# Set up PostgreSQL connection URL (Replace this with your Render PostgreSQL URL)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://owsquiz_user:1wdIySyimd34KFyMA7jEfBp5BuLmRxqp@dpg-cuvdd8l6l47c738qqufg-a.singapore-postgres.render.com/owsquiz"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the SQLAlchemy instance
db = SQLAlchemy(app)

# Initialize OAuth
oauth = OAuth(app)

# Google OAuth Configuration
google = oauth.remote_app(
    'google',
    consumer_key=os.getenv('GOOGLE_CLIENT_ID'),  # Add your client ID here
    consumer_secret=os.getenv('GOOGLE_CLIENT_SECRET'),  # Add your client secret here
    request_token_params={
        'scope': 'email',
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    corrects = db.Column(db.Integer, default=0)
    attempts = db.Column(db.Integer, default=0)

# Home route
@app.route('/')
def home():
    return "Welcome to WiseQuiz!"

# Route for user login via Google
@app.route('/login')
def login():
    return google.authorize(callback=url_for('authorized', _external=True))

# Callback route after successful Google login
@app.route('/callback')
def authorized():
    response = google.authorized_response()
    if response is None or response.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(request.args['error_reason'], request.args['error_description'])

    session['google_token'] = (response['access_token'], '')
    user_info = google.get('userinfo')
    user_email = user_info.data['email']

    # Check if the user already exists in the database
    user = User.query.filter_by(email=user_email).first()
    if not user:
        # Add the new user to the database
        user = User(email=user_email)
        db.session.add(user)
        db.session.commit()

    session['user_email'] = user_email  # Store email in session
    return redirect(url_for('home'))

# Helper function to get the Google token
@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates the database tables if they don't exist
    app.run(debug=True)
