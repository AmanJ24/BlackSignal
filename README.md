# 🕵️ OSINT + Threat Intel Automation Pipeline

**Automated Dark Web Monitoring & Threat Intelligence Pipeline built with n8n, Python, and Free-tier APIs**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Features](https://img.shields.io/badge/Features-12%2F15-green.svg)](https://github.com/AmanJ24/darkweb-osint-automater)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen.svg)](https://github.com/AmanJ24/darkweb-osint-automater)

---

## 📊 Project Status

**Features Completed: 12 / 15 (80% Complete)**

✅ **Active Features:**
- **Feature 1**: Tor Relay Enumeration
- **Feature 2**: .onion Domain Discovery  
- **Feature 3**: Marketplace Scraping
- **Feature 4**: API Enrichment (Multi-source)
- **Feature 5**: STIX/TAXII Feed Parsing
- **Feature 6**: IOC Extraction with Regex
- **Feature 7**: Named Entity Recognition (NER)
- **Feature 8**: Hash Extraction & Analysis
- **Feature 9**: Infrastructure Mapping
- **Feature 10**: Geolocation Correlation
- **Feature 11**: Handle Correlation
- **Feature 12**: Behavioral Analysis

🔄 **In Development:** Features 13-15

---

## 🔍 Overview

This project is a **modular, automated OSINT pipeline** for dark web monitoring and threat intelligence extraction:

- **15 Core Features** for comprehensive threat detection
- **Python-based microservices** with n8n orchestration
- **Tor network integration** for dark web access
- **Multi-source enrichment** using free threat intel APIs
- **Real-time webhook integration** for automated data flow
- **100% Free-tier implementation** (no paid tools required)

---

## 🎆 Key Features

### ✅ **Completed Features**
- 🌐 **Tor Relay Enumeration** - Discovers active Tor infrastructure
- 🧅 **Automated .onion Discovery** - Recursive hidden service crawling
- 🛍 **Marketplace Scraping** - Extracts vendor/product intelligence
- 📡 **API Enrichment** - Multi-source IOC enrichment (IP-API, BGPView, Shodan, etc.)
- 📄 **STIX/TAXII Integration** - Threat feed parsing and normalization
- 🔎 **IOC Extraction** - Comprehensive regex-based indicator extraction
- 🧠 **Named Entity Recognition (NER)** - Extract names, organizations, and entities
- 🔍 **Hash Extraction & Analysis** - Malware IOC detection and analysis
- 🌐 **Infrastructure Mapping** - C2 domains and bulletproof hosting detection
- 🌍 **Geolocation Correlation** - Enhanced geographic threat analysis
- 🔗 **Handle Correlation** - Cross-platform handle tracking and matching
- 📊 **Behavioral Analysis** - Vendor behavior patterns, sentiment analysis, and threat scoring

### 🚀 **Upcoming Features**
- 🏆 **Reputation Scoring** - Vendor trust and risk assessment
- 🎯 **MITRE ATT&CK TTP Mapping** - Link activities to attack techniques
- 💰 **Affiliate Recruitment Analysis** - RaaS and affiliate program detection

---

## 🧋 Tech Stack

**Core Technologies:**
- **Python 3.11+** (requests, stem, BeautifulSoup, Flask, spaCy)
- **n8n Cloud** (Workflow automation & webhook integration)
- **Tor Network** (SOCKS5 proxy for .onion access)

**Free APIs & Services:**
- IP-API, BGPView (Free geolocation & network info)
- AbuseIPDB, VirusTotal, Shodan (Threat intelligence)
- OTX/AlienVault (Community threat feeds)
- CIRCL/MISP (STIX/TAXII feeds)

---

## 📁 Project Structure

```bash
PROJECT_DARK_WEB/
├── PROJECT_DETAILS/              # Project documentation & progress
├── FEAT_1_TOR_RELAY/             # Tor relay enumeration
├── FEAT_2_ONION_CRAWL/           # .onion domain discovery
├── FEAT_3_MARKET_SCRAPE/         # Marketplace scraping
├── FEAT_4_API_ENRICH/            # Multi-API enrichment
├── FEAT_5_STIX_TAXII/            # Threat feed parsing
├── FEAT_6_IOC_EXTRACT/           # IOC extraction
├── FEAT_7_NER/                   # Named Entity Recognition
├── FEAT_8_HASH_EXTRACT/          # Hash extraction and analysis
├── FEAT_9_INFRA_MAP/             # Infrastructure mapping
├── FEAT_10_GEO_CORR/             # Geolocation correlation
├── FEAT_11_HANDLE_CORR/          # Handle correlation
├── FEAT_12_BEHAVIORAL_ANALYSIS/  # Behavioral analysis
├── logs/                         # Centralized logging
├── venv/                         # Python virtual environment
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Tor Browser** or **Tor daemon** (for .onion access)
- **n8n Cloud Account** (free tier available)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AmanJ24/darkweb-osint-automater.git
   cd PROJECT_DARK_WEB
   ```

2. **Set up virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Tor (if needed):**
   - Install Tor: `sudo apt install tor` (Linux)
   - Start Tor service: `sudo systemctl start tor`
   - Ensure SOCKS5 proxy on `127.0.0.1:9050`

### Running Features

Each feature can be run independently:

```bash
# Feature 4: API Enrichment
cd FEAT_4_API_ENRICH
python3 api_enrichment.py

# Feature 6: IOC Extraction  
cd FEAT_6_IOC_EXTRACT
python3 ioc_extractor.py

# Feature 12: Behavioral Analysis
cd FEAT_12_BEHAVIORAL_ANALYSIS
python3 behavioral_analysis.py
```

---

## ⚙️ Configuration

### API Keys (Optional)
For enhanced functionality, add API keys to `.secrets.env`:
```bash
VIRUSTOTAL_API_KEY=your_key_here
ABUSEIPDB_API_KEY=your_key_here
SHODAN_API_KEY=your_key_here
```

### n8n Webhook Setup
Each feature sends results to n8n webhooks. Expected endpoints:
- `api-enrich`
- `ioc-extract`
- `geo-correlation`
- `handle-correlation`
- `behavioral-analysis`

---

## 📊 Feature Details

| Feature | Status | Description | Webhook Endpoint |
|---------|--------|-------------|------------------|
| **Feature 1** | ✅ | Tor Relay Enumeration | `tor-relays` |
| **Feature 2** | ✅ | .onion Domain Discovery | `onion-discovery` |
| **Feature 3** | ✅ | Marketplace Scraping | `market-scrape` |
| **Feature 4** | ✅ | API Enrichment | `api-enrich` |
| **Feature 5** | ✅ | STIX/TAXII Parsing | `stix-taxii` |
| **Feature 6** | ✅ | IOC Extraction | `ioc-extract` |
| **Feature 10** | ✅ | Geolocation Correlation | `geo-correlation` |
| **Feature 11** | ✅ | Handle Correlation | `handle-correlation` |
| **Feature 12** | ✅ | Behavioral Analysis | `behavioral-analysis` |
| **Feature 7** | ✅ | Named Entity Recognition | `ner-analysis` |
| **Feature 8** | ✅ | Hash Extraction | `hash-analysis` |
| **Feature 9** | ✅ | Infrastructure Mapping | `infra-mapping` |
| **Feature 13** | 🔄 | Reputation Scoring | `reputation-scoring` |
| **Feature 14** | 🔄 | MITRE ATT&CK Mapping | `mitre-mapping` |
| **Feature 15** | 🔄 | Affiliate Analysis | `affiliate-analysis` |

---

## 🔒 Security Notes

- **Tor Usage**: All .onion requests route through Tor SOCKS5 proxy
- **API Keys**: Stored in `.secrets.env` (excluded from version control)
- **Rate Limiting**: Implemented for all external API calls
- **Error Handling**: Comprehensive exception handling for network failures

---

## 🤝 Contributing

Contributions are welcome! Please feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. Users are responsible for complying with applicable laws and regulations. The authors assume no liability for misuse of this software.

---

**Built with ❤️ for the cybersecurity community**
