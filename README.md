# 🕵️ OSINT + Threat Intel Automation Pipeline

**Automated Dark Web Monitoring & Threat Intelligence Pipeline built with n8n, Python, and Free-tier APIs**

---

## 📊 Project Status

**Features Completed: 7 / 15**

✅ **Active Features:**
- Tor Relay Enumeration
- .onion Domain Discovery
- Marketplace Scraping
- API Enrichment (Multi-source)
- STIX/TAXII Feed Parsing
- IOC Extraction with Regex
- Geolocation Correlation

🔄 **In Development:** Features 7-9, 11-15

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
- 🛒 **Marketplace Scraping** - Extracts vendor/product intelligence
- 📡 **API Enrichment** - Multi-source IOC enrichment (IP-API, BGPView, Shodan, etc.)
- 📄 **STIX/TAXII Integration** - Threat feed parsing and normalization
- 🔎 **IOC Extraction** - Comprehensive regex-based indicator extraction
- 🌍 **Geolocation Correlation** - Enhanced geographic threat analysis

### 🚀 **Upcoming Features**
- 🧠 Named Entity Recognition (NER)
- 🔍 Hash Extraction & Analysis
- 🌐 Infrastructure Mapping
- 🔗 Handle Correlation
- 📊 Behavioral Analysis
- 🏆 Reputation Scoring
- 🎯 MITRE ATT&CK TTP Mapping
- 💰 Affiliate Recruitment Analysis

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
├── PROJECT_DETAILS/          # Project documentation & progress
├── TOR_RELAY_FEAT_1/         # Tor relay enumeration
├── ONION_CRAWL_FEAT_2/       # .onion domain discovery
├── MARKET_SCRAPE_FEAT_3/     # Marketplace scraping
├── API_ENRICH_FEAT_4/        # Multi-API enrichment
├── STIX_TAXII_FEAT_5/        # Threat feed parsing
├── IOC_EXTRACT_FEAT_6/       # IOC extraction
├── GEO_CORR_FEAT_10/         # Geolocation correlation
├── logs/                     # Centralized logging
├── venv/                     # Python virtual environment
├── config.py                 # Global configuration
├── requirements.txt          # Dependencies
└── README.md                 # This file

