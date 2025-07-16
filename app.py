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
            board_id = board['id']
            section_resp = pinterest.get(f'https://api.pinterest.com/v5/boards/{board_id}/sections')
            sections = section_resp.json().get('items', [])

            section_previews = []
            for section in sections:
                sec_id = section.get('id')
                pin_resp = pinterest.get(f'https://api.pinterest.com/v5/boards/{board_id}/sections/{sec_id}/pins')
                pins = pin_resp.json().get('items', [])
                img = pins[0]['media']['images']['original']['url'] if pins else "https://via.placeholder.com/150x100?text=No+Image"
                section_previews.append({'id': sec_id, 'image': img})

            boards.append({
                'id': board_id,
                'name': board.get('name'),
                'description': board.get('description', ''),
                'cover_image': board.get('media', {}).get('image_cover_url') or "https://via.placeholder.com/300x200?text=No+Image",
                'sections': section_previews if section_previews else None
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

# HTML Template with ⚚ dropdown trigger
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
            position: relative;
        }
        .card {
            border: none;
            border-radius: 12px;
            background-color: #fff0f5;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        .card-title {
            font-size: 24px;
        }
        .section-img {
            height: 100px;
            border-radius: 10px;
            margin: 5px;
        }
        .dropdown-trigger {
            position: absolute;
            top: 10px;
            right: 15px;
            font-size: 26px;
            cursor: pointer;
            user-select: none;
        }
        .dropdown-menu {
            position: absolute;
            top: 45px;
            right: 15px;
            background: rgba(255,255,255,0.9);
            border: 1px solid #b30059;
            border-radius: 8px;
            padding: 10px;
            z-index: 10;
            display: none;
        }
        .dropdown-menu.show {
            display: block;
        }
        .dropdown-menu li {
            list-style: none;
            padding: 6px 0;
        }
        .dropdown-menu li:hover {
            background: #ffd6e6;
            cursor: pointer;
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
                <li>💬 Talk to My Board</li>
            </ul>
        </div>

        <h3>Your Boards</h3>
        <div class="row">
            {% for board in boards %}
            <div class="col-md-4 board-card">
                <div class="card">
                    <div class="dropdown-trigger" onclick="toggleDropdown('{{ board['id'] }}')">⚚</div>
                    <ul class="dropdown-menu" id="dropdown-{{ board['id'] }}">
                        <li>🎨 Theme & Color Analysis</li>
                        <li>🧠 Psychological Profile</li>
                        <li>🧚‍♀️ Generate Board Persona</li>
                        <li>🧭 Vibe Insights</li>
                        <li>💬 Talk to My Board</li>
                        <li>🗺️ Content Overlap Map (coming soon)</li>
                        <li>📄 Export Board Report</li>
                    </ul>
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
                        <a href="https://www.pinterest.com/board/{{ board['id'] }}" class="btn btn-outline-dark mt-2" target="_blank">View Board</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        function toggleDropdown(boardId) {
            const el = document.getElementById('dropdown-' + boardId);
            el.classList.toggle('show');
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)

