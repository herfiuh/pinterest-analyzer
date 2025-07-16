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
                image_url = pins[0]['media']['images'].get('original', {}).get('url') if pins else None
                section_previews.append({
                    'id': sec_id,
                    'image': image_url or "https://via.placeholder.com/150x100?text=No+Image"
                })

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
    <p>You can view the full policy <a href="https://www.termsfeed.com/live/90026cd3-68b4-415e-b50a-f7420791857c" target="_blank">here</a>.</p>
    """

@app.route('/test')
def test():
    return "✅ Test route working!"

# === Templates ===

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>p!nlyzer</title>
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #ffe6e6;
            font-family: 'Great Vibes', cursive;
            color: #4b0000;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            text-align: center;
        }
        h1 {
            font-size: 64px;
            margin-bottom: 40px;
            text-shadow: 1px 1px #fff0f5;
        }
        a.login-btn {
            font-size: 24px;
            padding: 14px 30px;
            background-color: #ffccd5;
            color: #4b0000;
            border: 2px solid #b30059;
            border-radius: 12px;
            text-decoration: none;
        }
        a.login-btn:hover {
            background-color: #f5b5c0;
        }
    </style>
</head>
<body>
    <h1>p!nlyzer</h1>
    <a class="login-btn" href="/login">Log in with Pinterest</a>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
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
            padding: 20px;
        }
        .logo {
            font-size: 48px;
            margin-bottom: 20px;
            text-shadow: 1px 1px #ccc;
        }
        .catalogue {
            background: rgba(255, 240, 240, 0.8);
            border: 2px dashed #b30059;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 40px;
            text-align: center;
        }
        .board-card {
            margin-bottom: 30px;
        }
        .card {
            border: none;
            border-radius: 12px;
            background-color: #fff0f5;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            position: relative;
        }
        .section-img {
            height: 100px;
            border-radius: 10px;
            margin: 5px;
        }
        .feature-button {
            position: absolute;
            top: 10px;
            right: 12px;
            font-size: 24px;
            cursor: pointer;
        }
        .dropdown-menu {
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">p!nlyzer</div>

        <div class="catalogue">
            <h2>P!NLYZE</h2>
            <p>Select a board or section to:</p>
            <ul style="list-style: none; padding-left: 0;">
                <li>💡 Analyze board themes & colors</li>
                <li>🧠 Build psychological profiles</li>
                <li>🧚‍♀️ Create board personas</li>
                <li>📌 Get personalized vibe insights</li>
                <li>🗣 Talk to your board</li>
                <li>🧭 Content overlap <em>(coming soon)</em></li>
            </ul>
        </div>

        <h3>Your Boards</h3>
        <div class="row">
            {% for board in boards %}
            <div class="col-md-4 board-card">
                <div class="card">
                    <div class="feature-button dropdown">
                        <span data-bs-toggle="dropdown" aria-expanded="false">⚚</span>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="#">Analyze Theme</a></li>
                            <li><a class="dropdown-item" href="#">Analyze Color</a></li>
                            <li><a class="dropdown-item" href="#">Board Vibe</a></li>
                            <li><a class="dropdown-item" href="#">Talk to My Board</a></li>
                            <li><a class="dropdown-item" href="#">Board Persona</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item disabled" href="#">Content Overlap (coming soon)</a></li>
                        </ul>
                    </div>
                    <img src="{{ board['cover_image'] }}" class="card-img-top" alt="Board Cover">
                    <div class="card-body">
                        <h5 class="card-title">{{ board['name'] }}</h5>
                        {% if board['sections'] %}
                            <div>
                                <p style="font-size: 18px;">Sections:</p>
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

