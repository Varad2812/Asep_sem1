from flask import Flask, jsonify, redirect, url_for
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "status": "success",
        "message": "ASEP API is running!",
        "endpoints": {
            "healthcare": "/healthcare",
            "reminder": "/reminder",
            "graph": "/graph"
        }
    })

@app.route('/healthcare')
def healthcare():
    return jsonify({
        "status": "success",
        "message": "Healthcare endpoint"
    })

@app.route('/reminder')
def reminder():
    return jsonify({
        "status": "success",
        "message": "Reminder endpoint"
    })

@app.route('/graph')
def graph():
    return jsonify({
        "status": "success",
        "message": "Graph endpoint"
    })

@app.route('/test-db')
def test_db():
    try:
        db_path = os.environ.get('DATABASE_URL', '/tmp/patient_data.db')
        return jsonify({
            "status": "success",
            "message": "Database configuration loaded",
            "db_path": db_path
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000) 