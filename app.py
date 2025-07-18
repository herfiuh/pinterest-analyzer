from flask import Flask, redirect, request, session, render_template_string, jsonify
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
            boards.append({
                'id': board['id'],
                'name': board.get('name'),
                'description': board.get('description', ''),
                'cover_image': board.get('media', {}).get('image_cover_url') or "https://via.placeholder.com/300x200?text=No+Image"
            })

        return render_template_string(DASHBOARD_TEMPLATE, user_info=user_info, boards=boards)
    except Exception as e:
        return f"<h3>❌ Failed to load dashboard:</h3><pre>{str(e)}</pre>"

# ======= Backend API Endpoints for features =======

# Analyze Theme (colors, general vibe)
@app.route('/analyze_theme/<board_id>')
def analyze_theme(board_id):
    # TODO: implement color analysis and theme extraction logic
    # Placeholder response
    return jsonify({
        'board_id': board_id,
        'theme_colors': ['#FF6F91', '#FF9671', '#FFC75F'],
        'description': 'Warm pastel vibes with bright energy',
    })

# Build Persona (psych profile of board owner from pins)
@app.route('/build_persona/<board_id>')
def build_persona(board_id):
    # TODO: implement psychological profile logic based on pins & boards
    return jsonify({
        'board_id': board_id,
        'persona': {
            'traits': ['Creative', 'Adventurous', 'Optimistic'],
            'summary': 'This user enjoys exploring new ideas with a positive outlook.'
        }
    })

# Talk to Board (chat-like interaction)
@app.route('/talk_to_board/<board_id>', methods=['POST'])
def talk_to_board(board_id):
    user_message = request.json.get('message', '')
    # TODO: integrate NLP/AI for chat response based on board content
    reply = f"Received your message on board {board_id}: {user_message}. (This is a placeholder reply.)"
    return jsonify({'reply': reply})

# Vibe/Energy Map
@app.route('/vibe_map/<board_id>')
def vibe_map(board_id):
    # TODO: create and return vibe/energy map visualization data
    return jsonify({
        'board_id': board_id,
        'vibe': 'Energetic and creative',
        'energy_score': 87
    })

# Pin similarity matrix
@app.route('/pin_similarity/<board_id>')
def pin_similarity(board_id):
    # TODO: calculate similarity matrix for pins on board
    return jsonify({
        'board_id': board_id,
        'similarities': [
            {'pin1': 'pin123', 'pin2': 'pin456', 'score': 0.85},
            {'pin1': 'pin789', 'pin2': 'pin101', 'score': 0.75}
        ]
    })

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
        img.card-img-top {
            border-radius: 15px 15px 0 0;
            object-fit: cover;
            height: 200px;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">p⚚nlyze</div>

        <div class="catalogue">
            <h2>p⚚nlyze</h2>
            <p>Select a board to:</p>
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
                            <li><a class="dropdown-item" href="#" onclick="triggerFeature('analyze_theme', '{{ board.id }}')">Analyze Theme</a></li>
                            <li><a class="dropdown-item" href="#" onclick="triggerFeature('build_persona', '{{ board.id }}')">Build Persona</a></li>
                            <li><a class="dropdown-item" href="#" onclick="triggerFeature('talk_to_board', '{{ board.id }}')">Talk to Board</a></li>
                            <li><a class="dropdown-item" href="#" onclick="triggerFeature('vibe_map', '{{ board.id }}')">Vibe/Energy Map</a></li>
                            <li><a class="dropdown-item" href="#" onclick="triggerFeature('pin_similarity', '{{ board.id }}')">Pin Similarity Matrix</a></li>
                        </ul>
                    </div>
                    <img src="{{ board.cover_image }}" class="card-img-top" alt="Board Cover">
                    <div class="card-body">
                        <h5 class="card-title">{{ board.name }}</h5>
                        {% if board.description %}
                        <p class="card-text">{{ board.description }}</p>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div id="feature-result" class="mt-5"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        async function triggerFeature(feature, boardId) {
            let endpoint = '/' + feature + '/' + boardId;
            let options = {};

            if(feature === 'talk_to_board') {
                let message = prompt("Say something to your board:");
                if(!message) return;
                options = {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message})
                };
            }

            try {
                const response = await fetch(endpoint, options);
                const data = await response.json();

                document.getElementById('feature-result').innerHTML = 
                    '<h4>Feature: ' + feature.replace(/_/g, ' ') + '</h4><pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (err) {
                alert('Error fetching feature data');
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)

