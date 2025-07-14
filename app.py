from flask import Flask, redirect, request, session
from requests_oauthlib import OAuth2Session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Pinterest OAuth settings
CLIENT_ID = '1525609'
CLIENT_SECRET = 'd9e41297b07020596772579074e308671f88fec5'
REDIRECT_URI = 'https://pinterest-analyzer.onrender.com/callback'

# Pinterest OAuth URLs
AUTHORIZATION_BASE_URL = 'https://www.pinterest.com/oauth/'
TOKEN_URL = 'https://api.pinterest.com/v5/oauth/token'  # ✅ UPDATED from v1 to v5

SCOPES = ['boards:read', 'pins:read']  # Adjust as needed for your app

@app.route('/')
def home():
    return "Welcome to the Pinterest Analyzer! <a href='/login'>Login with Pinterest</a>"

@app.route('/login')
def login():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
    
    # ✅ Pinterest expects these extra params
    authorization_url, state = pinterest.authorization_url(
        AUTHORIZATION_BASE_URL,
        response_type='code',
        scope=" ".join(SCOPES)
    )
    
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, state=session.get('oauth_state'))

    try:
        token = pinterest.fetch_token(
            TOKEN_URL,
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
    except Exception as e:
        return f"OAuth failed: {str(e)}"
    
    session['oauth_token'] = token
    return '✅ Pinterest login successful! You are now authenticated.'

@app.route('/test')
def test():
    return "✅ Test route working!"

@app.route('/privacy')
def privacy():
    return """
    <h1>Privacy Policy</h1>
    <p>This app uses Pinterest API to analyze boards with user permission. We do not permanently store personal data.</p>
    <p>You can view the full policy <a href="https://www.termsfeed.com/live/90026cd3-68b4-415e-b50a-f7420791857c" target="_blank">here</a>.</p>
    """

if __name__ == "__main__":
    app.run(debug=True)

