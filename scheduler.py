from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import sqlite3
import datetime
from config import DB_CONFIG, TELEGRAM_CONFIG
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_telegram_message(message, chat_id):
    """Send message to Telegram with enhanced error handling"""
    bot_token = TELEGRAM_CONFIG['BOT_TOKEN']
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'  # Enable HTML formatting
    }
    try:
        response = requests.post(api_url, data=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"Successfully sent message to chat_id: {chat_id}")
            return True
        else:
            logger.error(f"Failed to send message. Status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

def check_and_send_reminders():
    """Check for due reminders and send them with enhanced error handling"""
    try:
        conn = sqlite3.connect(DB_CONFIG['PATH'])
        cursor = conn.cursor()
        
        # Get current time
        now = datetime.datetime.now()
        
        # Get reminders that are due (within the last hour)
        cursor.execute("""
            SELECT r.user_id, r.description, r.time, us.telegram_chat_id
            FROM reminders r
            LEFT JOIN user_settings us ON r.user_id = us.user_id
            WHERE r.time <= ? AND r.time > ? - interval '1 hour'
            AND r.sent = 0  -- Only get unsent reminders
        """, (now, now))
        
        reminders = cursor.fetchall()
        
        for user_id, description, time, chat_id in reminders:
            if chat_id:  # Only send if user has configured Telegram
                if send_telegram_message(description, chat_id):
                    # Mark reminder as sent
                    cursor.execute("""
                        UPDATE reminders 
                        SET sent = 1, sent_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND time = ?
                    """, (user_id, time))
                    logger.info(f"Marked reminder as sent for user {user_id}")
        
        conn.commit()
        conn.close()
        logger.info(f"Processed {len(reminders)} reminders")
    except Exception as e:
        logger.error(f"Error checking reminders: {e}")
        if conn:
            conn.close()

def init_scheduler():
    """Initialize the scheduler with enhanced error handling"""
    try:
        scheduler = BackgroundScheduler()
        
        # Schedule reminder check every hour
        scheduler.add_job(
            check_and_send_reminders,
            CronTrigger(minute=0),  # Run at the start of every hour
            id='check_reminders',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Scheduler initialized successfully")
        return scheduler
    except Exception as e:
        logger.error(f"Error initializing scheduler: {e}")
        return None

# Initialize scheduler
scheduler = init_scheduler() 