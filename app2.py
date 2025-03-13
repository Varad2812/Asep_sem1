from flask import Flask, send_file, jsonify, make_response, request
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import io
import os
from flask_cors import CORS
import base64
from datetime import datetime

app = Flask(__name__)

# Enable CORS for all origins
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    return response

# Configure paths
HOME = os.path.expanduser('~')
DESKTOP = os.path.join(HOME, 'Desktop')
ASEP_DIR = os.path.join(DESKTOP, 'asep')
DB_PATH = os.path.join(ASEP_DIR, 'patient_data.db')

def calculate_blood_sugar(row):
    """Calculate blood sugar level using available measurements"""
    values = []
    if pd.notna(row['post_prandial_glucose']):
        values.append(row['post_prandial_glucose'])
    if pd.notna(row['fasting_glucose']):
        values.append(row['fasting_glucose'])
    if pd.notna(row['hba1c']):
        # Convert HbA1c to estimated average glucose
        eag = (28.7 * row['hba1c']) - 46.7
        values.append(eag)
    
    return sum(values) / len(values) if values else None

def create_graph():
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get data from personal_details table
        query = """
        SELECT 
            post_prandial_glucose as 'Post Prandial Glucose',
            fasting_glucose as 'Fasting Glucose',
            hba1c as 'HbA1c',
            id as 'Reading Number'
        FROM personal_details
        WHERE post_prandial_glucose IS NOT NULL 
        OR fasting_glucose IS NOT NULL 
        OR hba1c IS NOT NULL
        ORDER BY id DESC
        LIMIT 10
        """
        
        df = pd.read_sql_query(query, conn)
        print("\nData retrieved from database:")
        print(df)
        conn.close()

        if len(df) == 0:
            raise Exception("No blood sugar readings found. Please add your readings in the main application first.")

        # Calculate average blood sugar level
        df['Average Blood Sugar'] = df.apply(calculate_blood_sugar, axis=1)

        # Create plot
        plt.figure(figsize=(12, 6))
        
        # Plot each measurement
        x = range(len(df))
        plt.plot(x, df['Post Prandial Glucose'], 'r-o', label='Post Prandial Glucose')
        plt.plot(x, df['Fasting Glucose'], 'b-o', label='Fasting Glucose')
        plt.plot(x, df['HbA1c'], 'g-o', label='HbA1c')
        plt.plot(x, df['Average Blood Sugar'], 'k--o', label='Average Blood Sugar')
        
        plt.title('Blood Sugar Measurements Over Time')
        plt.xlabel('Reading Number')
        plt.ylabel('Value (mg/dL for Glucose, % for HbA1c)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)

        # Save plot
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        return buf

    except Exception as e:
        print(f"Error creating graph: {str(e)}")
        raise e

@app.route('/', methods=['GET', 'OPTIONS'])
def show_graph():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Create database connection
        conn = sqlite3.connect(DB_PATH)
        
        # Get last 5 entries with date
        query = """
        SELECT 
            post_prandial_glucose,
            fasting_glucose,
            hba1c,
            date
        FROM personal_details
        WHERE post_prandial_glucose IS NOT NULL 
           OR fasting_glucose IS NOT NULL 
           OR hba1c IS NOT NULL
        ORDER BY id DESC
        LIMIT 5
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()

        if len(df) == 0:
            return "No data found. Please add readings in the main application first."

        # Convert dates to datetime objects
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate average blood sugar
        df['calculated_blood_sugar'] = df.apply(calculate_blood_sugar, axis=1)

        # Sort by date
        df = df.sort_values('date')

        # Create plot with a larger figure size
        plt.figure(figsize=(12, 8))
        
        # Plot all measurements
        plt.plot(df['date'], df['post_prandial_glucose'], 'r-o', label='Post Prandial Glucose')
        plt.plot(df['date'], df['fasting_glucose'], 'b-o', label='Fasting Glucose')
        plt.plot(df['date'], df['hba1c'], 'g-o', label='HbA1c')
        plt.plot(df['date'], df['calculated_blood_sugar'], 'k--o', label='Calculated Blood Sugar')
        
        plt.title('Blood Sugar Measurements Over Time')
        plt.xlabel('Date')
        plt.ylabel('Value (mg/dL for Glucose, % for HbA1c)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        
        # Rotate date labels for better readability
        plt.gcf().autofmt_xdate()
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save plot to memory
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        response = make_response(send_file(buf, mimetype='image/png'))
        response.headers['Content-Type'] = 'image/png'
        return response

    except Exception as e:
        print(f"Error: {str(e)}")  # Print error for debugging
        return jsonify({'error': str(e)}), 500

@app.route('/graph-data', methods=['GET', 'OPTIONS'])
def get_graph_data():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        conn = sqlite3.connect(DB_PATH)
        
        query = """
        SELECT 
            post_prandial_glucose,
            fasting_glucose,
            hba1c,
            date
        FROM personal_details
        WHERE post_prandial_glucose IS NOT NULL 
           OR fasting_glucose IS NOT NULL 
           OR hba1c IS NOT NULL
        ORDER BY id DESC
        LIMIT 5
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()

        if len(df) == 0:
            return jsonify({'error': 'No data found'}), 404

        # Convert dates to datetime objects
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # Calculate average blood sugar
        df['calculated_blood_sugar'] = df.apply(calculate_blood_sugar, axis=1)

        # Convert DataFrame to dict for JSON response
        data = df.to_dict(orient='records')
        
        response = jsonify({
            'success': True,
            'data': data
        })
        return response

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print(f"Database path: {DB_PATH}")
    print("Server running at:")
    print("  http://127.0.0.1:5002")
    print("  http://localhost:5002")
    # Run the server with all interfaces
    app.run(host='0.0.0.0', port=5002, debug=True)
