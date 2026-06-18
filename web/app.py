import eventlet
eventlet.monkey_patch()

import os
import sys
import json
import glob
import subprocess
import time
import secrets
import logging
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

logger = logging.getLogger("WebDashboard")

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
def index():
    return render_template('landing.html')

@app.route('/dashboard')
@require_auth
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/status')
@require_auth
def status():
    status_data = PIPELINE_STATUS.copy()
    status_data["api_keys"] = {
        "virustotal": bool(config.VIRUSTOTAL_API_KEY),
        "abuseipdb": bool(config.ABUSEIPDB_API_KEY),
        "shodan": bool(config.SHODAN_API_KEY)
    }
    return jsonify(status_data)

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
        try:
            with open(f, 'r') as file_handle:
                content = json.load(file_handle)
                results.append({
                    "filename": os.path.basename(f),
                    "content": content
                })
        except json.JSONDecodeError as e:
            logger.warning(f"Skipping malformed JSON file {os.path.basename(f)}: {e}")
        except OSError as e:
            logger.warning(f"Failed to read file {os.path.basename(f)}: {e}")
    
    # Flatten items into flat_data to prevent Alpine nested template lag
    flat_data = []
    for f in results:
        file_data = f["content"].get("data", [])
        if isinstance(file_data, list):
            for item in file_data:
                if isinstance(item, dict):
                    if category == "intelligence":
                        item_copy = item.copy()
                        item_copy["source_file"] = f["filename"]
                        flat_data.append(item_copy)
                    else:
                        item_copy = item.copy()
                        item_copy["source_file"] = item_copy.get("source_file") or item_copy.get("source") or f["filename"]
                        flat_data.append(item_copy)
                elif isinstance(item, str):
                    flat_data.append({
                        "id": item,
                        "type": "raw_string",
                        "source_file": f["filename"]
                    })
    
    # Cap flat_data to 150 items to ensure instant rendering
    flat_data = flat_data[:150]
    
    return jsonify({
        "category": category, 
        "count": len(results), 
        "data": results,
        "flat_data": flat_data
    })

@app.route('/api/run', methods=['POST'])
@require_auth
def run_pipeline():
    if PIPELINE_STATUS["running"]:
        return jsonify({"status": "error", "message": "Pipeline already running"})
    
    # Start the pipeline in a background task
    socketio.start_background_task(execute_pipeline_script)
    
    return jsonify({"status": "success", "message": "Pipeline started"})

# --- WORKER ---

def execute_pipeline_script():
    global PIPELINE_STATUS
    PIPELINE_STATUS["running"] = True
    PIPELINE_STATUS["stage"] = "Initializing..."
    PIPELINE_STATUS["logs"] = []

    script_path = os.path.join(config.BASE_DIR, "orchestration", "run_pipeline.py")
    
    # Verify the pipeline script exists before attempting to run it
    if not os.path.exists(script_path):
        error_msg = f"❌ Pipeline script not found at {script_path}"
        logger.error(error_msg)
        PIPELINE_STATUS["logs"].append(error_msg)
        PIPELINE_STATUS["running"] = False
        PIPELINE_STATUS["stage"] = "Failed"
        socketio.emit('log_update', {'log': error_msg})
        socketio.emit('status_update', {"status": "completed"})
        return

    try:
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
                    socketio.sleep(0.01)  # Yield to eventlet to stream immediately
                    
                    # Keep log buffer manageable
                    if len(PIPELINE_STATUS["logs"]) > 500:
                        PIPELINE_STATUS["logs"].pop(0)

        process.wait()
        
        # Check exit code to detect failures
        if process.returncode != 0:
            error_msg = f"⚠️ Pipeline exited with code {process.returncode}"
            logger.warning(error_msg)
            PIPELINE_STATUS["logs"].append(error_msg)
            PIPELINE_STATUS["stage"] = "Failed"
            socketio.emit('log_update', {'log': error_msg})
        else:
            PIPELINE_STATUS["stage"] = "Completed"

    except FileNotFoundError as e:
        error_msg = f"❌ Failed to start pipeline: Python interpreter not found: {e}"
        logger.error(error_msg)
        PIPELINE_STATUS["logs"].append(error_msg)
        PIPELINE_STATUS["stage"] = "Failed"
        socketio.emit('log_update', {'log': error_msg})
    except Exception as e:
        error_msg = f"❌ Pipeline execution error: {e}"
        logger.error(error_msg, exc_info=True)
        PIPELINE_STATUS["logs"].append(error_msg)
        PIPELINE_STATUS["stage"] = "Failed"
        socketio.emit('log_update', {'log': error_msg})

    PIPELINE_STATUS["running"] = False
    socketio.emit('status_update', {"status": "completed"})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
