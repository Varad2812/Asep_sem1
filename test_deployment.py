import requests
import json
import os
from datetime import datetime, timedelta

# Replace with your Vercel deployment URL
BASE_URL = os.getenv('VERCEL_URL', 'https://your-project.vercel.app')

def test_login():
    """Test login functionality"""
    print("\nTesting login...")
    try:
        response = requests.post(f"{BASE_URL}/login", data={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        print(f"Login response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Login test failed: {e}")
        return False

def test_telegram_setup():
    """Test Telegram configuration"""
    print("\nTesting Telegram setup...")
    try:
        # First, get the session cookie from login
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/login", data={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        
        # Test Telegram configuration update
        response = session.post(f"{BASE_URL}/update_telegram_config", data={
            'chat_id': 'your-test-chat-id'
        })
        print(f"Telegram setup response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram setup test failed: {e}")
        return False

def test_reminder_creation():
    """Test reminder creation"""
    print("\nTesting reminder creation...")
    try:
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/login", data={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        
        # Create a test reminder
        reminder_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
        response = session.post(f"{BASE_URL}/", data={
            'med_name': ['Test Medicine'],
            'dosage': ['1 tablet'],
            'med_time': [reminder_time],
            'frequency': ['Once daily'],
            'additional_instructions': ['Take with water']
        })
        print(f"Reminder creation response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Reminder creation test failed: {e}")
        return False

def test_reminder_retrieval():
    """Test reminder retrieval"""
    print("\nTesting reminder retrieval...")
    try:
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/login", data={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        
        response = session.get(f"{BASE_URL}/get_reminders")
        print(f"Reminder retrieval response: {response.status_code}")
        if response.status_code == 200:
            reminders = response.json()
            print(f"Retrieved reminders: {json.dumps(reminders, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Reminder retrieval test failed: {e}")
        return False

def run_all_tests():
    """Run all deployment tests"""
    print("Starting deployment tests...")
    
    tests = {
        "Login": test_login,
        "Telegram Setup": test_telegram_setup,
        "Reminder Creation": test_reminder_creation,
        "Reminder Retrieval": test_reminder_retrieval
    }
    
    results = {}
    for test_name, test_func in tests.items():
        print(f"\nRunning {test_name} test...")
        results[test_name] = test_func()
        print(f"{test_name} test {'passed' if results[test_name] else 'failed'}")
    
    print("\nTest Summary:")
    for test_name, result in results.items():
        print(f"{test_name}: {'✓' if result else '✗'}")

if __name__ == "__main__":
    run_all_tests() 