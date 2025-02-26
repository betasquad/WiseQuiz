import os
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template_string, request, redirect, url_for, session
import threading
import time
import webbrowser

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "super_secret_key"  # Required for session storage

# Google Sheets authentication
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet by URL
sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1dcQiwJVKEDhis5qHTuHjbu6lor_e4BZz29QhY22I5-0/edit?usp=drive_link').sheet1

@app.route('/')
def quiz():
    # Get quiz data from Google Sheets
    data = sheet.get_all_records()  # This will fetch all rows as a list of dictionaries
    
    # Filter out phrases where "Corrects" is 10 or more
    df_filtered = [row for row in data if row["Corrects"] < 10]

    # If all phrases have "Corrects" ≥ 10, stop the quiz
    if not df_filtered:
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Quiz Complete</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #e3f2fd; }
                h1 { color: #0d47a1; font-size: 26px; }
            </style>
        </head>
        <body>
            <h1>🎉 Well done! You've mastered all phrases! 🎉</h1>
        </body>
        </html>
        """)

    # Select a random row
    row = random.choice(df_filtered)  # Randomly pick a question
    current_phrase = row["Phrases"]
    correct_answer = row["One Word"]
    correct_count = row["Corrects"]
    visibility_count = row["Attempts"]

    # Generate options (1 correct, 3 incorrect)
    incorrect_answers = [r["One Word"] for r in data if r["One Word"] != correct_answer]
    options = [correct_answer] + random.sample(incorrect_answers, 3)
    random.shuffle(options)

    # Render HTML dynamically
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>OWS Quiz</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 10px; background-color: #e3f2fd; }
            .container { width: 95%; max-width: 400px; margin: auto; background: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 15px rgba(0,0,0,0.2); position: relative; }
            h1 { font-size: 18px; color: #333; }
            h2 { color: #0d47a1; font-size: 22px; margin-bottom: 20px; }
            .option { display: block; margin: 10px auto; padding: 15px; border: none; cursor: pointer; width: 90%; text-align: center; font-size: 18px; background: #42a5f5; color: white; border-radius: 5px; transition: 0.3s; }
            .option:hover { background-color: #1e88e5; }
            .correct { background-color: #2e7d32 !important; } /* Green */
            .wrong { background-color: #c62828 !important; } /* Red */
            .timer { font-size: 18px; color: #0d47a1; font-weight: bold; position: absolute; top: 10px; right: 20px; }
            .info { font-size: 14px; color: #333; font-weight: bold; margin-top: 15px; }
        </style>
        <script>
            var timeLeft = 10;
            function countdown() {
                var timerDisplay = document.getElementById("timer");
                if (timeLeft <= 0) {
                    window.location.href = "/timeout";  // Redirect if time is up
                } else {
                    timerDisplay.innerHTML = "⏳ " + timeLeft + "s";
                    timeLeft--;
                    setTimeout(countdown, 1000);
                }
            }
            window.onload = countdown;

            function highlightAnswer(selectedOption) {
                fetch('/answer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'option=' + encodeURIComponent(selectedOption)
                }).then(response => {
                    var buttons = document.querySelectorAll(".option");
                    buttons.forEach(button => {
                        if (button.innerText === "{{ correct_answer }}") {
                            button.classList.add("correct");  // Green for correct
                        } else if (button.innerText === selectedOption) {
                            button.classList.add("wrong");  // Red for wrong
                        }
                        button.disabled = true;  // Disable buttons after selection
                    });
                    setTimeout(() => { window.location.href = "/"; }, 2000); // Move to next question in 2 seconds
                });
            }
        </script>
    </head>
    <body>
        <div class="container">
            <div class="timer" id="timer">⏳ 10s</div>
            <h1>What is the one-word substitution for:</h1>
            <h2>{{ phrase }}</h2>
            {% for option in options %}
                <button class="option" type="button" onclick="highlightAnswer('{{ option }}')">{{ option }}</button>
            {% endfor %}
            <div class="info">Corrects: {{ correct }} | Attempts: {{ visibility }}</div>
        </div>
    </body>
    </html>
    """, phrase=current_phrase, options=options, correct=correct_count, visibility=visibility_count, correct_answer=correct_answer)

@app.route('/answer', methods=['POST'])
def answer():
    global sheet, current_phrase, correct_answer

    selected_option = request.form.get("option")
    cell = sheet.find(current_phrase)  # Find the row in the sheet that contains the current phrase
    row_index = cell.row  # Get the row index where the current phrase is located

    # Update the Attempts column (Visibility)
    attempts_col = sheet.find('Attempts').col  # Find the column index for 'Attempts'
    current_attempts = int(sheet.cell(row_index, attempts_col).value)  # Get the current attempts count
    sheet.update_cell(row_index, attempts_col, current_attempts + 1)  # Increment attempts by 1

    # If the selected answer is correct, increment the Corrects column
    if selected_option == correct_answer:
        correct_col = sheet.find('Corrects').col  # Find the column index for 'Corrects'
        current_corrects = int(sheet.cell(row_index, correct_col).value)  # Get the current correct count
        sheet.update_cell(row_index, correct_col, current_corrects + 1)  # Increment correct count by 1

    return "OK"

@app.route('/timeout')
def timeout():
    return redirect(url_for('quiz'))

# Function to run Flask in a background thread
def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Wait a few seconds for Flask to start, then open in browser
time.sleep(2)
webbrowser.open("http://127.0.0.1:5000")