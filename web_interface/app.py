#!/usr/bin/env python3
"""
Dark Web OSINT Automation Pipeline - Web Interface
A professional workflow orchestration dashboard for security analysts
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import json
import os
import sys
import threading
import time
from pathlib import Path
from collections import OrderedDict
from mock_data import MockDataGenerator, populate_mock_data

# Add parent directory to path to import features
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'darkweb-osint-secret-key-change-in-production'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global storage for results and stats
results_store = {
    'tor_relays': [],
    'onion_domains': [],
    'marketplace_data': [],
    'iocs': {},
    'enriched_data': [],
    'logs': []
}

stats = {
    'total_domains': 0,
    'total_iocs': 0,
    'features_run': 0,
    'pipelines_executed': 0,
    'last_updated': datetime.now().isoformat()
}

# Pipeline workflow definition - organized by stages
PIPELINE_STAGES = OrderedDict([
    ('collection', {
        'name': 'Data Collection',
        'description': 'Gather raw intelligence from dark web sources',
        'features': ['tor-relay', 'onion-crawl', 'market-scrape', 'stix-taxii']
    }),
    ('extraction', {
        'name': 'Data Extraction',
        'description': 'Extract indicators and entities from collected data',
        'features': ['ioc-extract', 'ner', 'hash-extract']
    }),
    ('enrichment', {
        'name': 'Intelligence Enrichment',
        'description': 'Enrich indicators with threat intelligence',
        'features': ['api-enrich', 'infra-map', 'geo-corr']
    }),
    ('analysis', {
        'name': 'Threat Analysis',
        'description': 'Analyze patterns and generate actionable intelligence',
        'features': ['handle-corr', 'behavioral', 'reputation', 'mitre-attack', 'affiliate']
    })
])

# Define all 15 features with metadata and dependencies
FEATURES = {
    'tor-relay': {
        'id': 'tor-relay',
        'name': 'Tor Relay Enumeration',
        'description': 'Discover active Tor network infrastructure',
        'stage': 'collection',
        'depends_on': [],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_1_TOR_RELAY/tor_api.py'
    },
    'onion-crawl': {
        'id': 'onion-crawl',
        'name': 'Onion Domain Discovery',
        'description': 'Recursively crawl and discover hidden services',
        'stage': 'collection',
        'depends_on': [],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_2_ONION_CRAWL/onion_domain_discovery.py'
    },
    'market-scrape': {
        'id': 'market-scrape',
        'name': 'Marketplace Scraping',
        'description': 'Extract listings from dark web markets',
        'stage': 'collection',
        'depends_on': [],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_3_MARKET_SCRAPE/marketplace_scraper.py'
    },
    'stix-taxii': {
        'id': 'stix-taxii',
        'name': 'STIX/TAXII Feeds',
        'description': 'Parse structured threat intelligence feeds',
        'stage': 'collection',
        'depends_on': [],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_5_STIX_TAXII/stix_parser.py'
    },
    'ioc-extract': {
        'id': 'ioc-extract',
        'name': 'IOC Extraction',
        'description': 'Extract indicators from collected data',
        'stage': 'extraction',
        'depends_on': ['onion-crawl', 'market-scrape'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_6_IOC_EXTRACT/ioc_extractor.py'
    },
    'ner': {
        'id': 'ner',
        'name': 'Named Entity Recognition',
        'description': 'Identify entities with NLP',
        'stage': 'extraction',
        'depends_on': ['market-scrape'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_7_NER/ner_extractor.py'
    },
    'hash-extract': {
        'id': 'hash-extract',
        'name': 'Hash Extraction',
        'description': 'Detect and analyze malware hashes',
        'stage': 'extraction',
        'depends_on': ['market-scrape'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_8_HASH_EXTRACT/hash_extractor.py'
    },
    'api-enrich': {
        'id': 'api-enrich',
        'name': 'API Enrichment',
        'description': 'Enrich IOCs with threat intelligence APIs',
        'stage': 'enrichment',
        'depends_on': ['ioc-extract'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_4_API_ENRICH/api_enrichment.py'
    },
    'infra-map': {
        'id': 'infra-map',
        'name': 'Infrastructure Mapping',
        'description': 'Map C2 servers and hosting infrastructure',
        'stage': 'enrichment',
        'depends_on': ['ioc-extract'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_9_INFRA_MAP/infra_mapper.py'
    },
    'geo-corr': {
        'id': 'geo-corr',
        'name': 'Geolocation Correlation',
        'description': 'Correlate IP geolocation data',
        'stage': 'enrichment',
        'depends_on': ['api-enrich'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_10_GEO_CORR/geo_correlator.py'
    },
    'handle-corr': {
        'id': 'handle-corr',
        'name': 'Handle Correlation',
        'description': 'Track threat actor handles across platforms',
        'stage': 'analysis',
        'depends_on': ['ner'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_11_HANDLE_CORR/handle_correlator.py'
    },
    'behavioral': {
        'id': 'behavioral',
        'name': 'Behavioral Analysis',
        'description': 'Analyze vendor behavior patterns',
        'stage': 'analysis',
        'depends_on': ['market-scrape'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_12_BEHAVIORAL_ANALYSIS/behavioral_analyzer.py'
    },
    'reputation': {
        'id': 'reputation',
        'name': 'Reputation Scoring',
        'description': 'Calculate vendor reputation scores',
        'stage': 'analysis',
        'depends_on': ['behavioral'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_13_REPUTATION_SCORING/reputation_scorer.py'
    },
    'mitre-attack': {
        'id': 'mitre-attack',
        'name': 'MITRE ATT&CK Mapping',
        'description': 'Map observed behaviors to MITRE framework',
        'stage': 'analysis',
        'depends_on': ['ioc-extract', 'behavioral'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_14_MITRE_ATTACK/mitre_mapper.py'
    },
    'affiliate': {
        'id': 'affiliate',
        'name': 'Affiliate Analysis',
        'description': 'Detect RaaS affiliate structures',
        'stage': 'analysis',
        'depends_on': ['market-scrape', 'handle-corr'],
        'status': 'idle',
        'last_run': None,
        'script': 'FEAT_15_AFFILIATE_ANALYSIS/affiliate_analyzer.py'
    }
}

# Current pipeline execution state
pipeline_state = {
    'running': False,
    'current_stage': None,
    'current_feature': None,
    'progress': 0,
    'start_time': None
}

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard - workflow view"""
    return render_template('dashboard.html',
                         stats=stats,
                         stages=PIPELINE_STAGES,
                         pipeline_state=pipeline_state)

@app.route('/pipeline')
def pipeline():
    """Pipeline orchestration page"""
    return render_template('pipeline.html',
                         stages=PIPELINE_STAGES,
                         features=FEATURES,
                         pipeline_state=pipeline_state)

@app.route('/results')
def results():
    """Results viewer page"""
    return render_template('results.html', results=results_store)

@app.route('/logs')
def logs():
    """Live logs viewer page"""
    return render_template('logs.html')

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get current statistics"""
    stats['last_updated'] = datetime.now().isoformat()
    return jsonify(stats)

@app.route('/api/pipeline/status', methods=['GET'])
def get_pipeline_status():
    """Get pipeline execution status"""
    return jsonify(pipeline_state)

@app.route('/api/pipeline/run', methods=['POST'])
def run_full_pipeline():
    """Run the complete OSINT pipeline"""
    if pipeline_state['running']:
        return jsonify({'error': 'Pipeline already running'}), 400

    data = request.get_json() or {}
    stages_to_run = data.get('stages', list(PIPELINE_STAGES.keys()))

    emit_log('Starting full OSINT pipeline execution', 'info')

    def execute_pipeline():
        pipeline_state['running'] = True
        pipeline_state['start_time'] = datetime.now().isoformat()
        pipeline_state['progress'] = 0

        try:
            total_features = sum(len(PIPELINE_STAGES[stage]['features'])
                               for stage in stages_to_run)
            completed = 0

            for stage_id in stages_to_run:
                stage = PIPELINE_STAGES[stage_id]
                pipeline_state['current_stage'] = stage_id

                emit_log(f"STAGE: {stage['name']}", 'info')
                socketio.emit('pipeline_stage_start', {'stage': stage_id, 'name': stage['name']})

                for feature_id in stage['features']:
                    feature = FEATURES[feature_id]
                    pipeline_state['current_feature'] = feature_id

                    # Check dependencies
                    deps_met = check_dependencies(feature_id)
                    if not deps_met:
                        emit_log(f"Skipping {feature['name']} - dependencies not met", 'warning')
                        completed += 1
                        pipeline_state['progress'] = int((completed / total_features) * 100)
                        continue

                    # Execute feature
                    success = execute_feature(feature_id)

                    completed += 1
                    pipeline_state['progress'] = int((completed / total_features) * 100)
                    socketio.emit('pipeline_progress', {'progress': pipeline_state['progress']})

                    # Small delay between features
                    time.sleep(2)

                emit_log(f"Completed stage: {stage['name']}", 'success')

            stats['pipelines_executed'] += 1
            emit_log('Pipeline execution completed', 'success')

        except Exception as e:
            emit_log(f'Pipeline error: {str(e)}', 'error')
        finally:
            pipeline_state['running'] = False
            pipeline_state['current_stage'] = None
            pipeline_state['current_feature'] = None
            socketio.emit('pipeline_complete', {'stats': stats})

    thread = threading.Thread(target=execute_pipeline)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'pipeline_state': pipeline_state})

@app.route('/api/pipeline/stage/<stage_id>/run', methods=['POST'])
def run_pipeline_stage(stage_id):
    """Run a specific pipeline stage"""
    if stage_id not in PIPELINE_STAGES:
        return jsonify({'error': 'Invalid stage'}), 404

    if pipeline_state['running']:
        return jsonify({'error': 'Pipeline already running'}), 400

    stage = PIPELINE_STAGES[stage_id]
    emit_log(f"Starting stage: {stage['name']}", 'info')

    def execute_stage():
        pipeline_state['running'] = True
        pipeline_state['current_stage'] = stage_id

        try:
            for feature_id in stage['features']:
                pipeline_state['current_feature'] = feature_id
                execute_feature(feature_id)
                time.sleep(1)

            emit_log(f"Stage completed: {stage['name']}", 'success')
        finally:
            pipeline_state['running'] = False
            pipeline_state['current_stage'] = None
            pipeline_state['current_feature'] = None

    thread = threading.Thread(target=execute_stage)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'stage': stage_id})

@app.route('/api/features/<feature_id>/run', methods=['POST'])
def run_feature(feature_id):
    """Run a specific feature"""
    if feature_id not in FEATURES:
        return jsonify({'error': 'Feature not found'}), 404

    feature = FEATURES[feature_id]
    emit_log(f"Starting: {feature['name']}", 'info')

    def run_in_background():
        execute_feature(feature_id)

    thread = threading.Thread(target=run_in_background)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'feature': feature})

@app.route('/api/results/<result_type>', methods=['GET'])
def get_results(result_type):
    """Get specific result type"""
    if result_type in results_store:
        return jsonify(results_store[result_type])
    return jsonify({'error': 'Invalid result type'}), 404

@app.route('/api/webhook/<feature_id>', methods=['POST'])
def webhook_receiver(feature_id):
    """Receive webhook data from features"""
    try:
        data = request.get_json()

        # Store results based on feature type
        if feature_id == 'tor-relay':
            results_store['tor_relays'] = data
        elif feature_id == 'onion-crawl':
            results_store['onion_domains'] = data
            stats['total_domains'] = len(data.get('domains', []))
        elif feature_id == 'market-scrape':
            results_store['marketplace_data'] = data
        elif feature_id == 'ioc-extract':
            results_store['iocs'] = data
            stats['total_iocs'] = data.get('total_iocs', 0)
        elif feature_id == 'api-enrich':
            results_store['enriched_data'] = data

        socketio.emit('new_results', {
            'feature': feature_id,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })

        emit_log(f"Received data from {feature_id}", 'info')
        return jsonify({'status': 'received'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mock/populate', methods=['POST'])
def populate_mock():
    """Populate results with mock data for testing"""
    try:
        mock_data = populate_mock_data()

        # Populate results store
        results_store['onion_domains'] = mock_data['onion_domains']
        results_store['marketplace_data'] = mock_data['marketplace_data']
        results_store['iocs'] = mock_data['iocs']
        results_store['enriched_data'] = mock_data['enriched_data']
        results_store['logs'] = mock_data['logs']

        # Update stats
        stats['total_domains'] = len(mock_data['onion_domains']['domains'])
        stats['total_iocs'] = mock_data['iocs']['total_iocs']
        stats['features_run'] = 15
        stats['pipelines_executed'] = 1

        emit_log('Mock data populated successfully', 'success')

        return jsonify({
            'status': 'success',
            'message': 'Mock data populated',
            'stats': stats
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_dependencies(feature_id):
    """Check if feature dependencies are met"""
    feature = FEATURES[feature_id]

    if not feature['depends_on']:
        return True

    for dep_id in feature['depends_on']:
        dep_feature = FEATURES[dep_id]
        if dep_feature['status'] != 'completed':
            return False

    return True

def execute_feature(feature_id):
    """Execute a single feature"""
    feature = FEATURES[feature_id]

    try:
        feature['status'] = 'running'
        feature['last_run'] = datetime.now().isoformat()

        emit_log(f"Executing: {feature['name']}", 'info')
        socketio.emit('feature_update', {'feature': feature})

        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            feature['script']
        )

        if os.path.exists(script_path):
            import subprocess
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                feature['status'] = 'completed'
                stats['features_run'] += 1
                emit_log(f"Completed: {feature['name']}", 'success')
                socketio.emit('feature_update', {'feature': feature})
                return True
            else:
                feature['status'] = 'failed'
                emit_log(f"Failed: {feature['name']} - {result.stderr[:200]}", 'error')
                socketio.emit('feature_update', {'feature': feature})
                return False
        else:
            feature['status'] = 'failed'
            emit_log(f"Script not found: {script_path}", 'error')
            return False

    except Exception as e:
        feature['status'] = 'failed'
        emit_log(f"Error in {feature['name']}: {str(e)}", 'error')
        return False

def emit_log(message, level='info'):
    """Emit log message to connected clients"""
    log_entry = {
        'message': message,
        'level': level,
        'timestamp': datetime.now().isoformat()
    }
    results_store['logs'].append(log_entry)

    if len(results_store['logs']) > 1000:
        results_store['logs'] = results_store['logs'][-1000:]

    socketio.emit('log_message', log_entry)

# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    emit_log('Client connected', 'info')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print('Client disconnected')

@socketio.on('request_logs')
def handle_request_logs():
    """Send recent logs to client"""
    emit('recent_logs', results_store['logs'][-100:])

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║         Dark Web OSINT Automation Pipeline                ║
    ║                                                            ║
    ║         Professional Workflow Orchestration               ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝

    Dashboard running at: http://localhost:8080

    Pipeline Stages:
    → Data Collection (4 features)
    → Data Extraction (3 features)
    → Intelligence Enrichment (3 features)
    → Threat Analysis (5 features)

    Press Ctrl+C to stop
    """)

    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
