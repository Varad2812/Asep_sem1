import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask Configuration
FLASK_CONFIG = {
    'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key-here'),
    'DEBUG': os.getenv('FLASK_ENV', 'development') == 'development'
}

# Telegram Configuration
TELEGRAM_CONFIG = {
    'BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', 'your-telegram-bot-token'),
    'CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', 'your-telegram-chat-id')
}

# Database Configuration
DB_CONFIG = {
    'PATH': os.getenv('DATABASE_URL', '/tmp/patient_data.db')
}

# Email configuration (for future use)
EMAIL_CONFIG = {
    'SMTP_SERVER': os.getenv('SMTP_SERVER', ''),
    'SMTP_PORT': int(os.getenv('SMTP_PORT', 587)),
    'SMTP_USERNAME': os.getenv('SMTP_USERNAME', ''),
    'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD', ''),
    'SENDER_EMAIL': os.getenv('SENDER_EMAIL', '')
}

# User Settings Table Schema
USER_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY,
    telegram_chat_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""" 