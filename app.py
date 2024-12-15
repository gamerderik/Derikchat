import eventlet
eventlet.monkey_patch()

import os
import json
import html
from flask import Flask, request, render_template, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import firebase_admin
from firebase_admin import credentials, db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)  # Initialize SocketIO

# Secret key for Flask session
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")
ADMIN_PASSWORD = "Derik1408"

# Initialize Firebase Admin SDK
firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")  # Get Firebase credentials from environment
cred = credentials.Certificate(json.loads(firebase_credentials))  # Parse JSON string
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://derikchat-1408-default-rtdb.firebaseio.com/'  # Replace with your Firebase DB URL
})


# Firebase Helper Functions
def save_message_to_firebase(username, message):
    """Save a new message to Firebase with HTML escaping and preserving newlines."""
    escaped_message = html.escape(message).replace('\n', '<br>')  # Escape HTML
    ref = db.reference("messages")
    ref.push({
        "username": username,
        "message": escaped_message,
        "timestamp": datetime.now().isoformat()  # ISO 8601 format for consistency
    })


def load_messages_from_firebase():
    """Load all messages from Firebase."""
    ref = db.reference("messages")
    messages = ref.order_by_child("timestamp").get()
    return [(msg["username"], msg["message"]) for msg in messages.values()] if messages else []


# Routes
@app.route("/", methods=["GET", "POST"])
def home():
    if 'username' in session:
        username = session['username']
        messages = load_messages_from_firebase()  # Fetch old messages
        return render_template("index.html", username=username, messages=messages)
    return redirect(url_for('login'))



@app.route("/register", methods=["GET", "POST"])
def register():
    error_message = None
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        if username and password:
            ref = db.reference("users")
            if ref.child(username).get():
                error_message = "Username already taken."
            else:
                ref.child(username).set({
                    "username": username,
                    "password": generate_password_hash(password)
                })
                return redirect(url_for('login'))
        else:
            error_message = "Both fields are required."
    return render_template("register.html", error_message=error_message)


@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        if username and password:
            ref = db.reference("users")
            user = ref.child(username).get()
            if user and check_password_hash(user["password"], password):
                session['username'] = username
                return redirect(url_for('home'))
            else:
                error_message = "Invalid username or password."
        else:
            error_message = "Both fields are required."
    return render_template("login.html", error_message=error_message)


@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# Socket.IO Events
@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a new message."""
    username = data['username']
    message = data['message']
    save_message_to_firebase(username, message)  # Save to Firebase
    emit('receive_message', {'username': username, 'message': html.escape(message).replace('\n', '<br>')}, broadcast=True)


@socketio.on('join')
def handle_join(data):
    """Handle a user joining the chat and send them the message history."""
    username = data['username']
    # Load previous messages from Firebase
    messages = load_messages_from_firebase()
    # Send the message history to the new user
    emit('message_history', {'messages': messages}, room=request.sid)



if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
