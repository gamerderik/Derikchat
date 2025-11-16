<DOCUMENT filename="app.py">
import os
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key-change-in-production")
socketio = SocketIO(app, cors_allowed_origins="*")

# File paths
MESSAGES_FILE = "messages.json"
USERS_FILE = "users.json"
ADMIN_PASSWORD = "admin123"  # Change this!

# Initialize files
def init_files():
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)

init_files()

# === Helper Functions ===
def load_messages():
    try:
        with open(MESSAGES_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_messages(messages):
    with open(MESSAGES_FILE, "w") as f:
        json.dump(messages, f)

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_user(username, password_hash):
    users = load_users()
    users[username] = password_hash
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# === Routes ===
@app.route("/")
def index():
    if 'username' in session:
        return render_template("index.html")
    return redirect(url_for('index'))

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    users = load_users()
    stored_hash = users.get(username)

    if stored_hash and check_password_hash(stored_hash, password):
        session['username'] = username
        return jsonify({"success": True})
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if len(username) < 3 or len(password) < 4:
        return jsonify({"error": "Username ≥3, Password ≥4 chars"}), 400

    users = load_users()
    if username in users:
        return jsonify({"error": "Username taken"}), 400

    hashed = generate_password_hash(password)
    save_user(username, hashed)
    session['username'] = username
    return jsonify({"success": True})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop('username', None)
    return jsonify({"success": True})

@app.route("/api/check_session")
def check_session():
    if 'username' in session:
        return jsonify({"logged_in": True, "username": session['username']})
    return jsonify({"logged_in": False})

# === Socket.IO Events ===
@socketio.on('connect')
def handle_connect():
    if 'username' not in session:
        return False
    messages = load_messages()
    emit('load_messages', messages)

@socketio.on('send_message')
def handle_message(data):
    if 'username' not in session:
        return
    
    message = data.get('message', '').strip()
    if not message:
        return

    msg_obj = {
        "username": session['username'],
        "message": message.replace('\n', '<br>'),
        "timestamp": datetime.now().isoformat()
    }

    messages = load_messages()
    messages.append(msg_obj)
    save_messages(messages[-100:])  # Keep last 100

    emit('new_message', msg_obj, broadcast=True)

@socketio.on('clear_messages')
def handle_clear():
    if 'username' not in session:
        return
    
    # In real app: check if user is admin
    messages = []
    save_messages(messages)
    emit('messages_cleared', broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
</DOCUMENT>
