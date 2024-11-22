import os
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

FILE_NAME = "messages.txt"
ADMIN_PASSWORD = "Derik1408"

def load_messages():
    """Load messages from the file."""
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return file.read().splitlines()  # Return as list
    return []

def save_message(message):
    """Save a new message to the file."""
    with open(FILE_NAME, "a") as file:
        file.write(message + "\n")

def clear_messages():
    """Clear all messages in the file and reset the global messages list."""
    open(FILE_NAME, 'w').close()  # Clear the file content
    global messages
    messages = []  # Clear the in-memory list of messages

messages = load_messages()

@app.route("/", methods=["GET", "POST"])
def home():
    global messages
    error_message = None  # Initialize error message

    if request.method == "POST":
        # Handle message submission
        message = request.form.get("message")
        if message:
            messages.append(message)
            save_message(message)
        
        # Handle clearing messages with password
        clear_password = request.form.get("clear_password")
        if clear_password:
            if clear_password == ADMIN_PASSWORD:
                clear_messages()  # Clear messages if the password is correct
                return redirect(url_for('home'))  # Redirect to reload the page
            else:
                error_message = "Incorrect password. Access denied."  # Set the error message
    
    return render_template("index.html", messages=reversed(messages), error_message=error_message)

if __name__ == "__main__":
    app.run(debug=True)
