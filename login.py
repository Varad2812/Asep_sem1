from flask import Flask, request, render_template, redirect, flash, url_for, session
import sqlite3
import os
import hashlib
from db_config import get_db, init_db
from config import USER_SETTINGS_TABLE

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Add a flag to track first request
_is_first_request = True

def init_database():
    """Initialize all required database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create user settings table
    cursor.execute(USER_SETTINGS_TABLE)
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_login(email, password):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user from credentials table
        cursor.execute('SELECT username, password FROM credentials WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user and user[1] == hash_password(password):
            return True, user[0]  # Return True and username if credentials match
        return False, None
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False, None
    finally:
        if conn:
            conn.close()

@app.before_first_request
def before_first_request():
    """Initialize database before first request"""
    global _is_first_request
    if _is_first_request:
        init_database()
        _is_first_request = False

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')
        
        is_valid, username = verify_login(email, password)
        
        if is_valid:
            session['username'] = username
            session['email'] = email
            flash('Login successful! Welcome back.', 'success')
            # Show success message before redirecting
            return render_template('login.html')
        else:
            flash('Invalid email or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/signup')
def signup_redirect():
    return redirect(url_for('signup'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5006)