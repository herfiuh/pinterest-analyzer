from flask import Flask, redirect, request, session, render_template_string
from requests_oauthlib import OAuth2Session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = '1525609'
CLIENT_SECRET = 'd9e41297b07020596772579074e308671f88fec5'
REDIRECT_URI = 'https://pinterest-analyzer.onrender.com/callback'

AUTHORIZATION_BASE_URL = 'https://www.pinterest.com/oauth/'
TOKEN_URL = 'https://api.pinterest.com/v5/oauth/token'
SCOPE = ['boards:read', 'pins:read']

@app.route('/')
def home():
    return """
        <h2>Welcome to the Pinterest Analyzer</h2>
        <a href='/login'>Login with Pinterest</a>
    """

@app.route('/login', methods=['GET'])
def login():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    authorization_url, state = pinterest.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

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

@app.route('/dashboard')
def dashboard():
    token = session.get('oauth_token')
    if not token:
        return redirect('/login')

    pinterest = OAuth2Session(CLIENT_ID, token=token)

    try:
        user_info = pinterest.get('https://api.pinterest.com/v5/user_account').json()
        boards_resp = pinterest.get('https://api.pinterest.com/v5/boards')
        boards_data = boards_resp.json().get('items', [])

        boards = []
        for board in boards_data:
            board_entry = {
                'id': board['id'],
                'name': board.get('name'),
                'description': board.get('description', ''),
                'cover_image': board.get('media', {}).get('image_cover_url') or "https://via.placeholder.com/300x200?text=No+Image",
                'url': board.get('url'),
                'sections': []
            }

            # Optional: fetch sections
            sections_url = f"https://api.pinterest.com/v5/boards/{board['id']}/sections"
            sections_resp = pinterest.get(sections_url)
            if sections_resp.status_code == 200:
                sections = sections_resp.json().get('items', [])
                board_entry['sections'] = [s.get('title') for s in sections]

            boards.append(board_entry)

        return render_template_string(DASHBOARD_TEMPLATE, user_info=user_info, boards=boards)

    except Exception as e:
        return f"<h3>❌ Failed to load dashboard:</h3><pre>{str(e)}</pre>"

@app.route('/privacy')
def privacy():
    return """
    <h1>Privacy Policy</h1>
    <p>This app uses Pinterest API to analyze boards with user permission. We do not permanently store personal data.</p>
    <p>You can view the full policy <a href="https://www.termsfeed.com/live/90026cd3-68b4-415e-b50a-f7420791857c" target="_blank">here</a>.</p>
    """

@app.route('/test')
def test():
    return "✅ Test route working!"

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>P!nlyzer Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #ffe6e6;
            font-family: 'Brush Script MT', cursive;
            color: #4b0000;
        }
        .brand {
            font-size: 2.2rem;
            color: #800020;
        }
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 2rem;
        }
        .keypad-btn {
            font-size: 1.2rem;
            background-color: #800020;
            color: #fff;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 6px;
            font-family: 'Brush Script MT', cursive;
        }
        .card {
            background-color: #fff0f5;
            border: 1px solid #f0cdd8;
        }
        .card-title {
            font-weight: bold;
            color: #800020;
        }
        .catalogue {
            text-align: center;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="brand">P!nlyzer</div>
        <div class="catalogue">
            <button class="keypad-btn" onclick="alert('✨ Catalogue Coming Soon: Vibe, Themes, Energy, Psych Profile, Chat Persona ✨')">
                P!NLYZE
            </button>
        </div>
    </div>

    <div class="container">
        <h2 class="mb-4 text-center">Welcome, {{ user_info['username'] }}</h2>
        <div class="row">
            {% for board in boards %}
            <div class="col-md-4 board-card">
                <div class="card mb-4 shadow-sm">
                    <img src="{{ board['cover_image'] }}" class="card-img-top" alt="Board Cover">
                    <div class="card-body">
                        <h5 class="card-title">{{ board['name'] }}</h5>
                        {% if board.sections %}
                            <p class="card-text">
                                Sections ({{ board.sections | length }}):<br>
                                {{ board.sections | join(', ') }}
                            </p>
                        {% elif board.description %}
                            <p class="card-text">{{ board.description }}</p>
                        {% endif %}
                        {% if board.url %}
                            <a href="https://www.pinterest.com{{ board.url }}" class="btn btn-sm btn-outline-danger" target="_blank">View Board</a>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)

