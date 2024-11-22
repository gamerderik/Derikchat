import os
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

FILE_NAME = "messages.txt"
ADMIN_PASSWORD = "Derik1408"

def load_messages():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return file.read().splitlines()  # Return as list
    return []

def save_message(message):
    with open(FILE_NAME, "a") as file:
        file.write(message + "\n")

def clear_messages():
    open(FILE_NAME, 'w').close()
    global messages
    messages = []

messages = load_messages()

@app.route("/", methods=["GET", "POST"])
def home():
    global messages
    error_message = None  # Initialize error message
    
    if request.method == "POST":
        message = request.form.get("message")
        if message:
            messages.append(message)
            save_message(message)
        
        clear_password = request.form.get("clear_password")
        if clear_password:
            if clear_password == ADMIN_PASSWORD:
                clear_messages()
                return redirect(url_for('home'))
            else:
                error_message = "Incorrect password. Access denied."  # Set the error message
                print("Incorrect password entered")  # Debugging line
        
        return redirect(url_for('home'))  # Redirect to avoid reposting messages

    return render_template("index.html", messages=reversed(messages), error_message=error_message)  # Pass the error message to the template

if __name__ == "__main__":
    app.run(debug=True)
