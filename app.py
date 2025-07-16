from flask import Flask, redirect, request, session, render_template_string, jsonify, send_file
from requests_oauthlib import OAuth2Session
import os
import io
from PIL import Image
import requests
from colorthief import ColorThief
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import threading

# --- For AI image captioning stub ---
# You can replace this with actual AI model calls later
def generate_image_caption(image_url):
    # Placeholder caption generation
    # In reality, use open source models like BLIP or others to caption image
    captions = [
        "A cozy living room with pastel colors",
        "Fashion outfit with floral prints",
        "Minimalist workspace with wooden desk",
        "Outdoor nature scene with trees and sunlight",
        "Modern kitchen with stainless steel appliances"
    ]
    import random
    return random.choice(captions)

# --- Setup NLP ---
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = '1525609'
CLIENT_SECRET = 'd9e41297b07020596772579074e308671f88fec5'
REDIRECT_URI = 'https://pinterest-analyzer.onrender.com/callback'

AUTHORIZATION_BASE_URL = 'https://www.pinterest.com/oauth/'
TOKEN_URL = 'https://api.pinterest.com/v5/oauth/token'
SCOPE = ['boards:read', 'pins:read']

# Store chat history in session
def get_chat_history():
    return session.setdefault('chat_history', [])

def clear_chat_history():
    session['chat_history'] = []

@app.route('/')
def home():
    return render_template_string(LANDING_PAGE_TEMPLATE)

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
            # Get pins for board
            pins_resp = pinterest.get(f'https://api.pinterest.com/v5/boards/{board_id}/pins')
            pins = pins_resp.json().get('items', [])

            # Generate cover image from first pin's image or placeholder
            if pins:
                first_pin = pins[0]
                cover_image = first_pin['media']['images']['original']['url']
            else:
                cover_image = "https://via.placeholder.com/300x200?text=No+Image"

            boards.append({
                'id': board_id,
                'name': board.get('name'),
                'description': board.get('description', ''),
                'cover_image': cover_image,
                'pins': pins  # pass pins for backend analysis
            })

        session['boards'] = boards  # Store for backend access

        return render_template_string(DASHBOARD_TEMPLATE, user_info=user_info, boards=boards)
    except Exception as e:
        return f"<h3>❌ Failed to load dashboard:</h3><pre>{str(e)}</pre>"

# --- Feature endpoints ---

@app.route('/feature/analyze_theme_color/<board_id>')
def analyze_theme_color(board_id):
    boards = session.get('boards', [])
    board = next((b for b in boards if b['id'] == board_id), None)
    if not board:
        return jsonify({'error': 'Board not found'}), 404

    color_counts = {}
    total_pins = len(board['pins'])
    for pin in board['pins']:
        try:
            img_url = pin['media']['images']['original']['url']
            resp = requests.get(img_url)
            img = Image.open(io.BytesIO(resp.content))
            color_thief = ColorThief(io.BytesIO(resp.content))
            dominant_color = color_thief.get_color(quality=1)
            # convert to hex
            hex_color = '#%02x%02x%02x' % dominant_color
            color_counts[hex_color] = color_counts.get(hex_color, 0) + 1
        except Exception:
            continue

    # sort by frequency
    sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
    result = {
        'total_pins': total_pins,
        'dominant_colors': sorted_colors[:5]
    }
    return jsonify(result)

@app.route('/feature/psych_profile/<board_id>')
def psych_profile(board_id):
    boards = session.get('boards', [])
    board = next((b for b in boards if b['id'] == board_id), None)
    if not board:
        return jsonify({'error': 'Board not found'}), 404

    # Aggregate descriptions and captions
    texts = []
    for pin in board['pins']:
        desc = pin.get('description')
        if desc:
            texts.append(desc)
        else:
            # generate caption stub
            img_url = pin['media']['images']['original']['url']
            caption = generate_image_caption(img_url)
            texts.append(caption)

    full_text = ' '.join(texts)

    # Sentiment analysis
    sentiment = sia.polarity_scores(full_text)

    # Simple psych profile based on sentiment
    if sentiment['compound'] > 0.3:
        mood = "Positive and upbeat"
    elif sentiment['compound'] < -0.3:
        mood = "Reflective and somber"
    else:
        mood = "Neutral and balanced"

    profile = {
        'summary': mood,
        'sentiment_scores': sentiment
    }
    return jsonify(profile)

@app.route('/feature/generate_persona/<board_id>')
def generate_persona(board_id):
    boards = session.get('boards', [])
    board = next((b for b in boards if b['id'] == board_id), None)
    if not board:
        return jsonify({'error': 'Board not found'}), 404

    # Very basic persona generation using keywords from pins
    keywords = []
    for pin in board['pins']:
        desc = pin.get('description')
        if desc:
            keywords.extend(desc.lower().split())

    # Simple frequency count
    from collections import Counter
    freq = Counter(keywords)
    common_words = [w for w, c in freq.most_common(10) if len(w) > 3]

    persona = f"This board likely belongs to someone interested in: {', '.join(common_words)}."
    return jsonify({'persona': persona})

@app.route('/feature/vibe_insights/<board_id>')
def vibe_insights(board_id):
    # Combining color and psych to give a vibe summary
    color_data = analyze_theme_color(board_id).json[0]
    profile_data = psych_profile(board_id).json[0]

    vibe = "This board gives off a "
    # Simplified logic
    if profile_data['summary'] == "Positive and upbeat":
        vibe += "vibrant and cheerful vibe."
    elif profile_data['summary'] == "Reflective and somber":
        vibe += "calm and thoughtful vibe."
    else:
        vibe += "balanced and neutral vibe."

    vibe += f" Dominant colors include {', '.join([c for c, _ in color_data])}."

    return jsonify({'vibe': vibe})

@app.route('/feature/talk_to_my_board/<board_id>', methods=['GET', 'POST'])
def talk_to_my_board(board_id):
    if request.method == 'GET':
        history = get_chat_history()
        return jsonify({'history': history})

    data = request.json
    user_msg = data.get('message', '')
    if not user_msg:
        return jsonify({'error': 'No message sent'}), 400

    # Basic echo with "AI" reply placeholder
    history = get_chat_history()
    history.append({'role': 'user', 'message': user_msg})

    # Fake AI reply - in real life would integrate AI model + context from board data
    reply = f"🤖 [AI Reply to '{user_msg}'] Sorry, feature under construction."

    history.append({'role': 'bot', 'message': reply})
    session['chat_history'] = history
    return jsonify({'reply': reply, 'history': history})

@app.route('/feature/clear_chat')
def clear_chat():
    clear_chat_history()
    return jsonify({'status': 'Chat history cleared'})

@app.route('/feature/export_report/<board_id>')
def export_report(board_id):
    boards = session.get('boards', [])
    board = next((b for b in boards if b['id'] == board_id), None)
    if not board:
        return "<h3>❌ Board not found</h3>", 404

    # Generate PDF report with simple text + colors
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(72, 750, f"Board Report: {board['name']}")

    # Theme & color summary stub
    c.setFont("Helvetica", 12)
    c.drawString(72, 720, "Theme & Color Analysis:")
    color_analysis = analyze_theme_color(board_id).json
    if color_analysis:
        y = 700
        for color, count in color_analysis.get('dominant_colors', []):
            c.setFillColorRGB(*tuple(int(color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)))
            c.rect(72, y, 50, 20, fill=True, stroke=False)
            c.setFillColorRGB(0,0,0)
            c.drawString(130, y+5, f"{color} ({count} pins)")
            y -= 30

    # Finalize PDF
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"{board['name']}_report.pdf", mimetype='application/pdf')


# --- Templates ---

LANDING_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>p!nlyzer Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #ffe6e6;
            font-family: 'Great Vibes', cursive;
            color: #4b0000;
            margin: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }
        h1 {
            font-size: 80px;
            margin-bottom: 60px;
            text-shadow: 1px 1px #ccc;
        }
        .login-btn {
            font-family: 'Arial', sans-serif;
            background-color: #b30059;
            color: white;
            border: none;
            padding: 20px 40px;
            border-radius: 30px;
            font-size: 24px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .login-btn:hover {
            background-color: #850042;
        }
        /* subtle background pattern */
        .pattern {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: 0;
        }
        .pattern span {
            position: absolute;
            color: #cc99a1;
            user-select: none;
            font-size: 28px;
            opacity: 0.15;
        }
    </style>
</head>
<body>
    <h1>p!nlyzer</h1>
    <button class="login-btn" onclick="location.href='/login'">Login with Pinterest</button>

    <div class="pattern" aria-hidden="true">
        <!-- Randomly placed "୨୧" -->
        {% for i in range(40) %}
            <span style="top:{{ (loop.index0 * 7) % 100 }}vh; left:{{ (loop.index0 * 13) % 100 }}vw; color: rgba(204, 153, 161, 0.15);">୨୧</span>
        {% endfor %}
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>p!nlyzer Dashboard</title>
<style>
    body {
        font-family: 'Arial', sans-serif;
        background-color: #ffe6e6;
        margin: 0;
        padding: 20px;
        color: #4b0000;
    }
    header {
        font-family: 'Great Vibes', cursive;
        font-size: 36px;
        margin-bottom: 30px;
    }
    .board-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
    }
    .board {
        position: relative;
        width: 280px;
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 0 10px rgba(75,0,0,0.15);
    }
    .board img {
        width: 100%;
        height: 160px;
        object-fit: cover;
        display: block;
    }
    .board-info {
        padding: 12px;
    }
    .board-name {
        font-weight: bold;
        font-size: 18px;
        margin: 0 0 6px 0;
    }
    .board-description {
        font-size: 14px;
        color: #8b0000;
        height: 42px;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .feature-btn {
        position: absolute;
        top: 12px;
        right: 12px;
        background: white;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        box-shadow: 0 0 5px rgba(0,0,0,0.15);
        cursor: pointer;
        font-size: 22px;
        color: #b30059;
        display: flex;
        align-items: center;
        justify-content: center;
        user-select: none;
        transition: background-color 0.3s ease;
    }
    .feature-btn:hover {
        background-color: #b30059;
        color: white;
    }
    .dropdown {
        position: absolute;
        top: 56px;
        right: 12px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        padding: 8px 0;
        display: none;
        width: 250px;
        z-index: 10;
    }
    .dropdown.show {
        display: block;
    }
    .dropdown-item {
        padding: 10px 20px;
        font-size: 14px;
        color: #4b0000;
        cursor: pointer;
        border-bottom: 1px solid #eee;
    }
    .dropdown-item:last-child {
        border-bottom: none;
    }
    .dropdown-item:hover {
        background-color: #ffe6e6;
    }
</style>
<script>
function toggleDropdown(id) {
    const dropdown = document.getElementById('dropdown-' + id);
    if (dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
    } else {
        // Close others
        document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('show'));
        dropdown.classList.add('show');
    }
}

function featureClicked(boardId, feature) {
    alert("Feature: " + feature + "\\nBoard ID: " + boardId + "\\nFeature backend not fully implemented yet.");
    // Here you would add AJAX calls to trigger backend processing and show results dynamically
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('.feature-btn') && !e.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('show'));
    }
});
</script>
</head>
<body>
<header>p!nlyzer Dashboard</header>
<div class="board-container">
{% for board in boards %}
    <div class="board">
        <img src="{{ board.cover_image }}" alt="Cover image for {{ board.name }}" />
        <div class="board-info">
            <h3 class="board-name">{{ board.name }}</h3>
            <p class="board-description">{{ board.description }}</p>
        </div>
        <div class="feature-btn" onclick="toggleDropdown('{{ board.id }}')" title="⚚">⚚</div>
        <div id="dropdown-{{ board.id }}" class="dropdown">
            <div class="dropdown-item" onclick="featureClicked('{{ board.id }}', 'Theme & Color Analysis')">🎨 Theme & Color Analysis</div>
            <div class="dropdown-item" onclick="featureClicked('{{ board.id }}', 'Psychological Profile')">🧠 Psychological Profile</div>
            <div class="dropdown-item" onclick="featureClicked('{{ board.id }}', 'Generate Board Persona')">🧚‍♀️ Generate Board Persona</div>
            <div class="dropdown-item" onclick="featureClicked('{{ board.id }}', 'Vibe Insights')">🧭 Vibe Insights</div>
            <div class="dropdown-item" onclick="featureClicked('{{ board.id }}', 'Talk to My Board')">💬 Talk to My Board</div>
            <div class="dropdown-item disabled" style="color:#ccc; cursor:not-allowed;">🗺️ Content Overlap Map (coming soon)</div>
            <div class="dropdown-item" onclick="featureClicked('{{ board.id }}', 'Export Board Report')">📄 Export Board Report</div>
        </div>
    </div>
{% endfor %}
</div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
