import os
from flask import Flask, request, render_template, redirect, url_for, session
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")
socketio = SocketIO(app)

# File paths for storing data
MESSAGES_FILE = "messages.txt"
USERS_FILE = "users.txt"

# Helper Functions
def save_message_to_file(username, message):
    """Save a new message to a text file."""
    with open(MESSAGES_FILE, "a") as file:
        file.write(f"{username}|||{message}|||{datetime.now().isoformat()}\n")

def load_messages_from_file():
    """Load all messages from the text file."""
    if not os.path.exists(MESSAGES_FILE):
        return []
    with open(MESSAGES_FILE, "r") as file:
        return [line.strip().split("|||")[:2] for line in file.readlines()]

def save_user_to_file(username, password):
    """Save a new user to the text file."""
    with open(USERS_FILE, "a") as file:
        file.write(f"{username}|||{generate_password_hash(password)}\n")

def authenticate_user(username, password):
    """Authenticate a user using the text file."""
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, "r") as file:
        for line in file:
            stored_username, stored_password = line.strip().split("|||")
            if stored_username == username and check_password_hash(stored_password, password):
                return True
    return False

@app.route("/", methods=["GET", "POST"])
def home():
    error_message = None  # Initialize error message

    if 'username' in session:
        # User is logged in, show the chat
        if request.method == "POST":
            message = request.form.get("message")
            if message and message.strip():
                username = session['username']
                save_message_to_file(username, message)
                # Emit message to the clients using SocketIO
                socketio.emit('new_message', {'username': username, 'message': message}, broadcast=True)
            else:
                error_message = "Message cannot be blank."

        clear_password = request.form.get("clear_password")
        if clear_password:
            if clear_password == ADMIN_PASSWORD:
                open(MESSAGES_FILE, "w").close()  # Clear all messages in the text file
                return redirect(url_for('home'))
            else:
                error_message = "Incorrect password. Access denied."

        messages = load_messages_from_file()
        return render_template("index.html", messages=reversed(messages), error_message=error_message)

    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    error_message = None

    if request.method == "POST":
        username = request.form.get("username").strip()  # Remove leading/trailing spaces
        password = request.form.get("password").strip()  # Remove leading/trailing spaces

        if username and password:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, "r") as file:
                    if any(line.split("|||")[0] == username for line in file):
                        error_message = "Username already taken."
                        return render_template("register.html", error_message=error_message)

            save_user_to_file(username, password)
            return redirect(url_for('login'))
        else:
            error_message = "Both fields are required."

    return render_template("register.html", error_message=error_message)

@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None

    if request.method == "POST":
        username = request.form.get("username").strip()  # Remove leading/trailing spaces
        password = request.form.get("password").strip()  # Remove leading/trailing spaces

        if username and password:
            if authenticate_user(username, password):
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

# WebSocket event for new messages
@socketio.on('connect')
def on_connect():
    messages = load_messages_from_file()
    for msg in messages:
        emit('new_message', {'username': msg[0], 'message': msg[1]})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
