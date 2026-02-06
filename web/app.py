import os
import sys
import json
import glob
import subprocess
import threading
import time
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import settings as config
except ImportError:
    import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'darkweb-osint-secret-v2'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# State Tracking
PIPELINE_STATUS = {
    "running": False,
    "stage": "Idle",
    "logs": []
}

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def status():
    return jsonify(PIPELINE_STATUS)

@app.route('/api/data/<category>')
def get_data(category):
    """
    Unified API to fetch data from the file system.
    categories: raw, normalized, enriched, intelligence
    """
    base_path = os.path.join(config.DATA_DIR, category)
    if not os.path.exists(base_path):
        return jsonify({"error": "Category not found", "data": []})

    files = glob.glob(os.path.join(base_path, "*.json"))
    # Sort by modification time (newest first)
    files.sort(key=os.path.getmtime, reverse=True)
    
    results = []
    # Limit to top 20 recent files to prevent browser crash
    for f in files[:20]:
        with open(f, 'r') as file_handle:
            try:
                content = json.load(file_handle)
                results.append({
                    "filename": os.path.basename(f),
                    "content": content
                })
            except:
                pass
    
    return jsonify({"category": category, "count": len(results), "data": results})

@app.route('/api/run', methods=['POST'])
def run_pipeline():
    if PIPELINE_STATUS["running"]:
        return jsonify({"status": "error", "message": "Pipeline already running"})
    
    # Start the pipeline in a background thread
    thread = threading.Thread(target=execute_pipeline_script)
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "success", "message": "Pipeline started"})

# --- WORKER ---

def execute_pipeline_script():
    global PIPELINE_STATUS
    PIPELINE_STATUS["running"] = True
    PIPELINE_STATUS["stage"] = "Initializing..."
    PIPELINE_STATUS["logs"] = []

    script_path = os.path.join(config.BASE_DIR, "orchestration", "run_pipeline.py")
    
    process = subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Stream logs
    for line in iter(process.stdout.readline, ''):
        log_entry = line.strip()
        if log_entry:
            # Simple heuristic to update stage based on logs
            if "Starting Stage:" in log_entry:
                PIPELINE_STATUS["stage"] = log_entry.split("Starting Stage:")[-1].strip()
            
            PIPELINE_STATUS["logs"].append(log_entry)
            socketio.emit('log_update', {'log': log_entry})
            
            # Keep log buffer manageable
            if len(PIPELINE_STATUS["logs"]) > 500:
                PIPELINE_STATUS["logs"].pop(0)

    process.wait()
    PIPELINE_STATUS["running"] = False
    PIPELINE_STATUS["stage"] = "Completed"
    socketio.emit('status_update', {"status": "completed"})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
