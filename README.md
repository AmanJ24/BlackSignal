# 🕵️ OSINT & Threat Intel Automation Pipeline

**A modular, automated Dark Web Monitoring and Threat Intelligence Pipeline built with Python microservices, n8n, and free-tier APIs.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Features](https://img.shields.io/badge/Features-15%2F15-brightgreen.svg)](https://github.com/AmanJ24/darkweb-osint-automater)
[![Status](https://img.shields.io/badge/Status-Completed-blue.svg)](https://github.com/AmanJ24/darkweb-osint-automater)

---

## 📊 Project Status

**Development Complete: 15 / 15 Features Implemented**

This project has completed its core feature development. All 15 microservices are fully implemented and ready for integration into an automated workflow. The current focus is on building and refining the n8n orchestration pipeline.

---

## 🔍 Overview

This project is a **modular OSINT pipeline** designed for automated dark web monitoring and threat intelligence extraction. It leverages a powerful combination of Python-based microservices, orchestrated by the workflow automation tool **n8n**, to create a comprehensive and cost-effective monitoring solution.

-   **15 Core Features** for comprehensive data collection, enrichment, and analysis.
-   **Microservice Architecture** with standalone Python scripts for each feature.
-   **Tor Network Integration** for seamless and anonymous access to `.onion` sites.
-   **Multi-Source Enrichment** using a variety of free-tier threat intelligence APIs.
-   **Webhook-Driven** for a fully automated, event-driven data flow orchestrated by n8n.
-   **100% Free-Tier Implementation**, requiring no paid tools or subscriptions to operate.

---

## ⚙️ How It Works: The Automation Pipeline

The project is not a single application but a collection of specialized tools designed to be chained together in an orchestration platform like n8n. The data flows through the pipeline, getting richer and more insightful at each step.

1.  **Trigger**: The pipeline starts with a trigger in n8n (e.g., a schedule that runs every 12 hours).
2.  **Collection**: An n8n node calls a data collection script (e.g., **Onion Crawler** or **Marketplace Scraper**).
3.  **Extraction**: The script runs and sends its raw text output to an n8n webhook. n8n then passes this text to the extraction services (**IOC Extractor**, **NER**, **Hash Extractor**).
4.  **Enrichment**: The extracted IOCs (IPs, domains, hashes) are sent to the enrichment services (**API Enrichment**, **Infrastructure Mapper**, **Geolocation Correlator**).
5.  **Analysis**: The fully enriched data and original posts are then sent to the final analysis services for deeper insights (**Behavioral Analysis**, **Reputation Scoring**, **MITRE ATT&CK Mapping**, **Affiliate Analysis**).
6.  **Aggregation**: n8n receives the final, structured JSON reports and sends them to a destination, such as a database, a Google Sheet, or a security monitoring tool.

---

## 🎆 Key Features

All 15 core features of the pipeline have been implemented and are fully operational:

### Core Data Collection
-   🌐 **Tor Relay Enumeration** - Discovers and lists active Tor network infrastructure.
-   🧅 **Automated .onion Discovery** - Recursively crawls hidden services to find new .onion domains.
-   🛍 **Marketplace Scraping** - Extracts vendor names, product listings, and prices from dark web marketplaces.
-   📄 **STIX/TAXII Integration** - Parses structured threat intelligence from TAXII feeds like Abuse.ch.

### Data Processing & Enrichment
-   🔎 **IOC Extraction** - Uses comprehensive regex patterns to extract a wide range of IOCs from raw text.
-   🧠 **Named Entity Recognition (NER)** - Identifies and extracts key entities like names, organizations, and locations.
-   🔍 **Hash Extraction & Analysis** - Detects malware hashes (MD5, SHA1, SHA256) and enriches them via VirusTotal.
-   📡 **API Enrichment** - Enriches IOCs with data from IP-API, BGPView, OTX, Shodan, and more.

### Analysis & Intelligence Generation
-   🌐 **Infrastructure Mapping** - Analyzes IP addresses to identify hosting providers, open ports, and potential C2 servers.
-   🌍 **Geolocation Correlation** - Correlates multiple IPs to identify geographic patterns and high-risk locations.
-   🔗 **Handle Correlation** - Tracks and matches threat actor handles across different platforms and data sources.
-   📊 **Behavioral Analysis** - Analyzes vendor posting frequency, sentiment, and pricing to detect patterns.
-   🏆 **Reputation Scoring** - Calculates a reputation score for vendors based on feedback, transaction history, and age.
-   🎯 **MITRE ATT&CK TTP Mapping** - Links observed activities and keywords to specific MITRE ATT&CK techniques.
-   💰 **Affiliate Recruitment Analysis** - Detects Ransomware-as-a-Service (RaaS) structures by analyzing payment patterns and recruitment language.

---

## 🧋 Tech Stack

**Core Technologies:**
-   **Python 3.11+** (requests, stem, BeautifulSoup, Flask, spaCy, TextBlob)
-   **n8n Cloud** (Workflow automation & webhook integration)
-   **Tor Network** (SOCKS5 proxy for `.onion` access)

**Free APIs & Services:**
-   IP-API, BGPView (Geolocation & network info)
-   AbuseIPDB, VirusTotal, Shodan (Threat intelligence)
-   OTX/AlienVault (Community threat feeds)
-   Abuse.ch (Malware and URLhaus feeds)

---

## 📁 Project Structure

The project uses a clean, microservice-based architecture. Each feature is a self-contained module with its own dependencies, making it modular and easy to maintain.

```bash
.
├── config.py                     # Central configuration for API keys and webhooks
├── docs/                         # Project documentation
├── FEAT_1_TOR_RELAY/             # Feature 1: Tor relay enumeration
│   └── tor_api.py
│   └── requirements.txt
├── FEAT_2_ONION_CRAWL/           # Feature 2: .onion domain discovery
│   └── onion_domain_discovery.py
│   └── requirements.txt
├── ... (and so on for all 15 features) ...
├── logs/                         # Centralized logging folder (ignored by git)
├── output/                       # Local JSON output from scripts (ignored by git)
├── .gitignore                    # Git ignore file
├── README.md                     # This file
└── .secrets.env.example          # Example file for storing API keys
```

---

## 🚀 Getting Started

### Prerequisites
-   **Python 3.11+**
-   **Tor Browser** or a running **Tor daemon**
-   **n8n Cloud Account** (the free tier is sufficient)
-   **Git**

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AmanJ24/darkweb-osint-automater.git
    cd darkweb-osint-automater
    ```

2.  **Configure API Keys:**
    -   Rename `.secrets.env.example` to `.secrets.env`.
    -   Add your free API keys to the `.secrets.env` file. This file is ignored by Git to protect your secrets.
    ```bash
    # .secrets.env
    VIRUSTOTAL_API_KEY=your_key_here
    ABUSEIPDB_API_KEY=your_key_here
    SHODAN_API_KEY=your_key_here
    ```

3.  **Configure Tor:**
    -   Ensure the Tor service is running.
    -   Verify that your `config.py` points to the correct SOCKS proxy (`127.0.0.1:9050`) and control port (`127.0.0.1:9051`).

### Running a Feature (Manual Testing)

Each feature can be tested individually.

1.  **Navigate to a feature directory:**
    ```bash
    cd FEAT_6_IOC_EXTRACT/
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install its specific dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the script:**
    ```bash
    python3 ioc_extractor.py
    ```
    This will run the script using its sample data and send the results to the configured n8n webhook.

---

## ⚙️ n8n Orchestration

The true power of this project is realized when orchestrated by n8n.

1.  **Create Webhooks in n8n:** For each feature, create a "Webhook" node in n8n. This will generate a unique URL.
2.  **Update `config.py`:** Add the webhook URLs generated by n8n to the `WEBHOOK_URLS` dictionary in your `config.py` file.
3.  **Build Your Workflow:** Chain the features together using "HTTP Request" nodes in n8n to call your Python microservices. Use the output of one service as the input for the next.

---

## 🔒 Security Notes

-   **Tor Usage**: All requests to `.onion` sites are automatically routed through the Tor SOCKS5 proxy.
-   **API Keys**: Keys are loaded from a `.secrets.env` file, which is included in `.gitignore`.
-   **Rate Limiting**: Scripts include built-in delays to respect the rate limits of free public APIs.
-   **Error Handling**: Each script contains comprehensive exception handling to manage network failures and API errors gracefully.

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve the pipeline, please feel free to:
-   Report bugs and issues.
-   Suggest new features or data sources.
-   Submit pull requests with enhancements.
-   Improve documentation.

---

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

---

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. The user is responsible for ensuring their use of this software complies with all applicable laws and regulations. The authors assume no liability for any misuse of this software.

---

**Built with ❤️ for the cybersecurity community**
