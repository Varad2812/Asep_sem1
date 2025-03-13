from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import sqlite3
import os
import hashlib
import re
from functools import wraps
from db_config import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

# Database path
DB_PATH = os.environ.get('DB_PATH', '/tmp/patient_data.db')

def init_db():
    """Initialize the database and create tables if they don't exist."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Create credentials table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized successfully at {DB_PATH}")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

# Initialize database when the application starts
init_db()

def hash_password(password):
    """Hash the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):  
    """Validate email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """
    Validate password strength:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, ""

def is_valid_username(username):
    """
    Validate username:
    - At least 4 characters
    - Only alphanumeric characters and underscores
    - Must start with a letter
    """
    if len(username) < 4:
        return False, "Username must be at least 4 characters long"
    if not username[0].isalpha():
        return False, "Username must start with a letter"
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

@app.route('/')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate input
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('signup'))

        # Validate username
        valid_username, username_error = is_valid_username(username)
        if not valid_username:
            flash(username_error, 'error')
            return redirect(url_for('signup'))

        # Validate email
        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return redirect(url_for('signup'))

        # Validate password
        valid_password, password_error = is_valid_password(password)
        if not valid_password:
            flash(password_error, 'error')
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('signup'))

        try:
            conn = get_db()
            cursor = conn.cursor()

            # Check if username or email already exists
            cursor.execute('SELECT username, email FROM credentials WHERE username = ? OR email = ?', (username, email))
            existing_user = cursor.fetchone()
            if existing_user:
                if existing_user[0] == username:
                    flash('Username already exists', 'error')
                else:
                    flash('Email already registered', 'error')
                return redirect(url_for('signup'))

            # Hash the password and store user data
            hashed_password = hash_password(password)
            cursor.execute('''
                INSERT INTO credentials (username, email, password)
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))

            conn.commit()
            conn.close()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))  # Redirect directly to login route

        except Exception as e:
            flash(f'Error during registration: {str(e)}', 'error')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login')
def login_redirect():
    return redirect(url_for('login'))

if __name__ == '__main__':
    print(f"Signup server starting. Database path: {DB_PATH}")
    app.run(debug=True, port=5009)