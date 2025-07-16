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

# Safely pick the best image
def pick_best_image(media_dict):
    for size in ('original', 'large', 'medium', 'small'):
        if media_dict.get(size, {}).get('url'):
            return media_dict[size]['url']
    for item in media_dict.values():
        if isinstance(item, dict) and item.get('url'):
            return item['url']
    return "https://via.placeholder.com/150x100?text=No+Image"

@app.route('/')
def home():
    return render_template_string(LANDING_TEMPLATE)

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
    if not token: return redirect('/')

    pinterest = OAuth2Session(CLIENT_ID, token=token)
    try:
        user = pinterest.get('https://api.pinterest.com/v5/user_account').json()
        boards_raw = pinterest.get('https://api.pinterest.com/v5/boards').json().get('items', [])
        boards = []

        for b in boards_raw:
            b_id = b['id']
            sections_raw = pinterest.get(f'https://api.pinterest.com/v5/boards/{b_id}/sections').json().get('items', [])
            section_previews = []

            for s in sections_raw:
                pins = pinterest.get(
                    f'https://api.pinterest.com/v5/boards/{b_id}/sections/{s["id"]}/pins'
                ).json().get('items', [])
                img = pick_best_image(pins[0].get('media', {}).get('images', {})) if pins else "https://via.placeholder.com/150x100?text=No+Image"
                section_previews.append({'id': s['id'], 'image': img})

            boards.append({
                'id': b_id,
                'name': b.get('name'),
                'cover_image': pick_best_image(b.get('media', {}).get('images', {})),
                'sections': section_previews or None,
                'description': b.get('description', '')
            })

        return render_template_string(DASHBOARD_TEMPLATE, user=user, boards=boards)

    except Exception as e:
        return f"<h3>❌ Failed to load dashboard:</h3><pre>{str(e)}</pre>"

@app.route('/privacy')
def privacy():
    return redirect("https://www.termsfeed.com/live/90026cd3-68b4-415e-b50a-f7420791857c")

@app.route('/test')
def test(): return "✅ App is working!"

# === Landing Page Template ===
LANDING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>p!nlyzer</title>
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-color: #ffe6e6;
            font-family: 'Great Vibes', cursive;
            color: #4b0000;
        }
        .logo {
            font-size: 72px;
            margin-bottom: 40px;
            text-shadow: 2px 2px #ccc;
        }
        .btn-login {
            background: #800020;
            color: white;
            padding: 15px 30px;
            font-size: 32px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        .btn-login:hover {
            background: #a00030;
        }
    </style>
</head>
<body>
    <div class="logo">p!nlyzer</div>
    <button onclick="location.href='/login'" class="btn-login">Log in with Pinterest</button>
</body>
</html>
"""

# === Dashboard Template ===
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dashboard - p!nlyzer</title>
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
            font-weight: bold;
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
        .card-title {
            font-size: 24px;
        }
        .section-img {
            height: 100px;
            border-radius: 10px;
            margin: 5px;
        }
        .brand-button {
            position: absolute;
            top: 10px;
            right: 12px;
            font-size: 24px;
            background: none;
            border: none;
            cursor: pointer;
            color: #800020;
        }
        .brand-button:hover {
            color: #b30059;
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
                <li>💬 Talk to your board</li>
            </ul>
        </div>

        <h3>Your Boards</h3>
        <div class="row">
            {% for board in boards %}
            <div class="col-md-4 board-card">
                <div class="card">
                    <button class="brand-button" title="Open features">⚚</button>
                    <img src="{{ board['cover_image'] }}" class="card-img-top" alt="Board Cover">
                    <div class="card-body">
                        <h5 class="card-title">{{ board['name'] }}</h5>
                        {% if board['sections'] %}
                            <div>
                                <p style="font-size: 18px;">Sections:</p>
                                {% for section in board['sections'] %}
                                    <img src="{{ section['image'] }}" class="section-img" alt="Section">
                                {% endfor %}
                            </div>
                        {% elif board['description'] %}
                            <p class="card-text">{{ board['description'] }}</p>
                        {% endif %}
                        <a href="https://www.pinterest.com/board/{{ board['id'] }}" class="btn btn-outline-dark mt-2" target="_blank">View Board</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

# === Run the App ===
if __name__ == "__main__":
    app.run(debug=True)

