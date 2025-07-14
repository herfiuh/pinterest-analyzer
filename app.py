from flask import Flask, redirect, request, session, render_template_string
from requests_oauthlib import OAuth2Session
import os

# Setup Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Pinterest OAuth settings
CLIENT_ID = '1525609'
CLIENT_SECRET = 'd9e41297b07020596772579074e308671f88fec5'
REDIRECT_URI = 'https://pinterest-analyzer.onrender.com/callback'

AUTHORIZATION_BASE_URL = 'https://www.pinterest.com/oauth/'
TOKEN_URL = 'https://api.pinterest.com/v5/oauth/token'
SCOPE = ['boards:read', 'pins:read']

# Home route
@app.route('/')
def home():
    return """
        <h2>Welcome to the Pinterest Analyzer</h2>
        <a href='/login'>Login with Pinterest</a>
    """

# Login route – GET only
@app.route('/login', methods=['GET'])
def login():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    authorization_url, state = pinterest.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

# OAuth callback
@app.route('/callback')
def callback():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, state=session.get('oauth_state'))

    try:
        token = pinterest.fetch_token(
            TOKEN_URL,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        session['oauth_token'] = token
        return redirect('/dashboard')
    except Exception as e:
        return f"<h3>❌ Error during authentication:</h3><pre>{str(e)}</pre>"

# Dashboard route
@app.route('/dashboard')
def dashboard():
    token = session.get('oauth_token')
    if not token:
        return redirect('/login')

    pinterest = OAuth2Session(CLIENT_ID, token=token)

    try:
        # Get user account
        user_info = pinterest.get('https://api.pinterest.com/v5/user_account').json()

        # Get boards
        boards_resp = pinterest.get('https://api.pinterest.com/v5/boards')
        boards_data = boards_resp.json().get('items', [])

        boards = []
        for board in boards_data:
            boards.append({
                'id': board['id'],
                'name': board.get('name'),
                'description': board.get('description', ''),
                'cover_image': board.get('media', {}).get('image_cover_url') or "https://via.placeholder.com/300x200?text=No+Image"
            })

        return render_template_string(DASHBOARD_TEMPLATE, user_info=user_info, boards=boards)

    except Exception as e:
        return f"<h3>❌ Failed to load dashboard:</h3><pre>{str(e)}</pre>"

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

# HTML template for dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pinterest Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 20px; font-family: Arial, sans-serif; }
        .board-card { margin-bottom: 20px; }
        .pin-img { max-width: 100%; height: auto; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">📌 Welcome, {{ user_info['username'] }}!</h1>
        <h3>Your Boards</h3>
        <div class="row">
            {% for board in boards %}
            <div class="col-md-4 board-card">
                <div class="card">
                    <img src="{{ board['cover_image'] }}" class="card-img-top" alt="Board Cover">
                    <div class="card-body">
                        <h5 class="card-title">{{ board['name'] }}</h5>
                        <p class="card-text">{{ board['description'] or "No description" }}</p>
                        <a href="https://www.pinterest.com/{{ board['id'] }}" class="btn btn-primary" target="_blank">View Board</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

# Run app
if __name__ == "__main__":
    app.run(debug=True)
