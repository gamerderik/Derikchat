import os
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, render_template, redirect, url_for, session
from flask_caching import Cache
import json

# Flask Setup
app = Flask(__name__)

# Flask Caching Setup
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Firebase Setup: Retrieve Firebase credentials from environment variables
firebase_credentials = json.loads(os.getenv("FIREBASE_CREDENTIALS_JSON"))
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)

# Firestore Client
db = firestore.client()

# Flask Secret Key: Retrieve from environment variable
SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("FLASK_SECRET_KEY is not set in environment variables")

app.secret_key = SECRET_KEY

# Admin password for clearing messages
ADMIN_PASSWORD = "Derik1408"

# Load messages from Firebase with caching
@cache.cached()
def load_messages():
    """Load messages from Firebase Firestore."""
    messages_ref = db.collection('messages')
    docs = messages_ref.stream()
    return [doc.to_dict()['message'] for doc in docs]

# Save a message to Firebase and clear the cache
def save_message(message):
    """Save a new message to Firebase Firestore."""
    messages_ref = db.collection('messages')
    messages_ref.add({'message': message})
    cache.delete_memoized(load_messages)  # Clear cache for messages

# Clear messages from Firebase and reset the cache
def clear_messages():
    """Clear all messages in Firebase Firestore and reset the global messages list."""
    messages_ref = db.collection('messages')
    docs = messages_ref.stream()
    for doc in docs:
        doc.reference.delete()
    cache.delete_memoized(load_messages)  # Clear cache for messages

# Load users from Firebase with caching
@cache.cached()
def load_users():
    """Load users from Firebase Firestore."""
    users_ref = db.collection('users')
    docs = users_ref.stream()
    return [(doc.to_dict()['username'], doc.to_dict()['password']) for doc in docs]

# Save users to Firebase and clear the cache
def save_user(username, password):
    """Save a new user to Firebase Firestore."""
    users_ref = db.collection('users')
    users_ref.add({'username': username, 'password': password})
    cache.delete_memoized(load_users)  # Clear cache for users

@app.route("/", methods=["GET", "POST"])
def home():
    global messages
    error_message = None  # Initialize error message

    if 'username' in session:
        # User is logged in, show the chat
        if request.method == "POST":
            message = request.form.get("message")
            if message and message.strip():
                username = session['username']
                full_message = f"{username}: {message}"
                messages.append(full_message)
                save_message(full_message)
                return redirect(url_for('home'))  # Redirect after processing the form
            else:
                error_message = "Message cannot be blank."

            clear_password = request.form.get("clear_password")
            if clear_password:
                if clear_password == ADMIN_PASSWORD:
                    clear_messages()
                    return redirect(url_for('home'))
                else:
                    error_message = "Incorrect password. Access denied."

        return render_template("index.html", messages=reversed(messages), error_message=error_message)

    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    error_message = None

    if request.method == "POST":
        username = request.form.get("username").strip()  # Remove leading/trailing spaces
        password = request.form.get("password").strip()  # Remove leading/trailing spaces

        if username and password:
            users = load_users()
            if any(u[0] == username for u in users):
                error_message = "Username already taken."
            else:
                save_user(username, password)
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
            users = load_users()
            user = next((u for u in users if u[0] == username and u[1] == password), None)

            if user:
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
