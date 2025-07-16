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

# Placeholder AI caption generator
def generate_image_caption(image_url):
    return "Generated caption for an image."

# NLP setup
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

# Utility: Chat history in session
def get_chat_history():
    return session.setdefault('chat_history', [])

def clear_chat_history():
    session['chat_history'] = []

@app.route('/')
def home():
    return render_template_string(LANDING_PAGE_TEMPLATE)

@app.route('/login', methods=['GET'])
def login():
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    auth_url, state = oauth.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, state=session.get('oauth_state'))
    try:
        token = oauth.fetch_token(
            TOKEN_URL,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        session['oauth_token'] = token
        return redirect('/dashboard')
    except Exception as e:
        return f"<h3>Error:</h3><pre>{e}</pre>"

@app.route('/dashboard')
def dashboard():
    token = session.get('oauth_token')
    if not token:
        return redirect('/login')

    oauth = OAuth2Session(CLIENT_ID, token=token)
    try:
        user = oauth.get('https://api.pinterest.com/v5/user_account').json()
        resp = oauth.get('https://api.pinterest.com/v5/boards')
        boards = []
        for b in resp.json().get('items', []):
            pins = oauth.get(f"https://api.pinterest.com/v5/boards/{b['id']}/pins").json().get('items', [])
            cover = pins[0]['media']['images']['original']['url'] if pins else "https://via.placeholder.com/300"
            boards.append({
                'id': b['id'],
                'name': b.get('name'),
                'description': b.get('description', ''),
                'cover_image': cover,
                'pins': pins
            })
        session['boards'] = boards
        return render_template_string(DASHBOARD_TEMPLATE, user=user, boards=boards)
    except Exception as e:
        return f"<h3>Error loading dashboard:</h3><pre>{e}</pre>"

# Feature: Theme & Color Analysis
@app.route('/feature/analyze_theme_color/<board_id>')
def analyze_theme_color(board_id):
    boards = session.get('boards', [])
    board = next((b for b in boards if b['id'] == board_id), None)
    if not board:
        return jsonify({'error': 'Board not found'}), 404

    counts = {}
    for pin in board['pins']:
        try:
            resp = requests.get(pin['media']['images']['original']['url'])
            ct = ColorThief(io.BytesIO(resp.content))
            r, g, b = ct.get_color(quality=1)
            hexc = f'#{r:02x}{g:02x}{b:02x}'
            counts[hexc] = counts.get(hexc, 0) + 1
        except:
            pass
    sorted_colors = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return jsonify({'dominant_colors': sorted_colors[:5], 'total_pins': len(board['pins'])})

# Feature: Psychological Profile
@app.route('/feature/psych_profile/<board_id>')
def psych_profile(board_id):
    boards = session.get('boards', [])
    board = next((b for b in boards if b['id'] == board_id), None)
    if not board:
        return jsonify({'error': 'Board not found'}), 404

    texts = []
    for pin in board['pins']:
        d = pin.get('description')
        texts.append(d if d else generate_image_caption(pin['media']['images']['original']['url']))
    text = " ".join(texts)
    sentiment = sia.polarity_scores(text)
    mood = "Positive" if sentiment['compound'] > 0.3 else ("Negative" if sentiment['compound'] < -0.3 else "Neutral")
    return jsonify({'sentiment': sentiment, 'mood': mood})

# Feature: Generate Board Persona
@app.route('/feature/generate_persona/<board_id>')
def generate_persona(board_id):
    boards = session.get('boards', [])
    board = next((b for b in boards if b['id'] == board_id), None)
    if not board:
        return jsonify({'error': 'Board not found'}), 404
    words = []
    for pin in board['pins']:
        desc = pin.get('description')
        if desc:
            words += desc.lower().split()
    from collections import Counter
    common = Counter([w for w in words if len(w) > 4]).most_common(5)
    persona = "Likes: " + ", ".join(w for w, _ in common) if common else "No dominant theme"
    return jsonify({'persona': persona})

# Feature: Vibe Insights (simple)
@app.route('/feature/vibe_insights/<board_id>')
def vibe_insights(board_id):
    p = psych_profile(board_id).json
    colors = analyze_theme_color(board_id).json.get('dominant_colors', [])
    vibe = f"{p['mood']} mood; Colors: {[c for c, _ in colors]}"
    return jsonify({'vibe': vibe})

# Feature: Talk to My Board
@app.route('/feature/talk_to_my_board/<board_id>', methods=['GET', 'POST'])
def talk_to_my_board(board_id):
    if request.method == 'GET':
        return jsonify({'history': get_chat_history()})
    data = request.json or {}
    msg = data.get('message', '')
    hist = get_chat_history()
    hist.append({'role': 'user', 'message': msg})
    reply = f"AI Reply to '{msg}'. (Stub)"
    hist.append({'role': 'bot', 'message': reply})
    session['chat_history'] = hist
    return jsonify({'reply': reply, 'history': hist})

@app.route('/feature/clear_chat')
def clear_chat():
    clear_chat_history()
    return jsonify({'status': 'cleared'})

# Feature: Export Report
@app.route('/feature/export_report/<board_id>')
def export_report(board_id):
    boards = session.get('boards', [])
    board = next((b for b in boards if b['id'] == board_id), None)
    if not board:
        return "<h3>Board not found</h3>", 404

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 750, f"Board Report: {board['name']}")
    resp = analyze_theme_color(board_id).json
    y = 720
    for color, cnt in resp.get('dominant_colors', []):
        rgb = tuple(int(color[i:i+2], 16)/255 for i in (1, 3, 5))
        c.setFillColorRGB(*rgb)
        c.rect(72, y, 40, 20, fill=True, stroke=False)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(120, y+5, f"{color} – {cnt}")
        y -= 30
    c.save()
    buf.seek(0)
    return send_file(buf, download_name=f"{board['name']}_report.pdf", as_attachment=True, mimetype="application/pdf")

@app.route('/privacy')
def privacy():
    return "<h1>Privacy Policy</h1><p>We don’t store data.</p>"

# Add test route for Pillow
@app.route('/test-pillow')
def test_pillow():
    try:
        from PIL import Image
        return "✅ Pillow installed!"
    except ImportError:
        return "❌ Pillow NOT installed."

# Templates
LANDING_PAGE_TEMPLATE = """..."""
DASHBOARD_TEMPLATE = """..."""

if __name__ == "__main__":
    app.run(debug=True)
