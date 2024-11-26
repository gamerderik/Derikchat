import os
import dropbox
from flask import Flask, request, render_template, redirect, url_for, session
from flask_caching import Cache

# Flask Setup
app = Flask(__name__)

# Flask Caching Setup
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Dropbox Setup: Retrieve Dropbox access token from environment variables
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")  # Use environment variable for Dropbox token
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# File names and paths
FILE_NAME = "messages.txt"
USERS_FILE = "users.txt"
MESSAGES_PATH = "/messages.txt"
USERS_PATH = "/users.txt"

# Flask Secret Key: Retrieve from environment variable
SECRET_KEY = os.getenv("FLASK_SECRET_KEY")  # Use environment variable for Flask secret key
if not SECRET_KEY:
    raise RuntimeError("FLASK_SECRET_KEY is not set in environment variables")

app.secret_key = SECRET_KEY

# Admin password for clearing messages
ADMIN_PASSWORD = "Derik1408"

# Load messages from Dropbox with caching
@cache.cached()
def load_messages():
    """Load messages from Dropbox."""
    download_from_dropbox(MESSAGES_PATH, FILE_NAME)
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return file.read().splitlines()
    return []

# Save a message to Dropbox and clear the cache
def save_message(message):
    """Save a new message to Dropbox."""
    with open(FILE_NAME, "a") as file:
        file.write(message + "\n")
    upload_to_dropbox(FILE_NAME, MESSAGES_PATH)
    cache.delete_memoized(load_messages)  # Clear cache for messages

# Clear messages from Dropbox and reset the cache
def clear_messages():
    """Clear all messages in Dropbox and reset the global messages list."""
    open(FILE_NAME, 'w').close()  # Clear the file content locally
    upload_to_dropbox(FILE_NAME, MESSAGES_PATH)  # Clear the file on Dropbox
    cache.delete_memoized(load_messages)  # Clear cache for messages
    global messages
    messages = []

# Load users from Dropbox with caching
@cache.cached()
def load_users():
    """Load users from Dropbox."""
    download_from_dropbox(USERS_PATH, USERS_FILE)
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as file:
            return [line.strip().split(":") for line in file.readlines()]
    return []

# Save users to Dropbox and clear the cache
def save_user(username, password):
    """Save a new user to Dropbox."""
    with open(USERS_FILE, "a") as file:
        file.write(f"{username}:{password}\n")
    upload_to_dropbox(USERS_FILE, USERS_PATH)
    cache.delete_memoized(load_users)  # Clear cache for users

# Dropbox helper functions
def upload_to_dropbox(local_path, dropbox_path):
    """Upload a file to Dropbox."""
    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

def download_from_dropbox(dropbox_path, local_path):
    """Download a file from Dropbox."""
    try:
        metadata, response = dbx.files_download(dropbox_path)
        with open(local_path, "wb") as f:
            f.write(response.content)
    except dropbox.exceptions.ApiError:
        # File not found, create an empty file
        open(local_path, "w").close()

# Global messages variable (loaded from cache)
messages = load_messages()

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
