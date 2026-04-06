import os
import sys
import json
import glob
import subprocess
import threading
import time
import secrets
from functools import wraps
from flask import Flask, render_template, jsonify, request, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import settings as config
except ImportError:
    import config

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Only allow specific origins in production
ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:8080').split(',')
CORS(app, origins=ALLOWED_ORIGINS)
socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS)

# --- BASIC AUTH ---
# Set via environment: DASHBOARD_USER / DASHBOARD_PASSWORD
# If not set, auth is disabled (local development mode)
DASHBOARD_USER = os.getenv('DASHBOARD_USER')
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD')


def require_auth(f):
    """Basic HTTP auth decorator. Skipped if env vars are not set."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if DASHBOARD_USER and DASHBOARD_PASSWORD:
            auth = request.authorization
            if not auth or auth.username != DASHBOARD_USER or auth.password != DASHBOARD_PASSWORD:
                return Response(
                    'Authentication required.',
                    401,
                    {'WWW-Authenticate': 'Basic realm="BlackSignal Dashboard"'}
                )
        return f(*args, **kwargs)
    return decorated


# Whitelist of valid data categories (prevents path traversal)
VALID_CATEGORIES = {'raw', 'normalized', 'enriched', 'intelligence'}

# State Tracking
PIPELINE_STATUS = {
    "running": False,
    "stage": "Idle",
    "logs": []
}

# --- ROUTES ---

@app.route('/')
@require_auth
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
@require_auth
def status():
    return jsonify(PIPELINE_STATUS)

@app.route('/api/data/<category>')
@require_auth
def get_data(category):
    """
    Unified API to fetch data from the file system.
    categories: raw, normalized, enriched, intelligence
    """
    # Path traversal protection
    if category not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category", "data": []}), 400

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
            except json.JSONDecodeError:
                pass
    
    return jsonify({"category": category, "count": len(results), "data": results})

@app.route('/api/run', methods=['POST'])
@require_auth
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
        [sys.executable, '-u', script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Stream logs
    if process.stdout:
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
