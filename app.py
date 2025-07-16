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
    return render_template_string(HOME_TEMPLATE)

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
            board_id = board['id']
            section_resp = pinterest.get(f'https://api.pinterest.com/v5/boards/{board_id}/sections')
            sections = section_resp.json().get('items', [])

            section_previews = []
            for section in sections:
                sec_id = section.get('id')
                pin_resp = pinterest.get(f'https://api.pinterest.com/v5/boards/{board_id}/sections/{sec_id}/pins')
                pins = pin_resp.json().get('items', [])
                image_url = pins[0]['media']['images'].get('original', {}).get('url') if pins else "https://via.placeholder.com/100x100?text=No+Image"
                section_previews.append({'id': sec_id, 'image': image_url})

            boards.append({
                'id': board_id,
                'name': board.get('name'),
                'description': board.get('description', ''),
                'cover_image': board.get('media', {}).get('image_cover_url') or "https://via.placeholder.com/300x200?text=No+Image",
                'sections': section_previews
            })

        return render_template_string(DASHBOARD_TEMPLATE, user_info=user_info, boards=boards)
    except Exception as e:
        return f"<h3>❌ Failed to load dashboard:</h3><pre>{str(e)}</pre>"

@app.route('/privacy')
def privacy():
    return """
    <h1>Privacy Policy</h1>
    <p>This app uses Pinterest API to analyze boards with user permission. We do not permanently store personal data.</p>
    """

HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>p!nlyzer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #ffe6e6;
            font-family: 'Great Vibes', cursive;
            color: #4b0000;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        h1 {
            font-size: 64px;
            margin-bottom: 40px;
            text-shadow: 1px 1px #ccc;
        }
        a.btn {
            font-size: 24px;
            padding: 15px 30px;
        }
    </style>
</head>
<body>
    <h1>p!nlyzer</h1>
    <a href="/login" class="btn btn-dark">Login with Pinterest</a>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>p!nlyzer Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #ffe6e6;
            font-family: 'Great Vibes', cursive;
            color: #4b0000;
            padding: 30px;
        }
        .logo {
            font-size: 48px;
            text-shadow: 1px 1px #ccc;
            margin-bottom: 30px;
        }
        .catalogue {
            background: rgba(255, 240, 240, 0.85);
            border: 2px dashed #b30059;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 50px;
            text-align: center;
        }
        .board-card .card {
            background-color: #fff0f5;
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            position: relative;
        }
        .feature-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: white;
            border-radius: 50%;
            padding: 6px 12px;
            font-size: 20px;
            cursor: pointer;
            border: 1px solid #ccc;
        }
        .dropdown-menu {
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
        .section-img {
            width: 80px;
            height: 80px;
            border-radius: 10px;
            object-fit: cover;
            margin: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">p!nlyzer</div>

        <div class="catalogue">
            <h2>p⚚nlyze</h2>
            <p>Select a board or section to:</p>
            <ul style="list-style: none; padding-left: 0;">
                <li>🎨 Analyze board themes & colors</li>
                <li>🧠 Build psychological profiles</li>
                <li>🧚 Create board personas</li>
                <li>🗣️ Talk to your board</li>
                <li>🧭 Vibe/Energy Map</li>
                <li>🔍 Pin similarity matrix</li>
                <li>🧩 Content overlap map (coming soon)</li>
            </ul>
        </div>

        <div class="row">
            {% for board in boards %}
            <div class="col-md-4 mb-4 board-card">
                <div class="card p-2">
                    <div class="dropdown">
                        <span class="feature-btn dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">⚚</span>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="#">Analyze Theme</a></li>
                            <li><a class="dropdown-item" href="#">Build Persona</a></li>
                            <li><a class="dropdown-item" href="#">Talk to Board</a></li>
                        </ul>
                    </div>
                    <img src="{{ board['cover_image'] }}" class="card-img-top" alt="Board Cover">
                    <div class="card-body">
                        <h5 class="card-title">{{ board['name'] }}</h5>
                        {% if board['sections'] %}
                            <div class="d-flex flex-wrap">
                                {% for section in board['sections'] %}
                                    <img src="{{ section['image'] }}" class="section-img" alt="Section Image">
                                {% endfor %}
                            </div>
                        {% elif board['description'] %}
                            <p class="card-text">{{ board['description'] }}</p>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
