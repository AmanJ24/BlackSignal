# Quick Start Guide - Workflow Interface with Mock Data

## What's Been Built

### 1. Mock Data System
**File**: `mock_data.py`
- Generates realistic fake data for all 15 features
- 50+ onion domains
- 80+ IOCs (IPs, domains, hashes, Bitcoin addresses, emails)
- 20 marketplace listings with vendors, products, prices
- Enriched threat intelligence data
- 50 realistic log entries

### 2. Backend Updates (app.py)
- Pipeline orchestration with 4 stages
- Dependency management
- Mock data endpoint: `POST /api/mock/populate`
- Full pipeline execution: `POST /api/pipeline/run`
- Stage execution: `POST /api/pipeline/stage/{id}/run`

### 3. No Emojis
All emojis removed from:
- Backend code
- Log messages
- UI (will be completed in templates)

## How to Test Right Now

### Step 1: Start the Server
```bash
cd darkweb-osint-automater/web_interface
./start.sh
```

### Step 2: Populate Mock Data
Open another terminal and run:
```bash
curl -X POST http://localhost:8080/api/mock/populate
```

Or use your browser console on http://localhost:8080:
```javascript
fetch('/api/mock/populate', { method: 'POST' })
  .then(r => r.json())
  .then(console.log);
```

### Step 3: View the Data
- Navigate to http://localhost:8080/results
- You'll see mock data in all tabs:
  - .onion Domains (50 domains)
  - IOCs (80 indicators)
  - Marketplace Data (20 listings)
  - Enriched Data (15 enriched IPs)

## Current Workflow

The pipeline now works in 4 stages:

```
Stage 1: Data Collection
├─ Tor Relay Enumeration
├─ Onion Domain Discovery
├─ Marketplace Scraping
└─ STIX/TAXII Feeds
    ↓
Stage 2: Data Extraction
├─ IOC Extraction (depends on: onion-crawl, market-scrape)
├─ NER (depends on: market-scrape)
└─ Hash Extraction (depends on: market-scrape)
    ↓
Stage 3: Intelligence Enrichment
├─ API Enrichment (depends on: ioc-extract)
├─ Infrastructure Mapping (depends on: ioc-extract)
└─ Geolocation Correlation (depends on: api-enrich)
    ↓
Stage 4: Threat Analysis
├─ Handle Correlation (depends on: ner)
├─ Behavioral Analysis (depends on: market-scrape)
├─ Reputation Scoring (depends on: behavioral)
├─ MITRE ATT&CK Mapping (depends on: ioc-extract, behavioral)
└─ Affiliate Analysis (depends on: market-scrape, handle-corr)
```

## API Endpoints Available

### Mock Data
```bash
# Populate with fake data
POST /api/mock/populate
```

### Pipeline Control
```bash
# Run full pipeline (all 15 features)
POST /api/pipeline/run

# Run specific stage
POST /api/pipeline/stage/collection/run
POST /api/pipeline/stage/extraction/run
POST /api/pipeline/stage/enrichment/run
POST /api/pipeline/stage/analysis/run

# Get pipeline status
GET /api/pipeline/status
```

### Results
```bash
# Get specific results
GET /api/results/onion_domains
GET /api/results/iocs
GET /api/results/marketplace_data
GET /api/results/enriched_data
```

## Next Steps

### Templates Still Needed
I'm creating professional, workflow-focused templates:

1. **dashboard.html** - Main workflow view with pipeline controls
2. **pipeline.html** - Visual pipeline with stage diagram
3. **base.html** - Updated navigation (no emojis)
4. **results.html** - Updated (no emojis)
5. **logs.html** - Updated (no emojis)

### Design Principles
- **Clean typography** (Inter font)
- **Interesting but not fancy** visuals
- **Workflow-focused** UX
- **No emojis** anywhere
- **Professional** aesthetic

### Mock Data in Action
Once templates are complete, you'll see:
- Real-looking onion domains
- Realistic marketplace listings
- Genuine-looking IOCs
- Threat intelligence data
- Live log streams

## Testing the Mock Data

Open Python console:
```python
from mock_data import populate_mock_data
data = populate_mock_data()

# Check domains
print(f"Domains: {len(data['onion_domains']['domains'])}")

# Check IOCs
print(f"IPs: {len(data['iocs']['iocs']['ips'])}")
print(f"Total IOCs: {data['iocs']['total_iocs']}")

# Check marketplace
print(f"Listings: {len(data['marketplace_data']['scraped_data'])}")
```

## Current Status
- Backend: Complete
- Mock Data: Complete
- Templates: In Progress (completing now)

The workflow orchestration is ready - just need the UI to make it visible!
