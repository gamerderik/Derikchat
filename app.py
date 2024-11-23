import os
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)

FILE_NAME = "messages.txt"
USERS_FILE = "users.txt"
SECRET_KEY = "your-secret-key"  # Set a secret key for session management
ADMIN_PASSWORD = "Derik1408"

# Load existing messages
def load_messages():
    """Load messages from the file."""
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return file.read().splitlines()
    return []

# Save a new message
def save_message(message):
    """Save a new message to the file."""
    with open(FILE_NAME, "a") as file:
        file.write(message + "\n")

# Clear all messages
def clear_messages():
    """Clear all messages in the file and reset the global messages list."""
    open(FILE_NAME, 'w').close()  # Clear the file content
    global messages
    messages = []  # Clear the in-memory list of messages

# User registration and login handling
def load_users():
    """Load users from the file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as file:
            return [line.strip().split(":") for line in file.readlines()]
    return []

def save_user(username, password):
    """Save a new user to the users file."""
    with open(USERS_FILE, "a") as file:
        file.write(f"{username}:{password}\n")

# Global variable for messages
messages = load_messages()

# Setup the Flask session
app.secret_key = SECRET_KEY

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
