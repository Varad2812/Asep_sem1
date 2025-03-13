from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import requests
import datetime
import sqlite3
import os
import json
from config import TELEGRAM_CONFIG, FLASK_CONFIG, DB_CONFIG, USER_SETTINGS_TABLE
from scheduler import send_telegram_message

app = Flask(__name__)
app.secret_key = FLASK_CONFIG['SECRET_KEY']

# Telegram Bot Details from configuration
BOT_TOKEN = TELEGRAM_CONFIG['BOT_TOKEN']
CHAT_ID = TELEGRAM_CONFIG['CHAT_ID']
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Database path from configuration
DB_PATH = DB_CONFIG['PATH']

def init_db():
    """Initialize the database with required tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create reminders table with sent status
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            time TIMESTAMP NOT NULL,
            sent INTEGER DEFAULT 0,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create user settings table
        cursor.execute(USER_SETTINGS_TABLE)
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e

# Initialize database
init_db()

def get_user_telegram_id(user_id):
    """Get user's Telegram chat ID from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT telegram_chat_id 
            FROM user_settings 
            WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else CHAT_ID
    except Exception as e:
        print(f"Error getting user Telegram ID: {e}")
        return CHAT_ID

def update_user_telegram_id(user_id, chat_id):
    """Update user's Telegram chat ID in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_settings (user_id, telegram_chat_id)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                telegram_chat_id = ?,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, chat_id, chat_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating user Telegram ID: {e}")
        return False

@app.route('/update_telegram_config', methods=['POST'])
def update_telegram_config():
    """Update Telegram configuration for the current user"""
    if request.method == 'POST':
        new_chat_id = request.form.get('chat_id')
        user_id = session.get('user_id')
        
        if new_chat_id and user_id:
            # Test the new chat_id
            test_message = "Testing Telegram configuration. If you receive this message, your setup is correct!"
            if send_telegram_message(test_message, new_chat_id):
                if update_user_telegram_id(user_id, new_chat_id):
                    flash("Telegram configuration updated successfully!")
                else:
                    flash("Failed to save Telegram configuration.")
            else:
                flash("Failed to send test message. Please check your Telegram chat ID.")
        else:
            flash("Please provide both user ID and Telegram chat ID.")
            
        return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        scheduled_entries = {"medicine": [], "exercise": []}
        user_id = session.get('user_id')

        if request.method == 'POST' and user_id:
            # Retrieve multiple Medicine Reminder entries
            med_names = request.form.getlist('med_name')
            dosages = request.form.getlist('dosage')
            med_times = request.form.getlist('med_time')
            frequencies = request.form.getlist('frequency')
            instructions = request.form.getlist('additional_instructions')

            # Retrieve multiple Exercise Reminder entries
            exercise_types = request.form.getlist('exercise_type')
            durations = request.form.getlist('duration')
            exercise_times = request.form.getlist('exercise_time')
            exercise_specs_list = request.form.getlist('exercise_specs')

            now = datetime.datetime.now()
            
            # Process each Medicine entry
            for i in range(len(med_names)):
                if not med_names[i]:  # Skip empty entries
                    continue
                    
                try:
                    med_time_obj = datetime.datetime.strptime(med_times[i], "%H:%M").time()
                except ValueError:
                    flash("Time format error in Medicine entry. Please use HH:MM format.")
                    continue
                    
                med_datetime = datetime.datetime.combine(now.date(), med_time_obj)
                if med_datetime < now:
                    med_datetime += datetime.timedelta(days=1)
                    
                med_message = (
                    f"Hi! Here is your Medicine Reminder:\n"
                    f"Medicine: {med_names[i]}\n"
                    f"Dosage: {dosages[i]}\n"
                    f"Frequency: {frequencies[i]}\n"
                    f"Instructions: {instructions[i]}"
                )
                
                # Store in database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO reminders (user_id, type, description, time)
                    VALUES (?, ?, ?, ?)
                """, (user_id, 'medicine', med_message, med_datetime))
                conn.commit()
                conn.close()
                
                scheduled_entries["medicine"].append({
                    "medicine": med_names[i],
                    "dosage": dosages[i],
                    "time": med_datetime.strftime("%Y-%m-%d %H:%M"),
                    "frequency": frequencies[i],
                    "instructions": instructions[i]
                })

            # Process each Exercise entry
            for i in range(len(exercise_types)):
                if not exercise_types[i]:  # Skip empty entries
                    continue
                    
                try:
                    exercise_time_obj = datetime.datetime.strptime(exercise_times[i], "%H:%M").time()
                except ValueError:
                    flash("Time format error in Exercise entry. Please use HH:MM format.")
                    continue
                    
                exercise_datetime = datetime.datetime.combine(now.date(), exercise_time_obj)
                if exercise_datetime < now:
                    exercise_datetime += datetime.timedelta(days=1)
                    
                exercise_message = (
                    f"Hi! Here is your Exercise Reminder:\n"
                    f"Exercise: {exercise_types[i]}\n"
                    f"Duration: {durations[i]}\n"
                    f"Specifications: {exercise_specs_list[i]}"
                )
                
                # Store in database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO reminders (user_id, type, description, time)
                    VALUES (?, ?, ?, ?)
                """, (user_id, 'exercise', exercise_message, exercise_datetime))
                conn.commit()
                conn.close()
                
                scheduled_entries["exercise"].append({
                    "exercise": exercise_types[i],
                    "duration": durations[i],
                    "time": exercise_datetime.strftime("%Y-%m-%d %H:%M"),
                    "specs": exercise_specs_list[i]
                })

            flash("Reminders scheduled successfully!")
            return render_template('index2.html', scheduled_entries=scheduled_entries)

        return render_template('index2.html', scheduled_entries=scheduled_entries)
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        flash("An error occurred while processing your request. Please try again.")
        return render_template('index2.html', scheduled_entries={"medicine": [], "exercise": []})

@app.route('/get_reminders', methods=['GET'])
def get_reminders():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, description, time 
            FROM reminders 
            WHERE user_id = ?
            ORDER BY time DESC
        """, (user_id,))
        reminders = [
            {
                'type': row[0],
                'description': row[1],
                'time': row[2]
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        
        return jsonify({
            'status': 'success',
            'reminders': reminders
        })
    except Exception as e:
        print(f"Error in get_reminders: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=FLASK_CONFIG['DEBUG'], port=5005)
