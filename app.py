from flask import Flask, redirect, request, session
from requests_oauthlib import OAuth2Session
import os

# Setup Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Pinterest OAuth settings (update with your real values)
CLIENT_ID = '1525609'
CLIENT_SECRET = 'd9e41297b07020596772579074e308671f88fec5'
REDIRECT_URI = 'https://pinterest-analyzer.onrender.com/callback'

AUTHORIZATION_BASE_URL = 'https://www.pinterest.com/oauth/'
TOKEN_URL = 'https://api.pinterest.com/v5/oauth/token'  # ✅ Updated to Pinterest's v5 API
SCOPE = ['boards:read', 'pins:read']

# Home route
@app.route('/')
def home():
    return """
        <h2>Welcome to the Pinterest Analyzer</h2>
        <a href='/login'>Login with Pinterest</a>
    """

# Login route – allow only GET requests to avoid HEAD error
@app.route('/login', methods=['GET'])
def login():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    authorization_url, state = pinterest.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

# Callback route
@app.route('/callback')
def callback():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, state=session.get('oauth_state'))

    try:
        token = pinterest.fetch_token(
            TOKEN_URL,
            client_id=CLIENT_ID,  # ✅ Added this to fix missing_token error
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        session['oauth_token'] = token
        return "<h3>✅ Pinterest login successful!</h3>"
    except Exception as e:
        return f"<h3>❌ Error during authentication:</h3><pre>{str(e)}</pre>"

# Privacy policy route
@app.route('/privacy')
def privacy():
    return """
    <h1>Privacy Policy</h1>
    <p>This app uses Pinterest API to analyze boards with user permission. We do not permanently store personal data.</p>
    <p>You can view the full policy <a href="https://www.termsfeed.com/live/90026cd3-68b4-415e-b50a-f7420791857c" target="_blank">here</a>.</p>
    """

# Test route
@app.route('/test')
def test():
    return "✅ Test route working!"

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)

