import os
import json
from flask import Flask, request, render_template, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

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
    """Save a new message to Firebase."""
    ref = db.reference("messages")
    ref.push({
        "username": username,
        "message": message,
        "timestamp": datetime.now().isoformat()  # Store timestamp in ISO 8601 format
    })


def load_messages_from_firebase():
    """Load all messages from Firebase."""
    ref = db.reference("messages")
    messages = ref.order_by_child("timestamp").get()
    return [(msg.get("username", ""), msg.get("message", "")) for msg in messages.values()] if messages else []


def save_user_to_firebase(username, password):
    """Save a new user to Firebase."""
    ref = db.reference("users")
    ref.child(username).set({
        "password": generate_password_hash(password)
    })


def authenticate_user(username, password):
    """Authenticate a user using Firebase."""
    ref = db.reference("users")
    user = ref.child(username).get()
    return user and check_password_hash(user["password"], password)


# Routes
@app.route("/", methods=["GET", "POST"])
def home():
    error_message = None

    if 'username' in session:
        # User is logged in, show the chat
        if request.method == "POST":
            message = request.form.get("message")
            if message and message.strip():
                save_message_to_firebase(session['username'], message)
            else:
                error_message = "Message cannot be blank."

            clear_password = request.form.get("clear_password")
            if clear_password:
                if clear_password == ADMIN_PASSWORD:
                    db.reference("messages").delete()
                    return redirect(url_for('home'))
                else:
                    error_message = "Incorrect admin password."

        messages = load_messages_from_firebase()
        return render_template("index.html", messages=reversed(messages), error_message=error_message)

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
                save_user_to_firebase(username, password)
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


if __name__ == "__main__":
    app.run(debug=True)
