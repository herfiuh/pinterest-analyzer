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
    return redirect('/dashboard')

@app.route('/login', methods=['GET'])
def login():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    url, state = pinterest.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    return redirect(url)

@app.route('/callback')
def callback():
    pinterest = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, state=session.get('oauth_state'))
    try:
        token = pinterest.fetch_token(
            TOKEN_URL, client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        session['oauth_token'] = token
        return redirect('/dashboard')
    except Exception as e:
        return f"<h3>Error:</h3><pre>{str(e)}</pre>"

@app.route('/dashboard')
def dashboard():
    token = session.get('oauth_token')
    if not token:
        return redirect('/login')

    pinterest = OAuth2Session(CLIENT_ID, token=token)
    try:
        user = pinterest.get('https://api.pinterest.com/v5/user_account').json()
        boards_resp = pinterest.get('https://api.pinterest.com/v5/boards')
        boards_data = boards_resp.json().get('items', [])
        boards = []
        for b in boards_data:
            board = {
                'id': b['id'],
                'name': b.get('name'),
                'img': b.get('media', {}).get('image_cover_url') or "https://via.placeholder.com/300?text=No+Image",
                'url': b.get('url'),
                'sections': []
            }
            # Fetch sections & one latest pin img
            sec_resp = pinterest.get(f"https://api.pinterest.com/v5/boards/{b['id']}/sections")
            secs = sec_resp.json().get('items', [])
            for s in secs:
                pin_resp = pinterest.get(f"https://api.pinterest.com/v5/sections/{s['id']}/pins?limit=1")
                pin_items = pin_resp.json().get('items', [])
                img = pin_items[0].get('media', {}).get('images', [{}])[0].get('url') if pin_items else None
                board['sections'].append({'id': s['id'], 'title': s['title'], 'img': img})
            boards.append(board)

        return render_template_string(TEMPLATE, user=user, boards=boards)
    except Exception as e:
        return f"<h3>Error loading dashboard:</h3><pre>{str(e)}</pre>"

# Rendered HTML + CSS
TEMPLATE = """
<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
  body { background:#ffe6e6; font-family:'Great Vibes', cursive; color:#4b0000; }
  .top-bar { display:flex; justify-content:space-between; align-items:center; padding:1rem; }
  .brand { font-size:2.5rem; }
  .keypad-btn { font-family:'Great Vibes', cursive; font-size:1.5rem;
    background:#800020;color:#fff;border:none;padding:0.5rem 1rem;border-radius:8px;
  }
  .overlay { display:none; position:fixed;top:0;left:0;width:100%;height:100%;
     background:rgba(255,255,255,0.95); z-index:10; padding:2rem; }
  .overlay.open { display:block; }
  .catalogue-item { margin:1rem 0; font-size:1.3rem; cursor:pointer; }
  .board-card img { height:200px;object-fit:cover;border-radius:8px; }
</style>
</head><body>

<div class="top-bar">
  <div class="brand">P!nlyzer</div>
  <button class="keypad-btn" onclick="document.getElementById('catalogue').classList.toggle('open')">P!NLYZE</button>
</div>

<div id="catalogue" class="overlay">
  <h2>Select a function</h2>
  <div class="catalogue-item">🎨 Analyze Colors & Themes</div>
  <div class="catalogue-item">🌈 Vibe & Energy Mood</div>
  <div class="catalogue-item">🧠 Psychological Profile</div>
  <div class="catalogue-item">💬 Create Board Persona</div>
</div>

<div class="container mt-4">
  <h3>Welcome, {{ user['username'] }}</h3>
  <div class="row">
    {% for b in boards %}
      <div class="col-md-4 mb-4">
        <div class="card">
          <!-- Cover Image -->
          <img src="{{ b.img }}" class="card-img-top" alt="{{ b.name }}">
          <div class="card-body">
            <h5 class="card-title">{{ b.name }}</h5>
            {% if b.sections %}
              <p>Sections:</p>
              <div class="d-flex">
                {% for s in b.sections %}
                  {% if s.img %}
                    <img src="{{ s.img }}" width="60" class="me-2" style="border-radius:4px;">
                  {% endif %}
                {% endfor %}
              </div>
            {% endif %}
            <a href="https://pinterest.com{{ b.url }}" class="btn btn-outline-danger mt-2" target="_blank">
              View Board
            </a>
          </div>
        </div>
      </div>
    {% endfor %}
  </div>
</div>

</body></html>
"""

@app.route('/privacy')
def policy():
    return redirect("/privacy")  # unchanged

@app.route('/test')
def test():
    return "✅"

if __name__=="__main__":
    app.run(debug=True)
"""

