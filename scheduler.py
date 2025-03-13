from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import sqlite3
import datetime
from config import DB_CONFIG, TELEGRAM_CONFIG
import requests

def send_telegram_message(message, chat_id):
    """Send message to Telegram"""
    bot_token = TELEGRAM_CONFIG['BOT_TOKEN']
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {'chat_id': chat_id, 'text': message}
    try:
        response = requests.post(api_url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def check_and_send_reminders():
    """Check for due reminders and send them"""
    try:
        conn = sqlite3.connect(DB_CONFIG['PATH'])
        cursor = conn.cursor()
        
        # Get current time
        now = datetime.datetime.now()
        
        # Get reminders that are due
        cursor.execute("""
            SELECT r.user_id, r.description, r.time, us.telegram_chat_id
            FROM reminders r
            LEFT JOIN user_settings us ON r.user_id = us.user_id
            WHERE r.time <= ? AND r.time > ? - interval '1 hour'
        """, (now, now))
        
        reminders = cursor.fetchall()
        
        for user_id, description, time, chat_id in reminders:
            if chat_id:  # Only send if user has configured Telegram
                send_telegram_message(description, chat_id)
        
        conn.close()
    except Exception as e:
        print(f"Error checking reminders: {e}")

def init_scheduler():
    """Initialize the scheduler"""
    scheduler = BackgroundScheduler()
    
    # Schedule reminder check every hour
    scheduler.add_job(
        check_and_send_reminders,
        CronTrigger(minute=0),  # Run at the start of every hour
        id='check_reminders',
        replace_existing=True
    )
    
    scheduler.start()
    return scheduler

# Initialize scheduler when the module is imported
scheduler = init_scheduler() 