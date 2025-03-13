from flask import Flask, render_template_string
import sqlite3
import os

app = Flask(__name__)

# Configure paths
HOME = os.path.expanduser('~')
DESKTOP = os.path.join(HOME, 'Desktop')
ASEP_DIR = os.path.join(DESKTOP, 'asep')
DB_PATH = os.path.join(ASEP_DIR, 'patient_data.db')

@app.route('/')
def view_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get data from all tables with better NULL handling
        cursor.execute("""
        SELECT 
            p.id,
            COALESCE(p.full_name, '') as full_name,
            COALESCE(p.age, '') as age,
            COALESCE(p.gender, '') as gender,
            COALESCE(p.email, '') as email,
            COALESCE(p.phone, '') as phone,
            COALESCE(p.address, '') as address,
            COALESCE(p.emergency_contact, '') as emergency_contact,
            COALESCE(p.blood_group, '') as blood_group,
            COALESCE(p.type_of_diabetes, '') as type_of_diabetes,
            COALESCE(p.date_of_diagnosis, '') as date_of_diagnosis,
            COALESCE(p.family_history_diabetes, '') as family_history_diabetes,
            COALESCE(p.known_allergies, '') as known_allergies,
            COALESCE(p.current_medications, '') as current_medications,
            COALESCE(p.family_medical_history, '') as family_medical_history,
            COALESCE(p.other_medical_conditions, '') as other_medical_conditions,
            COALESCE(p.weight, '') as weight,
            COALESCE(p.height, '') as height,
            datetime(p.date) as registration_date,
            COALESCE(h.post_prandial_glucose, '') as post_prandial_glucose,
            COALESCE(h.fasting_glucose, '') as fasting_glucose,
            COALESCE(h.hba1c, '') as hba1c,
            COALESCE(h.systolic_bp, '') as systolic_bp,
            COALESCE(h.diastolic_bp, '') as diastolic_bp,
            COALESCE(h.hdl_cholesterol, '') as hdl_cholesterol,
            COALESCE(h.ldl_cholesterol, '') as ldl_cholesterol,
            COALESCE(h.triglycerides, '') as triglycerides,
            COALESCE(h.urine_glucose, '') as urine_glucose,
            COALESCE(h.urine_ketones, '') as urine_ketones,
            COALESCE(h.urine_protein, '') as urine_protein,
            datetime(h.report_date) as report_date,
            COALESCE(l.physical_activity_level, '') as physical_activity_level,
            COALESCE(l.exercise_routine, '') as exercise_routine,
            COALESCE(l.average_sleep_hours, '') as average_sleep_hours,
            COALESCE(l.diet_preferences, '') as diet_preferences,
            COALESCE(l.target_blood_sugar_min, '') as target_blood_sugar_min,
            COALESCE(l.target_blood_sugar_max, '') as target_blood_sugar_max,
            COALESCE(l.weight_goals, '') as weight_goals,
            COALESCE(l.weekly_activity_goal, '') as weekly_activity_goal,
            COALESCE(l.additional_health_goals, '') as additional_health_goals,
            datetime(l.date) as lifestyle_date
        FROM personal_details p
        LEFT JOIN health_metrics h ON p.id = h.patient_id
        LEFT JOIN lifestyle_goals l ON p.id = l.patient_id
        ORDER BY p.id DESC, h.report_date DESC
        """)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Get all rows
        rows = cursor.fetchall()
        
        conn.close()
        
        # HTML template with modern styling
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Patient Health Records</title>
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #e6f3ff 0%, #e6fff7 100%);
                }
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #1a91ff;
                    text-align: center;
                    margin-bottom: 30px;
                }
                .table-container {
                    overflow-x: auto;
                    margin-bottom: 40px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                    background: white;
                }
                th {
                    background: #1a91ff;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    position: sticky;
                    top: 0;
                    white-space: nowrap;
                    font-size: 0.9em;
                }
                td {
                    padding: 12px;
                    border-bottom: 1px solid #e0e0e0;
                    font-size: 0.9em;
                }
                tr:nth-child(even) {
                    background: #f8f9fa;
                }
                tr:hover {
                    background: #f0f7ff;
                }
                .section {
                    margin-bottom: 30px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 5px;
                }
                .section h2 {
                    color: #1a91ff;
                    margin-top: 0;
                }
                .refresh-button {
                    display: block;
                    margin: 20px auto;
                    padding: 10px 20px;
                    background: #1a91ff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }
                .refresh-button:hover {
                    background: #0055b3;
                }
                .column-group {
                    border-right: 2px solid #1a91ff;
                }
                .empty-cell {
                    color: #999;
                    font-style: italic;
                }
                .goals-cell {
                    white-space: pre-wrap;
                    max-width: 200px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Patient Health Records</h1>
                <button class="refresh-button" onclick="location.reload()">Refresh Data</button>
                
                {% if rows %}
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th colspan="19" class="column-group">Personal Details</th>
                                    <th colspan="12" class="column-group">Health Metrics</th>
                                    <th colspan="10">Lifestyle & Goals</th>
                                </tr>
                                <tr>
                                    {% for column in columns %}
                                        <th>{{ column.replace('_', ' ').title() }}</th>
                                    {% endfor %}
                                </tr>
                            </thead>
                            <tbody>
                                {% for row in rows %}
                                    <tr>
                                        {% for value in row %}
                                            <td {% if not value %}class="empty-cell"{% endif %}
                                                {% if loop.index0 in [38, 39] %}class="goals-cell"{% endif %}>
                                                {{ value if value else 'Not provided' }}
                                            </td>
                                        {% endfor %}
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="section">
                        <h2>No Data Found</h2>
                        <p>No records found in the database.</p>
                    </div>
                {% endif %}
            </div>
        </body>
        </html>
        """
        
        return render_template_string(html_template, columns=columns, rows=rows)
        
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    print(f"Database path: {DB_PATH}")
    app.run(debug=True, port=5007) 