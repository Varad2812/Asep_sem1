import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set this before importing pyplot
import matplotlib.pyplot as plt
from datetime import datetime
from flask import Flask, send_file, render_template
import io
import os
import sqlite3
from db_config import get_db
import base64
from io import BytesIO

app = Flask(__name__)

# Configure paths
HOME = os.path.expanduser('~')
DESKTOP = os.path.join(HOME, 'Desktop')
ASEP_DIR = os.path.join(DESKTOP, 'asep')
DB_PATH = os.path.join(ASEP_DIR, 'patient_data.db')

print(f"Database path: {DB_PATH}")

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

@app.route('/')
def home():
    try:
        # Generate the graph data
        graph_data = generate_graph_data()
        if isinstance(graph_data, tuple) and len(graph_data) == 2:
            return graph_data  # Error message
        
        # Convert plot to base64 string
        img_base64 = base64.b64encode(graph_data.getvalue()).decode('utf-8')
        
        return render_template('graph.html', graph_data=img_base64)
    except Exception as e:
        return f"Error: {str(e)}"

def generate_graph_data():
    try:
        # Create database connection
        conn = sqlite3.connect(DB_PATH)
        
        # Get last 5 entries with all required fields
        query = """
        SELECT 
            h.post_prandial_glucose,
            h.fasting_glucose,
            h.hba1c,
            h.systolic_bp,
            h.diastolic_bp,
            h.report_date,
            p.full_name
        FROM health_metrics h
        LEFT JOIN personal_details p ON h.patient_id = p.id
        ORDER BY h.report_date DESC
        LIMIT 5;
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) == 0:
            return "No data found", 404

        # Reverse the order to show oldest to newest
        df = df.iloc[::-1]

        # Create figure with more space for labels
        plt.style.use('bmh')  # Using 'bmh' style instead of seaborn
        fig = plt.figure(figsize=(15, 10))
        
        # Set background color to white
        fig.patch.set_facecolor('white')
        
        # Create subplots with specific height ratios and spacing
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 1], hspace=0.3)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        
        # Set background color for subplots
        ax1.set_facecolor('white')
        ax2.set_facecolor('white')
        
        # Add title with proper spacing
        fig.suptitle('Health Metrics Over Time', fontsize=16, y=0.95)

        # Plot glucose values on the first subplot
        x = range(len(df))
        
        # Plot glucose values with adjusted marker sizes and styles
        if not df['post_prandial_glucose'].isna().all():
            ax1.plot(x, df['post_prandial_glucose'], 'r-o', label='Post Prandial', linewidth=2, markersize=8)
        if not df['fasting_glucose'].isna().all():
            ax1.plot(x, df['fasting_glucose'], 'b-o', label='Fasting', linewidth=2, markersize=8)
        if not df['hba1c'].isna().all():
            ax1.plot(x, df['hba1c'], 'g-o', label='HbA1c', linewidth=2, markersize=8)

        # Configure first subplot
        ax1.set_title('Blood Glucose Levels', pad=20, fontsize=14)
        ax1.set_xlabel('Date', fontsize=12, labelpad=10)
        ax1.set_ylabel('Glucose (mg/dL) / HbA1c (%)', fontsize=12, labelpad=10)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=10)
        ax1.tick_params(axis='both', which='major', labelsize=10)

        # Add value labels on the first subplot
        for line in ax1.lines:
            for x_val, y_val in zip(x, line.get_ydata()):
                if not pd.isna(y_val):
                    ax1.annotate(f'{y_val:.1f}', 
                               (x_val, y_val), 
                               textcoords="offset points", 
                               xytext=(0,10), 
                               ha='center',
                               fontsize=9)

        # Plot blood pressure on the second subplot
        if not df['systolic_bp'].isna().all():
            ax2.plot(x, df['systolic_bp'], 'm-o', label='Systolic BP', linewidth=2, markersize=8)
        if not df['diastolic_bp'].isna().all():
            ax2.plot(x, df['diastolic_bp'], 'c-o', label='Diastolic BP', linewidth=2, markersize=8)

        # Configure second subplot
        ax2.set_title('Blood Pressure', pad=20, fontsize=14)
        ax2.set_xlabel('Date', fontsize=12, labelpad=10)
        ax2.set_ylabel('Blood Pressure (mmHg)', fontsize=12, labelpad=10)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=10)
        ax2.tick_params(axis='both', which='major', labelsize=10)

        # Add value labels on the second subplot
        for line in ax2.lines:
            for x_val, y_val in zip(x, line.get_ydata()):
                if not pd.isna(y_val):
                    ax2.annotate(f'{int(y_val)}', 
                               (x_val, y_val), 
                               textcoords="offset points", 
                               xytext=(0,10), 
                               ha='center',
                               fontsize=9)

        # Set x-axis labels for both subplots
        dates = [d.split()[0] for d in df['report_date']]  # Get just the date part
        for ax in [ax1, ax2]:
            ax.set_xticks(x)
            ax.set_xticklabels(dates, rotation=45, ha='right')

        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save plot to memory with extra padding for labels
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white', 
                   pad_inches=0.5)
        buf.seek(0)
        plt.close()

        return buf
        
    except Exception as e:
        print(f"Error generating graph: {str(e)}")
        return f"Error: {str(e)}", 500

def create_graphs(username):
    """Create graphs for the 5 most recent entries"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get the 5 most recent entries for the user
        cursor.execute('''
            SELECT post_prandial_glucose, fasting_glucose, systolic_bp, diastolic_bp, report_date 
            FROM health_metrics 
            WHERE username = ? 
            ORDER BY report_date DESC 
            LIMIT 5
        ''', (username,))
        
        rows = cursor.fetchall()
        
        if not rows:
            return None, None, None

        # Prepare data
        dates = [datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S') for row in rows]
        dates = [date.strftime('%Y-%m-%d') for date in dates]
        dates.reverse()  # Show oldest to newest
        
        pp_glucose = [row[0] for row in rows]
        pp_glucose.reverse()
        
        fasting_glucose = [row[1] for row in rows]
        fasting_glucose.reverse()
        
        systolic = [row[2] for row in rows]
        systolic.reverse()
        
        diastolic = [row[3] for row in rows]
        diastolic.reverse()

        # Create glucose graph
        plt.figure(figsize=(10, 6))
        plt.plot(dates, pp_glucose, 'b-o', label='Post Prandial Glucose')
        plt.plot(dates, fasting_glucose, 'r-o', label='Fasting Glucose')
        plt.title('Glucose Levels Over Time')
        plt.xlabel('Date')
        plt.ylabel('Glucose Level (mg/dL)')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        
        # Save glucose graph to string
        glucose_img = BytesIO()
        plt.savefig(glucose_img, format='png', bbox_inches='tight')
        glucose_img.seek(0)
        glucose_graph = base64.b64encode(glucose_img.getvalue()).decode()
        plt.close()

        # Create blood pressure graph
        plt.figure(figsize=(10, 6))
        plt.plot(dates, systolic, 'g-o', label='Systolic')
        plt.plot(dates, diastolic, 'p-o', label='Diastolic')
        plt.title('Blood Pressure Over Time')
        plt.xlabel('Date')
        plt.ylabel('Blood Pressure (mmHg)')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        
        # Save BP graph to string
        bp_img = BytesIO()
        plt.savefig(bp_img, format='png', bbox_inches='tight')
        bp_img.seek(0)
        bp_graph = base64.b64encode(bp_img.getvalue()).decode()
        plt.close()

        # Create combined metrics graph
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.plot(dates, pp_glucose, 'b-o', label='Post Prandial')
        plt.plot(dates, fasting_glucose, 'r-o', label='Fasting')
        plt.title('Glucose Levels')
        plt.xlabel('Date')
        plt.ylabel('mg/dL')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()

        plt.subplot(1, 2, 2)
        plt.plot(dates, systolic, 'g-o', label='Systolic')
        plt.plot(dates, diastolic, 'p-o', label='Diastolic')
        plt.title('Blood Pressure')
        plt.xlabel('Date')
        plt.ylabel('mmHg')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()

        # Save combined graph to string
        combined_img = BytesIO()
        plt.savefig(combined_img, format='png', bbox_inches='tight')
        combined_img.seek(0)
        combined_graph = base64.b64encode(combined_img.getvalue()).decode()
        plt.close()

        return glucose_graph, bp_graph, combined_graph

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None, None, None
    except Exception as e:
        print(f"Error creating graphs: {e}")
        return None, None, None
    finally:
        if conn:
            conn.close()

def get_latest_metrics(username):
    """Get the latest metrics for display"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT post_prandial_glucose, fasting_glucose, systolic_bp, diastolic_bp, report_date 
            FROM health_metrics 
            WHERE username = ? 
            ORDER BY report_date DESC 
            LIMIT 1
        ''', (username,))
        
        row = cursor.fetchone()
        
        if row:
            return {
                'post_prandial_glucose': row[0],
                'fasting_glucose': row[1],
                'systolic': row[2],
                'diastolic': row[3],
                'date': datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            }
        return None

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Server running at: http://localhost:5008")
    app.run(debug=True, port=5008) 