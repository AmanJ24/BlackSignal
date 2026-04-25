# 🕵️ BlackSignal — Dark Web Threat Intelligence Pipeline

**Automated dark web OSINT collection, enrichment, and threat scoring — built for security teams who need to know what's happening on Tor before it hits their network.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-29%20passing-brightgreen.svg)]()

---

## Why BlackSignal Exists

Dark web marketplaces sell stolen credentials, leaked databases, ransomware kits, and zero-day exploits **every day**. Most organizations only learn about this _after_ the breach.

BlackSignal fills that gap. It's a **proactive intelligence pipeline** that continuously monitors dark web sources and answers one question:

> _What activity on the dark web is relevant to my organization, and how dangerous is it?_

### Real-World Use Cases

| Who Uses It | What They Get |
|-------------|--------------|
| **SOC Analysts** | Automated alerts when company credentials, domains, or IPs appear in dark web listings |
| **Threat Intelligence Teams** | Structured IOC feeds (hashes, IPs, wallets) enriched with VirusTotal/AbuseIPDB/Shodan data |
| **Incident Responders** | MITRE ATT&CK TTP mapping from marketplace posts — identify attacker playbooks before they strike |
| **Security Researchers** | Behavioral profiling of threat actors — track vendor reputation, RaaS affiliate patterns, handle correlation across forums |
| **Red Teams** | Understand what's being sold (exploit kits, credentials) to anticipate attack vectors |
| **CISOs / Risk Teams** | Confidence-scored threat reports — prioritize response based on data, not gut feeling |

### What It Actually Produces

BlackSignal doesn't just "scrape the dark web" — it generates **actionable intelligence artifacts**:

```
📊 Scored Intelligence Report
├── Entity: "DarkVault_Vendor_X"
│   ├── Threat Score: 87/100 (CRITICAL)
│   ├── Severity: CRITICAL
│   ├── Evidence:
│   │   ├── behavioral: high_risk_keywords (ransomware, exploit) — confidence: 0.8
│   │   ├── mitre: T1486 Data Encrypted for Impact — confidence: 0.7
│   │   ├── affiliate: RaaS recruitment detected — confidence: 0.9
│   │   └── ioc: SHA256 detected by 14 VirusTotal engines — confidence: 1.0
│   └── Overall Confidence: 0.85
```

---

## Skills & Technologies Demonstrated

This project is an end-to-end Cyber Threat Intelligence (CTI) platform, built to showcase practical intersections between software engineering and security operations. It demonstrates:

- **Systems Architecture & Data Engineering**: Designing DAG-based, unidirectional parallel processing pipelines with explicit fault tolerance and fail-fast guarantees.
- **Offensive Security & OSINT**: Automating safe Tor interactions, extracting structured IOCs from dark web marketplaces, and profiling TTPs against the **MITRE ATT&CK** framework.
- **Machine Learning & NLP**: Utilizing Named Entity Recognition (**spaCy**) for extracting handles, vendors, and targets from unstructured forum posts.
- **Full Stack Development**: Orchestrating backend analytics with live WebSockets, delivering real-time visualizations via a **Flask** monitoring dashboard.
- **Production DevOps**: Containerized deployment patterns utilizing **Docker Compose** and **Makefiles** for reproducible environments.

---

## Architecture

BlackSignal is a **DAG-based, unidirectional pipeline** — not a collection of scripts. Each stage has strict data contracts, explicit dependencies, and isolated execution.

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          COLLECTION (Parallel)                          │
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────┐ ┌─────────────┐    │
│  │ Tor Relay    │ │ .onion        │ │ Marketplace  │ │ STIX/TAXII  │    │
│  │ Inventory    │ │ Discovery     │ │ Scraper      │ │ Feed Ingest │    │
│  └──────────────┘ └───────────────┘ └──────────────┘ └─────────────┘    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ data/raw/*.json
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROCESSING (Parallel)                           │
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────┐                    │
│  │ IOC Extract  │ │ Hash Extract  │ │ NER Extract  │                    │
│  │ (IPs, BTC,   │ │ (MD5, SHA1,   │ │ (People, Org │                    │
│  │  Emails)     │ │  SHA256)      │ │  Locations)  │                    │
│  └──────────────┘ └───────────────┘ └──────────────┘                    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ data/normalized/*.json
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ENRICHMENT (Parallel)                           │ 
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────┐                    │
│  │ VirusTotal   │ │ Shodan /      │ │ Geo-IP       │                    │
│  │ AbuseIPDB    │ │ BGPView       │ │ Correlation  │                    │
│  └──────────────┘ └───────────────┘ └──────────────┘                    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ data/enriched/*.json
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          ANALYSIS (Parallel)                            │
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────┐ ┌─────────────┐    │
│  │ Behavioral   │ │ MITRE ATT&CK  │ │ Affiliate /  │ │ Handle      │    │
│  │ Profiling    │ │ TTP Mapping   │ │ RaaS Detect  │ │ Correlation │    │
│  └──────────────┘ └───────────────┘ └──────────────┘ └─────────────┘    │
│                           │                                             │
│                   ┌───────▼────────┐                                    │
│                   │  Reputation    │                                    │
│                   │  Aggregation   │                                    │
│                   └────────────────┘                                    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ data/intelligence/*.json
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       SCORING (Final Stage)                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Confidence-Weighted Threat Scoring Engine                       │    │
│  │ Input: all enriched + intelligence evidence                     │    │
│  │ Output: 0-100 score, severity (LOW/MED/HIGH/CRITICAL),          │    │
│  │         per-signal breakdown with confidence intervals          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ scored_intelligence_*.json
                                ▼
                    📊 Analyst Dashboard (Web UI)
```

### Key Design Decisions

- **DAG execution** — Stages run in parallel; dependencies are explicit, not inferred from file names
- **Fail-fast for critical stages** — If collection or scoring fails, the pipeline halts. Non-critical failures are skipped gracefully
- **Tor-first networking** — All dark web access routes through `TorManager` with per-purpose circuit isolation. No silent clearnet fallback
- **Data flows forward only** — Raw → Normalized → Enriched → Intelligence → Scored. No stage mutates upstream data
- **Evidence-based scoring** — Every threat score is decomposable: you can trace exactly _why_ an entity scored 87/100

---

## Project Structure

```
BlackSignal/
├── core/                       # Brain of the system
│   ├── pipeline/
│   │   ├── pipeline_engine.py  # Async DAG executor with fail-fast
│   │   ├── stage_registry.py   # DAG definition — all stage dependencies
│   │   └── scoring_stage.py    # Final stage: evidence → scored intelligence
│   ├── tor/
│   │   └── tor_manager.py      # Tor SOCKS proxy + circuit management
│   ├── scoring_engine.py       # Confidence-weighted 0-100 threat scorer
│   ├── logging_config.py       # Centralized rotating-file + console logging
│   └── schemas/
│       └── scoring_input_schema.json  # Data contract for scoring input
│
├── collectors/                 # Stage 1: Tor-facing data collection
│   ├── tor/relay_inventory.py        # Tor consensus relay enumeration
│   ├── discovery/onion_discovery.py  # Recursive .onion link crawler
│   ├── marketplaces/market_scraper.py # Dark marketplace page scraper
│   └── feeds/stix_taxii_ingest.py    # URLHaus / STIX threat feed ingest
│
├── processors/                 # Stage 2: IOC & entity extraction
│   └── extraction/
│       ├── ioc_extractor.py    # IPs, emails, BTC/ETH wallets, .onion domains
│       ├── hash_extractor.py   # MD5, SHA1, SHA256 hashes
│       └── ner_extractor.py    # Named Entity Recognition (spaCy)
│
├── enrichment/                 # Stage 3: External intelligence correlation
│   ├── api_enrichment.py       # VirusTotal + AbuseIPDB lookups
│   ├── infrastructure_mapper.py # Shodan + BGPView ASN analysis
│   ├── geolocation_correlator.py # Geo-IP risk correlation
│   └── utils.py                # Base enricher class
│
├── analysis/                   # Stage 4: Threat analysis
│   ├── behavioral_analysis.py  # Sentiment + keyword risk scoring
│   ├── mitre_attack_mapping.py # MITRE ATT&CK TTP detection
│   ├── affiliate_analysis.py   # RaaS / affiliate recruitment detection
│   ├── handle_correlation.py   # Threat actor alias matching
│   └── reputation_analysis.py  # Multi-source evidence aggregation
│
├── orchestration/
│   └── run_pipeline.py         # CLI entry point
│
├── web/
│   ├── app.py                  # Flask + SocketIO dashboard server
│   └── templates/dashboard.html # Live pipeline UI
│
├── data/                       # Pipeline data (gitignored)
│   ├── raw/                    # Stage 1 output
│   ├── normalized/             # Stage 2 output
│   ├── enriched/               # Stage 3 output
│   └── intelligence/           # Stage 4+5 output (includes scored results)
│
├── tests/                      # pytest test suite (29 tests)
│   ├── test_scoring_engine.py  # ScoringEngine unit tests
│   └── test_extractors.py      # IOC + Hash pattern tests
│
├── config/settings.py          # Runtime config + env loading
├── requirements.txt            # Python dependencies
├── setup.sh                    # One-command setup script
└── .secrets.env.example        # Template for API keys and credentials
```

---

## Quick Start

### Prerequisites

- Python **3.10+**
- A running **Tor daemon** with control port enabled
  - SOCKS proxy: `127.0.0.1:9050`
  - Control port: `127.0.0.1:9051`

### Installation

**Option 1: Using Make (Local Setup)**
```bash
git clone https://github.com/AmanJ24/BlackSignal
cd BlackSignal

make install
```
This creates a virtual environment, installs dependencies, and downloads NLP models.

**Option 2: Using Docker (Recommended)**
```bash
docker-compose up -d
```
This builds and runs the application and a Tor daemon in isolated containers.

### Configuration

```bash
cp .env.example .env
# Edit .env with your API keys and Tor password
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `TOR_PASSWORD` | ✅ | Tor control port authentication |
| `VIRUSTOTAL_API_KEY` | ❌ | Hash reputation lookups |
| `ABUSEIPDB_API_KEY` | ❌ | IP abuse scoring |
| `SHODAN_API_KEY` | ❌ | Infrastructure reconnaissance |
| `DASHBOARD_USER` / `DASHBOARD_PASSWORD` | ❌ | Dashboard HTTP auth (disabled if unset) |

> The pipeline runs without API keys, but enrichment depth will be reduced.

---

## Usage

### Run the Pipeline (CLI)

```bash
# Locally:
make run

# via Docker:
docker-compose --profile pipeline-run up blacksignal-pipeline
```

Output:
```
14:32:01 │ PipelineEngine       │ INFO    │ 🎬 Starting OSINT Pipeline...
14:32:01 │ PipelineEngine       │ INFO    │ 🚀 Starting Stage: relay_inventory
14:32:01 │ PipelineEngine       │ INFO    │ 🚀 Starting Stage: stix_ingest
14:32:03 │ PipelineEngine       │ INFO    │ ✅ Finished Stage: stix_ingest (2.1s) [SUCCESS]
14:32:15 │ PipelineEngine       │ INFO    │ 🚀 Starting Stage: ioc_extraction
...
14:33:42 │ ScoringStage         │ INFO    │ 🎯 Scored 47 entities — 🔴 3 CRITICAL, 🟠 8 HIGH
14:33:42 │ PipelineEngine       │ INFO    │ 🏁 Pipeline Completed in 101s — ✅ 16 succeeded, ❌ 0 failed, ⏭️ 0 skipped
```

### Run the Dashboard

```bash
# Locally:
make web

# If using Docker, the dashboard runs automatically on startup.
# Open http://localhost:8080
```

Features:
- **One-click pipeline execution** with live log streaming
- **Data explorer** — browse raw, normalized, enriched, and scored intelligence
- **Real-time status** via WebSocket

### Run Tests

```bash
make test
```

---

## How the Scoring Works

Every entity (IP, hash, vendor handle, wallet) accumulates **evidence** from multiple pipeline stages. The Scoring Engine converts this into a single threat score:

```
Threat Score = Σ (signal_confidence × category_weight × 10)
```

| Evidence Category | Weight | Example Signal |
|-------------------|--------|----------------|
| `ioc` | 1.0× | IP found in threat feed |
| `infrastructure` | 1.5× | Hosted on bulletproof ASN |
| `behavioral` | 2.0× | Negative sentiment + ransomware keywords |
| `mitre` | 2.5× | Matches T1486 (Data Encrypted for Impact) |
| `affiliate` | 3.0× | RaaS recruitment language detected |

- Score is **capped at 100** and bucketed into severity levels: LOW (<40), MEDIUM (40-59), HIGH (60-79), CRITICAL (80+)
- Every score includes a **reason breakdown** — no black-box outputs

---

## Security & OpSec

- ✅ All dark web traffic routed through Tor with per-purpose circuit isolation
- ✅ Circuit renewal (`NEWNYM`) supported for long-running operations
- ✅ No silent clearnet fallback — if Tor fails, collection halts
- ✅ Dashboard supports optional HTTP Basic Auth  
- ✅ Path traversal protection on data API endpoints
- ✅ Secrets loaded from `.env` (gitignored)
- ✅ SECRET_KEY auto-generated if not set

---

## Disclaimer

**For educational and research purposes only.**

Accessing dark web services may be illegal in some jurisdictions. You are responsible for ensuring compliance with all applicable laws. The authors assume no liability for misuse.

---

## Contributing

Contributions are welcome, but must follow architectural rules:

1. All Tor access must go through `TorManager`
2. Pipeline data flows forward only — never mutate upstream artifacts
3. All analysis modules must emit confidence-scored evidence
4. New stages must be registered in `stage_registry.py` with explicit dependencies
5. Tests are required for new logic — run `pytest` before submitting

---

**Built to understand the dark web, not just scrape it.**
