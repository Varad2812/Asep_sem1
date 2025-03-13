import os
import sqlite3
from pathlib import Path

# Get the base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Database configuration
if os.environ.get('VERCEL_ENV') == 'production':
    # Use /tmp directory in production (Vercel)
    DB_PATH = '/tmp/patient_data.db'
else:
    # Use local path in development
    DB_PATH = os.path.join(BASE_DIR, 'patient_data.db')

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create credentials table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create other necessary tables here...

    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn 