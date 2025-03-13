from flask import Flask, render_template_string, jsonify, redirect
import google.generativeai as genai
import pandas as pd
import os
import re
import sqlite3

app = Flask(__name__)

# Configure Gemini API using your API key (for testing only; use environment variables in production)
gemini_api_key = "AIzaSyC9NwVA01MVc2_zqEZpWLfeoAs_nIR_66M"
genai.configure(api_key=gemini_api_key)

# Define Gemini generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the Gemini model instance
model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

# Configure paths
HOME = os.path.expanduser('~')
DESKTOP = os.path.join(HOME, 'Desktop')
ASEP_DIR = os.path.join(DESKTOP, 'asep')
DB_PATH = os.path.join(ASEP_DIR, 'patient_data.db')

def get_latest_data():
    """Read the latest entry from all tables in SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get the latest entry from all tables with existing columns
        cursor.execute("""
            SELECT 
                pd.full_name,
                pd.age,
                pd.gender,
                pd.blood_group,
                pd.type_of_diabetes,
                pd.date_of_diagnosis,
                pd.family_history_diabetes,
                pd.known_allergies,
                pd.current_medications,
                pd.family_medical_history,
                pd.other_medical_conditions,
                pd.weight,
                pd.height,
                hm.post_prandial_glucose,
                hm.fasting_glucose,
                hm.hba1c,
                hm.systolic_bp,
                hm.diastolic_bp,
                hm.hdl_cholesterol,
                hm.ldl_cholesterol,
                hm.triglycerides,
                hm.urine_glucose,
                hm.urine_ketones,
                hm.urine_protein,
                lg.physical_activity_level,
                lg.exercise_routine,
                lg.average_sleep_hours,
                lg.diet_preferences,
                lg.target_blood_sugar_min,
                lg.target_blood_sugar_max,
                lg.weight_goals,
                lg.weekly_activity_goal,
                lg.additional_health_goals
            FROM personal_details pd
            LEFT JOIN health_metrics hm ON pd.id = hm.patient_id
            LEFT JOIN lifestyle_goals lg ON pd.id = lg.patient_id
            ORDER BY pd.id DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            raise Exception("No data found in the database. Please add your details first.")
        
        latest_personal = {
            'Full Name': row[0] or 'N/A',
            'Age': row[1] or 'N/A',
            'Gender': row[2] or 'N/A',
            'Blood Group': row[3] or 'N/A',
            'Type of Diabetes': row[4] or 'N/A',
            'Date of Diagnosis': row[5] or 'N/A',
            'Family History of Diabetes': row[6] or 'None',
            'Known Allergies': row[7] or 'None',
            'Current Medications': row[8] or 'None',
            'Family Medical History': row[9] or 'None',
            'Other Medical Conditions': row[10] or 'None'
        }
        
        # Get health metrics from the database
        latest_health = {
            'Weight (kg)': row[11] or '70',  # Default weight if null
            'Height (cm)': row[12] or '170',  # Default height if null
            'BMI': calculate_bmi(row[11], row[12]) if row[11] and row[12] else '23',  # Calculate BMI or use default
            'Post Prandial Glucose': f"{row[13] or 'N/A'} mg/dL",
            'Fasting Glucose': f"{row[14] or 'N/A'} mg/dL",
            'HbA1c': f"{row[15] or 'N/A'}%",
            'Blood Pressure': f"{row[16] or '120'}/{row[17] or '80'} mmHg",
            'HDL Cholesterol': row[18] or 'N/A',
            'LDL Cholesterol': row[19] or 'N/A',
            'Triglycerides': row[20] or 'N/A',
            'Urine Glucose': row[21] or 'N/A',
            'Urine Ketones': row[22] or 'N/A',
            'Urine Protein': row[23] or 'N/A'
        }
        
        latest_lifestyle = {
            'Activity Level': row[24] or 'Moderate',
            'Exercise Routine': row[25] or 'N/A',
            'Average Sleep Hours': row[26] or '8',
            'Diet Preferences': row[27] or 'Balanced',
            'Target Blood Sugar Range': f"{row[28] or '80'}-{row[29] or '130'} mg/dL",
            'Weight Goal': row[30] or latest_health['Weight (kg)'],
            'Weekly Activity Goal': row[31] or '0 hours',
            'Additional Health Goals': row[32] or 'None'
        }
        
        conn.close()
        return latest_personal, latest_health, latest_lifestyle
        
    except Exception as e:
        print(f"Error reading data: {str(e)}")
        raise e

def calculate_bmi(weight, height):
    """Calculate BMI from weight (kg) and height (cm)."""
    if not weight or not height:
        return '23'  # Default BMI
    try:
        height_m = float(height) / 100  # Convert cm to m
        bmi = float(weight) / (height_m * height_m)
        return f"{bmi:.1f}"
    except:
        return '23'  # Default BMI if calculation fails

def convert_markdown_to_html(text):
    """Convert markdown-like syntax from Gemini's response to HTML."""
    text = re.sub(r'\*\*(.*?)\*\*', r'<h3 class="heading">\1</h3>', text)
    lines = text.splitlines()
    html_lines = []
    in_list = False
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('•'):
            if not in_list:
                html_lines.append("<ul class='bullet-list'>")
                in_list = True
            content = stripped_line.lstrip('•').strip()
            html_lines.append(f'<li>{content}</li>')
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if stripped_line:
                html_lines.append(f'<p>{stripped_line}</p>')
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)

# Updated HTML template with modern UI design
index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SmartDiaTrack - Home</title>
  <!-- Google Fonts and Font Awesome -->
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
  <style>
    :root {
      --primary-color: #1a91ff;
      --secondary-color: #0055b3;
      --accent-color: #00d1ff;
      --medical-blue: #0077cc;
      --light-blue: #e6f3ff;
      --success-green: #00b894;
      --light-green: #e6fff7;
    }

    body {
      font-family: 'Poppins', sans-serif;
      margin: 0;
      background: linear-gradient(135deg, var(--light-blue) 0%, var(--light-green) 100%);
      min-height: 100vh;
      color: #1f2937;
    }

    /* Header Styles */
    header {
      background-color: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      position: fixed;
      width: 100%;
      top: 0;
      z-index: 1000;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      height: 90px;
      display: flex;
      align-items: center;
    }

    nav {
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .logo-text {
      font-weight: 700;
      font-size: 1.8rem;
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .nav-links {
      display: flex;
      gap: 2rem;
      align-items: center;
      height: 100%;
    }

    .nav-links > a,
    .nav-links > .nav-dropdown {
      display: flex;
      align-items: center;
    }

    .nav-links a {
      color: var(--medical-blue);
      text-decoration: none;
      font-weight: 500;
      transition: all 0.3s ease;
      padding: 0.5rem 1rem;
      border-radius: 8px;
    }

    .nav-links a:hover {
      background: var(--light-blue);
      color: var(--primary-color);
    }

    /* Main Layout */
    .main-container {
      display: flex;
      padding-top: 90px;
      min-height: calc(100vh - 90px);
    }

    /* Side Menu */
    .side-menu {
      width: 280px;
      background: rgba(255, 255, 255, 0.95);
      padding: 2rem;
      height: calc(100vh - 90px);
      position: fixed;
      left: 0;
      box-shadow: 2px 0 10px rgba(0,0,0,0.1);
      padding-bottom: 5rem;
    }

    .menu-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      margin-bottom: 1rem;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.3s ease;
      color: var(--medical-blue);
    }

    .menu-item:hover {
      background: var(--light-blue);
      transform: translateX(5px);
    }

    .menu-item i {
      font-size: 1.2rem;
      width: 24px;
      animation: pulse 2s infinite;
    }

    /* Main Content */
    .content {
      flex: 1;
      margin-left: 280px;
      padding: 3rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
    }

    .welcome-text {
      font-size: 3rem;
      font-weight: 700;
      margin-bottom: 1.5rem;
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: fadeIn 1s ease;
    }

    .subtitle {
      font-size: 1.5rem;
      color: var(--medical-blue);
      opacity: 0.8;
      margin-bottom: 2rem;
      animation: slideUp 1s ease;
    }

    /* Decorative Elements */
    .medical-icon {
      font-size: 5rem;
      color: var(--primary-color);
      opacity: 0.1;
      position: absolute;
      animation: float 3s ease-in-out infinite;
    }

    .medical-icon:nth-child(1) { top: 20%; left: 35%; }
    .medical-icon:nth-child(2) { top: 40%; right: 35%; }
    .medical-icon:nth-child(3) { bottom: 20%; left: 40%; }

    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.1); }
      100% { transform: scale(1); }
    }

    @keyframes float {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-20px); }
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @keyframes slideUp {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 0.8; }
    }

    @media (max-width: 768px) {
      .side-menu {
        transform: translateX(-100%);
        transition: transform 0.3s ease;
      }

      .content {
        margin-left: 0;
        padding: 2rem;
      }

      .welcome-text {
        font-size: 2rem;
      }

      .subtitle {
        font-size: 1.2rem;
      }
    }

    /* Dropdown Styles */
    .dropdown {
      position: relative;
    }

    .dropdown > .menu-item {
      display: flex;
      justify-content: space-between;
    }

    .dropdown > .menu-item i.fa-chevron-down {
      transition: transform 0.3s ease;
    }

    .dropdown.active > .menu-item i.fa-chevron-down {
      transform: rotate(180deg);
    }

    .dropdown-content {
      display: none;
      padding-left: 2.5rem;
      margin-top: 0.2rem;
    }

    .dropdown.active .dropdown-content {
      display: block;
    }

    .dropdown-content .menu-item {
      font-size: 0.95rem;
      padding: 0.6rem 1rem;
    }

    .add-report-btn {
      position: fixed;
      bottom: 2rem;
      left: 1rem;
      width: calc(250px - 2rem);
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      color: white;
      border: none;
      padding: 1rem;
      border-radius: 10px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.8rem;
      font-size: 1rem;
      font-weight: 500;
      transition: all 0.3s ease;
      z-index: 1000;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .add-report-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(26, 145, 255, 0.2);
    }
  </style>
</head>
<body>
  <header>
    <nav>
      <h2 class="logo-text">SmartDiaTrack</h2>
      <div class="nav-links">
        <a href="#" class="active"><i class="fas fa-user"></i> Profile</a>
        <a href="#">About Us</a>
        <div class="nav-dropdown">
          <a href="#">Contact</a>
          <div class="nav-dropdown-content">
            <a href="tel:9529200000">
              <i class="fas fa-phone"></i>
              95292XXXXX
            </a>
            <a href="mailto:smartdiatrack@gmail.com">
              <i class="fas fa-envelope"></i>
              smartdiatrack@gmail.com
            </a>
          </div>
        </div>
        <a href="#" class="logout-link"><i class="fas fa-sign-out-alt"></i> Logout</a>
      </div>
    </nav>
  </header>

  <div class="main-container">
    <aside class="side-menu">
      <div class="menu-item" onclick="showGraph()">
        <i class="fas fa-chart-line"></i>
        <span>Track</span>
      </div>
      <div class="menu-item" onclick="showReminder()">
        <i class="fas fa-bell"></i>
        <span>Reminder</span>
      </div>
      <div class="dropdown">
        <div class="menu-item">
          <div>
            <i class="fas fa-heart"></i>
            <span>Healthcare</span>
          </div>
          <i class="fas fa-chevron-down"></i>
        </div>
        <div class="dropdown-content">
          <div class="menu-item" onclick="getRecommendations('nutrition')">
            <i class="fas fa-apple-alt"></i>
            <span>Nutrition Recommendation</span>
          </div>
          <div class="menu-item" onclick="getRecommendations('exercise')">
            <i class="fas fa-dumbbell"></i>
            <span>Exercise</span>
          </div>
        </div>
      </div>
    </aside>

    <main class="content">
      <h1 class="welcome-text">SmartDiaTrack</h1>
      <p class="subtitle">Your intelligent companion for seamless diabetes management and tracking.</p>
      <div id="recommendations"></div>
      <div id="graph-container" style="display: none; margin-top: 20px;">
        <h2 style="color: #1a91ff; margin-bottom: 20px;">Blood Sugar Measurements</h2>
        <img id="graph-image" style="max-width: 100%; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);" />
      </div>
    </main>
  </div>

  <button class="add-report-btn">
    <i class="fas fa-plus-circle"></i>
    <span>Add Report</span>
  </button>

  <script>
    function getRecommendations(planType) {
      const recommendationsDiv = document.getElementById('recommendations');
      recommendationsDiv.innerHTML = '<p>Loading recommendations...</p>';
      
      fetch('/get_recommendations/' + planType)
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            recommendationsDiv.innerHTML = data.recommendations;
          } else {
            recommendationsDiv.innerHTML = `<p style="color: red;">Error: ${data.message}</p>`;
          }
        })
        .catch(error => {
          recommendationsDiv.innerHTML = `<p style="color: red;">Error: ${error}</p>`;
        });
    }

    function showGraph() {
      window.location.href = 'http://localhost:5008';
    }

    function showReminder() {
      window.location.href = 'http://localhost:5005';
    }

    // Toggle dropdown
    document.querySelectorAll('.dropdown > .menu-item').forEach(item => {
      item.addEventListener('click', () => {
        const parent = item.parentElement;
        parent.classList.toggle('active');
      });
    });
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(index_html)

@app.route('/graph')
def graph():
    """Redirect to the graph visualization page"""
    return redirect('http://localhost:5008')

@app.route('/reminder')
def reminder():
    """Redirect to the reminder page"""
    return redirect('http://localhost:5005')

@app.route('/get_recommendations/<plan_type>')
def get_recommendations(plan_type):
    try:
        # Retrieve the latest patient data
        latest_personal, latest_health, latest_lifestyle = get_latest_data()

        # Build the patient profile string with all available information
        user_profile = f"""
**Patient: {latest_personal['Full Name']}**

Patient Profile for Planning:
• Personal Information:
    - Age: {latest_personal['Age']}
    - Gender: {latest_personal['Gender']}
    - Blood Group: {latest_personal['Blood Group']}
    - Type of Diabetes: {latest_personal['Type of Diabetes']}
    - Diagnosed: {latest_personal['Date of Diagnosis']}
    - Family History of Diabetes: {latest_personal['Family History of Diabetes']}
    - Current Medications: {latest_personal['Current Medications']}
    - Known Allergies: {latest_personal['Known Allergies']}
    - Other Medical Conditions: {latest_personal['Other Medical Conditions']}

• Health Metrics:
    - Height: {latest_health['Height (cm)']} cm
    - Current Weight: {latest_health['Weight (kg)']} kg
    - BMI: {latest_health['BMI']}
    - Blood Sugar Readings:
        * Post Prandial: {latest_health['Post Prandial Glucose']}
        * Fasting: {latest_health['Fasting Glucose']}
        * HbA1c: {latest_health['HbA1c']}
    - Blood Pressure: {latest_health['Blood Pressure']}
    - Cholesterol Profile:
        * HDL: {latest_health['HDL Cholesterol']}
        * LDL: {latest_health['LDL Cholesterol']}
        * Triglycerides: {latest_health['Triglycerides']}
    - Urine Tests:
        * Glucose: {latest_health['Urine Glucose']}
        * Ketones: {latest_health['Urine Ketones']}
        * Protein: {latest_health['Urine Protein']}

• Lifestyle & Goals:
    - Activity Level: {latest_lifestyle['Activity Level']}
    - Current Exercise Routine: {latest_lifestyle['Exercise Routine']}
    - Average Sleep: {latest_lifestyle['Average Sleep Hours']} hours
    - Diet Preferences: {latest_lifestyle['Diet Preferences']}
    - Target Blood Sugar Range: {latest_lifestyle['Target Blood Sugar Range']}
    - Weight Goal: {latest_lifestyle['Weight Goal']} kg
    - Weekly Activity Goal: {latest_lifestyle['Weekly Activity Goal']}
    - Additional Health Goals: {latest_lifestyle['Additional Health Goals']}
        """

        # Define the prompt based on the requested plan type
        if plan_type.lower() == 'nutrition':
            prompt = f"""
Based on this diabetic patient's profile:
{user_profile}

Please create a detailed but concise **Nutrition Plan** that includes:
1. **Daily Caloric Intake Recommendation**
2. **Macro Distribution** (carbohydrates, protein, fat)
3. **Specific Food Recommendations and Meal Ideas**
4. **Meal Timing Suggestions**
5. **Foods to Avoid**
6. **Snack Options for Managing Blood Sugar**
7. **Hydration Recommendations**

Format your response using clear headings, bullet lists, and proper line breaks.
            """
        elif plan_type.lower() == 'exercise':
            prompt = f"""
Based on this diabetic patient's profile:
{user_profile}

Please create a safe and effective **Exercise Plan** that includes:
1. **Types of Recommended Exercises** (cardio and strength training)
2. **Weekly Schedule with Rest Days**
3. **Duration and Intensity Recommendations**
4. **Safety Precautions for Diabetic Patients**
5. **Blood Sugar Monitoring Guidelines During Exercise**
6. **Warning Signs to Watch For**
7. **Progress Tracking Suggestions**
8. **Warm-Up and Cool-Down Routines**

Format your response using clear headings, bullet lists, and proper line breaks.
            """
        else:
            return jsonify({'success': False, 'message': 'Invalid recommendation type.'}), 400

        # Generate recommendations using the Gemini model
        response = model.generate_content(prompt)

        # Convert Gemini's output (with markdown-like syntax) to HTML
        formatted_text = convert_markdown_to_html(response.text)
        
        return jsonify({
            'success': True,
            'recommendations': formatted_text
        })

    except Exception as e:
        print(f"Error generating {plan_type} plan: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)