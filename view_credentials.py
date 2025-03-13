import sqlite3
from tabulate import tabulate
import os

def view_credentials_data():
    try:
        # Connect to the database
        conn = sqlite3.connect('patient_data.db')
        cursor = conn.cursor()

        # Get all data from credentials table including password
        cursor.execute('''
            SELECT id, username, email, password, created_at 
            FROM credentials
            ORDER BY id
        ''')
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        if not rows:
            print("\nNo credentials found in the database.")
            return

        # Define headers for the table
        headers = ['ID', 'Username', 'Email', 'Password (Hashed)', 'Created At']
        
        # Print the table using tabulate with full width for all columns
        print("\nCredentials Data:")
        print(tabulate(rows, headers=headers, tablefmt='grid'))
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    view_credentials_data() 