from flask import Flask, redirect, request, session
from requests_oauthlib import OAuth2Session
import os

# Set up Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # You can change this to something more permanent for production

# Pinterest OAuth settings (replace with your actual credentials)
CLIENT_ID = 'your-actual-client-id'
CLIENT_SECRET = 'your-actual-client-secret'
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
AUTHORIZATION_BASE_URL = 'https://www.pinterest.com/oauth/'
TOKEN_URL = 'https://api.pinterest.com/v1/oauth/token/'

# Home route to display a simple message
@app.route('/')
def home():
    return "Welcome to the Pinterest Analyzer! <a href='/login'>Login with Pinterest</a>"

# Route to initiate OAuth login with Pinterest
@app.route('/login')
def login():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    authorization_url, state = pinterest.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

# Route to handle Pinterest OAuth callback
@app.route('/callback')
def callback():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, state=session['oauth_state'])
    pinterest.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)
    
    # Store token in session for later use (make authenticated Pinterest API calls)
    session['oauth_token'] = pinterest.token
    return 'Pinterest login successful! You are now authenticated.'

# Test route to check if the app is working
@app.route('/test')
def test():
    return "Test route working!"

if __name__ == "__main__":
    app.run(debug=True)
