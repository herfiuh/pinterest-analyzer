from flask import Flask, redirect, request, session, render_template_string, jsonify
from requests_oauthlib import OAuth2Session
from transformers import BlipProcessor, BlipForConditionalGeneration
from colorthief import ColorThief
import requests
from io import BytesIO
import colorsys
import os

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")


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
        return redirect('/onboarding')  # 👈 Go to onboarding instead
    except Exception as e:
        return f"<h3>❌ Error during authentication:</h3><pre>{str(e)}</pre>"
    
@app.route('/onboarding')
def onboarding():
    return render_template_string(SPIRAL_TEMPLATE)

@app.route('/onboarding_stage2')
def onboarding_stage2():
    return render_template_string(ONBOARDING_TEMPLATE)


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

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ======= Backend API Endpoints for features =======

# Analyze Theme (colors, general vibe)

def get_caption(image_url):
    resp = requests.get(image_url)
    img = BytesIO(resp.content)
    pixel_data = img.getvalue()
    inputs = processor(images=pixel_data, return_tensors="pt")
    out = model.generate(**inputs)
    return processor.decode(out[0], skip_special_tokens=True)

def get_palette(image_url, num_colors=5):
    resp = requests.get(image_url)
    img = BytesIO(resp.content)
    ct = ColorThief(img)
    palette = ct.get_palette(color_count=num_colors)
    # Convert rgb tuples to hex
    return ['#%02x%02x%02x' % rgb for rgb in palette]

@app.route('/analyze_theme/<board_id>')
def analyze_theme(board_id):
    pinterest = OAuth2Session(CLIENT_ID, token=session['oauth_token'])
    pins = pinterest.get(f'https://api.pinterest.com/v5/boards/{board_id}/pins').json().get('items', [])
    
    captions, palettes, combined = [], [], []
    for pin in pins[:10]:  # limit to 10
        img_url = pin.get('media', {}).get('images', {}).get('orig', {}).get('url')
        if not img_url: continue
        cap = get_caption(img_url)
        pal = get_palette(img_url)
        captions.append(cap)
        palettes.extend(pal)
        combined.append({'caption': cap, 'palette': pal})

    theme = f"{captions[0].split()[0] if captions else 'Visual'} vibes with {len(palettes)} colors"
    
    return jsonify({
        'board_id': board_id,
        'captions': captions,
        'dominant_palette': palettes[:5],
        'combined': combined,
        'theme_summary': theme
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
            position: relative;
            overflow: hidden;
            transition: background-color 0.3s, color 0.3s;
        }

        h1 {
            font-size: 64px;
            margin-bottom: 40px;
            text-shadow: 1px 1px #ccc;
            z-index: 1;
        }

        a.btn {
            font-size: 24px;
            padding: 15px 30px;
            background-color: #ffe6ea;
            border: 2px solid #b30000;
            color: #b30000;
            z-index: 1;
            transition: background-color 0.3s, color 0.3s, border 0.3s;
        }

        a.btn:hover {
            background-color: #ffccd5;
            color: #990000;
        }

        .flair {
            position: absolute;
            font-size: 20px;
            color: #cc8888;
            opacity: 0.5;
            animation: floaty 4s ease-in-out infinite alternate;
        }

        @keyframes floaty {
            0% { transform: translateY(0); }
            100% { transform: translateY(-10px); }
        }

        #toggle-theme {
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 999;
            font-size: 18px;
            border-radius: 30px;
        }
    </style>
</head>
<body>
    <button id="toggle-theme" class="btn btn-sm btn-outline-dark">🌙</button>

    <h1>p!nlyzer</h1>
    <a href="/login" class="btn">Login with Pinterest</a>

    {% for i in range(25) %}
    <div class="flair" style="
        top: {{ (loop.index * 37) % 100 }}%;
        left: {{ (loop.index * 53) % 100 }}%;
        animation-delay: {{ (loop.index * 0.3) % 2 }}s;
    ">୨୧</div>
    {% endfor %}

    <script>
        const toggleBtn = document.getElementById('toggle-theme');
        const flairEls = document.querySelectorAll('.flair');
        const loginBtn = document.querySelector('a.btn');

        function setTheme(dark) {
            document.body.style.backgroundColor = dark ? '#1e1e1e' : '#ffe6e6';
            document.body.style.color = dark ? '#f2f2f2' : '#4b0000';
            toggleBtn.textContent = dark ? '☀️' : '🌙';
            flairEls.forEach(f => f.style.color = dark ? '#555' : '#cc8888');
            loginBtn.style.backgroundColor = dark ? '#2e2e2e' : '#ffe6ea';
            loginBtn.style.color = dark ? '#ff9999' : '#b30000';
            loginBtn.style.borderColor = dark ? '#ff9999' : '#b30000';
        }

        // Load from localStorage
        const darkMode = localStorage.getItem('darkMode') === 'true';
        setTheme(darkMode);

        toggleBtn.addEventListener('click', () => {
            const newMode = !(localStorage.getItem('darkMode') === 'true');
            localStorage.setItem('darkMode', newMode);
            setTheme(newMode);
        });
    </script>
</body>
</html>
"""

SPIRAL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>p!nlyzer Loading</title>
    <style>
        body {
            margin: 0;
            background: #ffe6e6;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .spiral {
            width: 200px;
            height: 200px;
            border: 10px solid transparent;
            border-top: 10px solid #ff99aa;
            border-right: 10px solid #ffb3c6;
            border-radius: 50%;
            animation: spin 3s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg) scale(1); opacity: 1; }
            50% { transform: rotate(720deg) scale(1.2); opacity: 0.6; }
            100% { transform: rotate(1440deg) scale(0); opacity: 0; }
        }
    </style>
</head>
<body>
    <div class="spiral"></div>

    <script>
        setTimeout(() => {
            window.location.href = '/onboarding_stage2';
        }, 3000);
    </script>
</body>
</html>
"""


ONBOARDING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>welcome to p!nlyzer</title>
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet">
    <style>
        body {
            background: #fff0f5;
            color: #4b0000;
            font-family: 'Great Vibes', cursive;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 50px;
            height: 100vh;
            text-align: center;
            animation: fadeIn 2s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h1 {
            font-size: 48px;
            margin-bottom: 30px;
        }

        p {
            font-size: 22px;
            max-width: 800px;
            margin-bottom: 20px;
            opacity: 0;
            animation: fadeIn 1.5s ease forwards;
        }

        p:nth-of-type(1) { animation-delay: 0.5s; }
        p:nth-of-type(2) { animation-delay: 1s; }
        p:nth-of-type(3) { animation-delay: 1.5s; }
        p:nth-of-type(4) { animation-delay: 2s; }

        .cta-btn {
            margin-top: 40px;
            font-size: 20px;
            background: #ffe6ea;
            border: 2px solid #b30059;
            color: #b30059;
            padding: 12px 24px;
            border-radius: 30px;
            cursor: pointer;
            transition: background 0.3s, color 0.3s;
            animation: fadeIn 1.5s ease forwards;
            animation-delay: 2.5s;
            opacity: 0;
        }

        .cta-btn:hover {
            background: #ffccda;
            color: #800033;
        }
    </style>
</head>
<body>
    <h1>welcome, curator ✧˖°</h1>

    <p>what if your boards had more potential? more power? more reach?</p>
    <p>what if you could talk to them — and they talked back?</p>
    <p>what if expert analysis revealed the hidden patterns behind your pins… your taste… your curation?</p>
    <p>what if your boards could do more than just inspire — what if they could manifest with you?</p>
    <p>or maybe... you just want the validation of knowing your aesthetic is actually elite.</p>

    <a href="/dashboard" class="cta-btn">I want in!</a>
</body>
</html>
"""


DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>p!nlyzer dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #ffe6e6;
            font-family: 'Great Vibes', cursive;
            color: #4b0000;
            padding: 30px;
            transition: background-color 0.3s, color 0.3s;
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

        /* Theme dark mode styles */
        body.dark-mode {
            background-color: #1e1e1e;
            color: #ffe6e6;
        }

        body.dark-mode .catalogue {
            background: rgba(70, 0, 35, 0.4);
            border-color: #ff99cc;
        }

        body.dark-mode .card {
            background-color: #2c2c2c;
            color: #ffe6e6;
        }

        /* Theme + brb button container */
        .top-buttons {
            position: absolute;
            top: 20px;
            right: 30px;
            display: flex;
            gap: 10px;
        }

        .theme-btn {
            border: none;
            background: transparent;
            font-size: 24px;
            cursor: pointer;
        }

        .brb-btn {
            font-family: Arial, sans-serif;
            border-radius: 20px;
            font-size: 14px;
            padding: 6px 12px;
        }
    </style>
</head>
<body>
    <div class="top-buttons">
        <button id="toggle-theme" class="theme-btn">🌙</button>
        <a href="/logout" class="btn btn-outline-danger brb-btn">brb</a>
    </div>

    <div class="container">
        <div class="logo">p!nlyzer</div>

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

        // Theme toggle with localStorage
        const toggleTheme = document.getElementById('toggle-theme');
        const body = document.body;

        if (localStorage.getItem('theme') === 'dark') {
            body.classList.add('dark-mode');
            toggleTheme.textContent = '☀️';
        }

        toggleTheme.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            const isDark = body.classList.contains('dark-mode');
            toggleTheme.textContent = isDark ? '☀️' : '🌙';
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    </script>
</body>
</html>
"""





if __name__ == "__main__":
    app.run(debug=True)

