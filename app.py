from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# Path to existing patient_data.db in asep folder
HOME = os.path.expanduser('~')
DESKTOP = os.path.join(HOME, 'Desktop')
ASEP_DIR = os.path.join(DESKTOP, 'asep')
DB_PATH = os.path.join(ASEP_DIR, 'patient_data.db')

def verify_database():
    """Create tables if they don't exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create personal_details table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            emergency_contact TEXT,
            blood_group TEXT,
            type_of_diabetes TEXT,
            date_of_diagnosis TEXT,
            family_history_diabetes TEXT,
            known_allergies TEXT,
            current_medications TEXT,
            family_medical_history TEXT,
            other_medical_conditions TEXT,
            weight REAL,
            height REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create health_metrics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            post_prandial_glucose REAL,
            fasting_glucose REAL,
            hba1c REAL,
            systolic_bp INTEGER,
            diastolic_bp INTEGER,
            hdl_cholesterol REAL,
            ldl_cholesterol REAL,
            triglycerides REAL,
            urine_glucose TEXT,
            urine_ketones TEXT,
            urine_protein TEXT,
            report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES personal_details (id)
        )
        """)

        # Create lifestyle_goals table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lifestyle_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            physical_activity_level TEXT,
            exercise_routine TEXT,
            average_sleep_hours INTEGER,
            diet_preferences TEXT,
            target_blood_sugar_min INTEGER,
            target_blood_sugar_max INTEGER,
            weight_goals REAL,
            weekly_activity_goal TEXT,
            additional_health_goals TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES personal_details (id)
        )
        """)

        conn.commit()
        conn.close()
        print("Database tables created successfully")
        
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        raise e

@app.route('/')
def index():
    verify_database()  # Ensure database exists
    return render_template('personal_details.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.form
        print("\n=== FORM DATA RECEIVED ===")
        for key, value in data.items():
            print(f"{key}: {value}")
        print("========================\n")
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert personal details
        personal_details_query = '''
        INSERT INTO personal_details (
            full_name, age, gender, email, phone, address,
            emergency_contact, blood_group, type_of_diabetes,
            date_of_diagnosis, family_history_diabetes, known_allergies,
            current_medications, family_medical_history,
            other_medical_conditions, weight, height
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        personal_details_data = (
            data.get('full_name', '').strip(),
            data.get('age', '').strip(),
            data.get('gender', '').strip(),
            data.get('email', '').strip(),
            data.get('phone', '').strip(),
            data.get('address', '').strip(),
            data.get('emergency_contact', '').strip(),
            data.get('blood_group', '').strip(),
            data.get('type_of_diabetes', '').strip(),
            data.get('date_of_diagnosis', '').strip(),
            data.get('family_history_diabetes', '').strip(),
            data.get('known_allergies', '').strip(),
            data.get('current_medications', '').strip(),
            data.get('family_medical_history', '').strip(),
            data.get('other_medical_conditions', '').strip(),
            float(data.get('weight')) if data.get('weight') and data.get('weight').strip() else None,
            float(data.get('height')) if data.get('height') and data.get('height').strip() else None
        )
        
        print("\n=== PERSONAL DETAILS DATA ===")
        print("Query:", personal_details_query)
        print("Data:", personal_details_data)
        print("===========================\n")
        
        cursor.execute(personal_details_query, personal_details_data)
        patient_id = cursor.lastrowid
        print(f"Generated patient_id: {patient_id}")

        # Insert health metrics
        health_query = '''
        INSERT INTO health_metrics (
            patient_id,
            post_prandial_glucose,
            fasting_glucose,
            hba1c,
            systolic_bp,
            diastolic_bp,
            hdl_cholesterol,
            ldl_cholesterol,
            triglycerides,
            urine_glucose,
            urine_ketones,
            urine_protein
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        health_data = (
            patient_id,
            float(data.get('post_prandial_glucose')) if data.get('post_prandial_glucose') and data.get('post_prandial_glucose').strip() else None,
            float(data.get('fasting_glucose')) if data.get('fasting_glucose') and data.get('fasting_glucose').strip() else None,
            float(data.get('hba1c')) if data.get('hba1c') and data.get('hba1c').strip() else None,
            int(data.get('systolic_bp')) if data.get('systolic_bp') and data.get('systolic_bp').strip() else None,
            int(data.get('diastolic_bp')) if data.get('diastolic_bp') and data.get('diastolic_bp').strip() else None,
            float(data.get('hdl_cholesterol')) if data.get('hdl_cholesterol') and data.get('hdl_cholesterol').strip() else None,
            float(data.get('ldl_cholesterol')) if data.get('ldl_cholesterol') and data.get('ldl_cholesterol').strip() else None,
            float(data.get('triglycerides')) if data.get('triglycerides') and data.get('triglycerides').strip() else None,
            data.get('urine_glucose', '').strip(),
            data.get('urine_ketones', '').strip(),
            data.get('urine_protein', '').strip()
        )
        
        print("\n=== HEALTH METRICS DATA ===")
        print("Query:", health_query)
        print("Data:", health_data)
        print("=========================\n")
        
        cursor.execute(health_query, health_data)

        # Insert lifestyle goals
        lifestyle_query = '''
        INSERT INTO lifestyle_goals (
            patient_id,
            physical_activity_level,
            exercise_routine,
            average_sleep_hours,
            diet_preferences,
            target_blood_sugar_min,
            target_blood_sugar_max,
            weight_goals,
            weekly_activity_goal,
            additional_health_goals
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        lifestyle_data = (
            patient_id,
            data.get('physical_activity_level', '').strip(),
            data.get('exercise_routine', '').strip(),
            int(data.get('average_sleep_hours')) if data.get('average_sleep_hours') and data.get('average_sleep_hours').strip() else None,
            data.get('diet_preferences', '').strip(),
            float(data.get('target_blood_sugar_min')) if data.get('target_blood_sugar_min') and data.get('target_blood_sugar_min').strip() else None,
            float(data.get('target_blood_sugar_max')) if data.get('target_blood_sugar_max') and data.get('target_blood_sugar_max').strip() else None,
            float(data.get('weight_goals')) if data.get('weight_goals') and data.get('weight_goals').strip() else None,
            data.get('weekly_activity_goal', '').strip(),
            data.get('additional_health_goals', '').strip()
        )
        
        print("\n=== LIFESTYLE GOALS DATA ===")
        print("Query:", lifestyle_query)
        print("Data:", lifestyle_data)
        print("==========================\n")
        
        cursor.execute(lifestyle_query, lifestyle_data)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Data saved successfully!'
        })
        
    except Exception as e:
        print(f"\nERROR SAVING DATA: {str(e)}")
        print("Error details:", e.__class__.__name__)
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Error saving data: {str(e)}'
        }), 500

@app.route('/view_data')
def view_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM personal_details')
        data = cursor.fetchall()
        conn.close()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    verify_database()  # Create tables on startup
    app.run(debug=True, port=4001)