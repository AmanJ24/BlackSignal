# Dark Web OSINT Automation Pipeline - Web Interface

**Last Updated**: November 6, 2025

A professional, workflow-focused web dashboard for orchestrating and monitoring dark web intelligence gathering operations. Built for security analysts who need automated, dependency-managed execution of 15 OSINT features through a clean, minimalist interface.

---

## Overview

This web interface transforms the Dark Web OSINT tool from 15 independent scripts into a unified, automated pipeline with intelligent workflow orchestration. Security analysts can execute the entire intelligence gathering workflow with a single click, or run specific stages as needed.

### Key Capabilities

- **Automated Pipeline Execution**: One-click execution of all 15 OSINT features in correct dependency order
- **Stage-Based Workflow**: 4-stage pipeline (Collection → Extraction → Enrichment → Analysis)
- **Dependency Management**: Automatic handling of feature dependencies and execution prerequisites
- **Real-Time Monitoring**: Live progress tracking, WebSocket-based log streaming, and execution status
- **Mock Data System**: Realistic simulated data for testing, development, and demonstrations
- **Professional UI/UX**: Clean, minimalist interface designed for analyst workflows

---

## Architecture

### Pipeline Stages

The workflow is organized into 4 sequential stages with automatic dependency resolution:

#### Stage 1: Data Collection
Gather raw intelligence from dark web sources
- Tor Relay Enumeration
- Onion Domain Discovery
- Marketplace Scraping
- STIX/TAXII Feed Parsing

#### Stage 2: Data Extraction
Extract indicators and entities from collected data
- IOC Extraction (depends on: onion-crawl, market-scrape)
- Named Entity Recognition (depends on: market-scrape)
- Hash Extraction (depends on: market-scrape)

#### Stage 3: Intelligence Enrichment
Enrich indicators with threat intelligence
- API Enrichment (depends on: ioc-extract)
- Infrastructure Mapping (depends on: ioc-extract)
- Geolocation Correlation (depends on: api-enrich)

#### Stage 4: Threat Analysis
Generate actionable intelligence
- Handle Correlation (depends on: ner)
- Behavioral Analysis (depends on: market-scrape)
- Reputation Scoring (depends on: behavioral)
- MITRE ATT&CK Mapping (depends on: ioc-extract, behavioral)
- Affiliate Analysis (depends on: market-scrape, handle-corr)

---

## Features

### Workflow Orchestration
- **Full Pipeline Execution**: Run all 15 features sequentially with automatic dependency handling
- **Stage Execution**: Execute specific pipeline stages independently
- **Individual Feature Control**: Manual execution of specific features when needed
- **Progress Tracking**: Real-time progress percentage and stage indicators
- **Execution History**: Track completed pipelines and feature runs

### Data Management
- **Mock Data Generator**: Produces realistic simulated data for testing:
  - 50+ .onion domain addresses
  - 80+ IOCs (IPs, domains, hashes, Bitcoin addresses, emails)
  - 20 marketplace listings with vendors, products, and prices
  - Enriched threat intelligence with geolocation and ASN data
  - 50 realistic log entries
- **Results Storage**: Centralized storage for all pipeline outputs
- **Export Functionality**: Export results as JSON for external analysis

### Monitoring & Visualization
- **Real-Time Logs**: WebSocket-powered live log streaming with color-coded severity levels
- **Statistics Dashboard**: Live metrics for domains discovered, IOCs extracted, and features executed
- **Pipeline Visualization**: Interactive stage diagram showing feature dependencies
- **Execution Status**: Real-time indicators for running, completed, and failed features

### User Interface
- **Dashboard**: Workflow overview with statistics, pipeline controls, and stage execution
- **Pipeline View**: Visual representation of all stages and feature dependencies
- **Results Viewer**: Tabbed interface for different data types with search and export
- **Live Logs**: Terminal-style log viewer with filtering and auto-scroll

---

## Technology Stack

### Backend
- **Flask 3.0.0**: Web framework and API endpoints
- **Flask-SocketIO 5.3.5**: WebSocket support for real-time updates
- **Flask-CORS 4.0.0**: Cross-origin resource sharing
- **Python-SocketIO 5.10.0**: WebSocket client/server implementation

### Frontend
- **Tailwind CSS**: Utility-first CSS framework (CDN)
- **Alpine.js**: Lightweight reactive framework
- **Lucide Icons**: Clean, professional icon set
- **Socket.IO Client**: Real-time bi-directional communication

### Design System
- **Typography**: Inter font family (Google Fonts)
- **Color Palette**: White/light gray backgrounds with subtle blue accents (#0ea5e9)
- **Visual Style**: Minimalist, professional, card-based layouts with smooth transitions
- **Responsive**: Mobile-friendly grid layouts and navigation

---

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

### Setup

1. **Navigate to web interface directory**
   ```bash
   cd darkweb-osint-automater/web_interface
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the server**
   ```bash
   # Using the startup script (Mac/Linux)
   ./start.sh

   # Or manually
   python3 app.py
   ```

4. **Access the interface**
   ```
   http://localhost:8080
   ```

---

## Usage

### Quick Start

1. **Load Mock Data** (for testing)
   - Click "Load Mock Data" button in top navigation
   - Or via API: `curl -X POST http://localhost:8080/api/mock/populate`

2. **Run Full Pipeline**
   - Navigate to Dashboard
   - Click "Run Full Pipeline" button
   - Monitor progress in real-time
   - View results when complete

3. **Run Specific Stage**
   - Navigate to Dashboard or Pipeline page
   - Click "Run This Stage" on desired stage
   - Watch logs for execution details

### Analyst Workflow

**Option 1: Automated Full Execution**
```
Open Dashboard → Click "Run Full Pipeline" → Monitor Progress → View Results
```

**Option 2: Stage-by-Stage Review**
```
Run "Data Collection" → Review collected domains/markets
     ↓
Run "Data Extraction" → Review extracted IOCs
     ↓
Run "Intelligence Enrichment" → Review threat intelligence
     ↓
Run "Threat Analysis" → Get final intelligence report
```

**Option 3: Individual Features** (for debugging/testing)
```
Navigate to Pipeline → Run specific feature manually
```

---

## API Reference

### Pipeline Control

#### Run Full Pipeline
```http
POST /api/pipeline/run
```
Executes all 15 features in dependency order.

**Response:**
```json
{
  "status": "started",
  "pipeline_state": {
    "running": true,
    "current_stage": "collection",
    "progress": 0
  }
}
```

#### Run Specific Stage
```http
POST /api/pipeline/stage/{stage_id}/run
```
Executes all features in a specific stage.

**Parameters:**
- `stage_id`: `collection`, `extraction`, `enrichment`, or `analysis`

#### Get Pipeline Status
```http
GET /api/pipeline/status
```
Returns current pipeline execution state.

### Results

#### Get Statistics
```http
GET /api/stats
```
Returns current statistics (domains, IOCs, features run, pipelines executed).

#### Get Results by Type
```http
GET /api/results/{type}
```
Returns results for specific data type.

**Types:**
- `onion_domains`: Discovered .onion addresses
- `iocs`: Extracted indicators of compromise
- `marketplace_data`: Scraped marketplace listings
- `enriched_data`: API-enriched threat intelligence

### Mock Data

#### Populate Mock Data
```http
POST /api/mock/populate
```
Fills results store with realistic simulated data for testing.

**Response:**
```json
{
  "status": "success",
  "message": "Mock data populated",
  "stats": {
    "total_domains": 50,
    "total_iocs": 80,
    "features_run": 15,
    "pipelines_executed": 1
  }
}
```

### Feature Execution

#### Run Individual Feature
```http
POST /api/features/{feature_id}/run
```
Executes a specific OSINT feature.

**Feature IDs:**
- `tor-relay`, `onion-crawl`, `market-scrape`, `stix-taxii`
- `ioc-extract`, `ner`, `hash-extract`
- `api-enrich`, `infra-map`, `geo-corr`
- `handle-corr`, `behavioral`, `reputation`, `mitre-attack`, `affiliate`

---

## Project Structure

```
web_interface/
├── app.py                      # Flask application and API endpoints
├── mock_data.py               # Realistic data generator for testing
├── requirements.txt           # Python dependencies
├── start.sh                   # Startup script (Mac/Linux)
├── start.bat                  # Startup script (Windows)
├── templates/
│   ├── base.html             # Base template with navigation
│   ├── dashboard.html        # Workflow dashboard with pipeline controls
│   ├── pipeline.html         # Visual pipeline with stage diagram
│   ├── results.html          # Results viewer with export functionality
│   └── logs.html             # Real-time log monitoring
├── static/
│   ├── css/
│   │   └── custom.css        # Custom styling and animations
│   └── js/
│       ├── dashboard.js      # Dashboard utilities and helpers
│       └── logs.js           # Log management and filtering
└── README.md                 # This file
```

---

## Configuration

### Server Settings

Default configuration in `app.py`:
```python
HOST = '0.0.0.0'
PORT = 8080
DEBUG = True
SECRET_KEY = 'darkweb-osint-secret-key-change-in-production'
```

### Changing Port
Edit `app.py` line 591:
```python
socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
```

### Production Deployment
For production use, deploy with a proper WSGI server:

**Using Gunicorn:**
```bash
pip install gunicorn eventlet
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:8080 app:app
```

**Using Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "app.py"]
```

---

## Development

### Adding New Features

1. **Define feature in `app.py`:**
   ```python
   FEATURES['new-feature'] = {
       'id': 'new-feature',
       'name': 'Feature Name',
       'description': 'Feature description',
       'stage': 'collection',  # or extraction, enrichment, analysis
       'depends_on': ['prerequisite-feature'],
       'status': 'idle',
       'script': 'FEAT_XX_NAME/script.py'
   }
   ```

2. **Add to appropriate stage:**
   ```python
   PIPELINE_STAGES['stage_name']['features'].append('new-feature')
   ```

3. **Implement feature script:**
   - Create feature directory: `FEAT_XX_NAME/`
   - Add Python script with main execution logic
   - Send results to webhook: `POST /api/webhook/new-feature`

### Mock Data Generation

Extend `mock_data.py` to generate data for new features:
```python
@staticmethod
def generate_new_data(count=10):
    """Generate mock data for new feature"""
    # Implementation
    return data
```

---

## Troubleshooting

### Server Won't Start

**Issue**: `ModuleNotFoundError: No module named 'flask_socketio'`
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

**Issue**: `Port 8080 is in use`
**Solution**: Change port in `app.py` or kill existing process
```bash
lsof -ti:8080 | xargs kill -9
```

### WebSocket Connection Issues

**Issue**: Live logs not updating
**Solution**: Check browser console for WebSocket errors, ensure server is running with SocketIO support

### Mock Data Not Loading

**Issue**: Results page shows "No data"
**Solution**: Populate mock data
```bash
curl -X POST http://localhost:8080/api/mock/populate
```

### Pipeline Execution Fails

**Issue**: Features fail with "dependencies not met"
**Solution**: Features must execute in order. Run full pipeline or ensure prerequisites completed successfully.

---

## Security Considerations

### Development vs Production

This interface is configured for **development use**. For production:

1. **Change SECRET_KEY**: Generate cryptographically secure key
2. **Disable DEBUG mode**: Set `debug=False` in `socketio.run()`
3. **Use production WSGI server**: Gunicorn, uWSGI, or similar
4. **Enable HTTPS**: Use reverse proxy (nginx, Apache) with SSL/TLS
5. **Implement authentication**: Add user authentication and authorization
6. **Restrict CORS**: Update `CORS(app)` to allow specific origins only
7. **Rate limiting**: Implement API rate limiting for production use

### Data Security

- Mock data is for testing only - do not use in production
- Real OSINT data may contain sensitive information - implement proper access controls
- Log files may contain IOCs and threat data - secure appropriately
- WebSocket connections transmit data in real-time - use WSS in production

---

## Performance Optimization

### Recommended Settings

- **Log Retention**: Default 1000 logs (configurable in `app.py`)
- **WebSocket Compression**: Enabled by default
- **Result Pagination**: Implement for large datasets (>1000 items)
- **Database Storage**: Consider PostgreSQL/MongoDB for production results storage

### Scaling Considerations

- Current implementation: Single-threaded execution
- For concurrent pipelines: Implement task queue (Celery, RQ)
- For multiple analysts: Add user sessions and isolated execution
- For large datasets: Implement result pagination and lazy loading

---

## Browser Compatibility

| Browser | Minimum Version | Status |
|---------|----------------|--------|
| Chrome | 90+ | Fully Supported |
| Firefox | 88+ | Fully Supported |
| Safari | 14+ | Fully Supported |
| Edge | 90+ | Fully Supported |

**Required Features:**
- ES6+ JavaScript support
- WebSocket API
- CSS Grid and Flexbox
- Fetch API

---

## Contributing

When adding features or improvements:

1. Maintain the workflow-focused design philosophy
2. Follow existing code structure and naming conventions
3. Update mock data generator for new data types
4. Add API documentation for new endpoints
5. Test WebSocket functionality thoroughly
6. Ensure responsive design on mobile devices
7. Update this README with any new features

---

## Changelog

### Version 2.0 - November 6, 2025

**Major Redesign: Workflow-Focused Architecture**

#### New Features
- Complete workflow orchestration system with 4-stage pipeline
- Automated dependency management and execution ordering
- One-click full pipeline execution with progress tracking
- Stage-based execution for analyst workflows
- Real-time WebSocket-powered log streaming
- Comprehensive mock data generation system
- Professional, minimalist UI with Inter typography

#### Technical Improvements
- Migrated from individual features to pipeline stages
- Implemented dependency resolution engine
- Added WebSocket support for real-time updates
- Created mock data system for testing and demos
- Built responsive grid layouts with Tailwind CSS
- Integrated Alpine.js for reactive UI components

#### Interface Updates
- Removed all emoji decorations for professional appearance
- Redesigned dashboard with workflow focus
- Added pipeline visualization page
- Enhanced results viewer with tabbed interface
- Improved logs page with terminal-style display
- Added "Load Mock Data" quick action button

#### API Additions
- `POST /api/pipeline/run` - Execute full pipeline
- `POST /api/pipeline/stage/{id}/run` - Execute specific stage
- `GET /api/pipeline/status` - Get execution state
- `POST /api/mock/populate` - Load simulated data

#### Dependencies
- Added Flask-SocketIO for WebSocket support
- Added Flask-CORS for cross-origin requests
- Integrated Tailwind CSS and Alpine.js via CDN
- Added Lucide Icons for professional iconography

---

## License

Same as parent project (MIT License)

---

## Support

For issues specific to the web interface:
- Check server logs in console output
- Verify all dependencies installed: `pip list | grep -i flask`
- Ensure port 8080 is available
- Check browser console for JavaScript errors
- Verify WebSocket connection in Network tab

For general OSINT tool questions, refer to parent project documentation.

---

**Built for security analysts who need professional, automated dark web intelligence gathering.**
