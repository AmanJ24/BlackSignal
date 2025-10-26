# 🕵️ OSINT & Threat Intel Automation Pipeline (Local Version)

**A modular, self-contained Dark Web Monitoring and Threat Intelligence Pipeline built with Python microservices and orchestrated by a master script.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Features](https://img.shields.io/badge/Features-15%2F15-brightgreen.svg)](https://github.com/AmanJ24/darkweb-osint-automater)
[![Status](https://img.shields.io/badge/Status-Completed-blue.svg)](https://github.com/AmanJ24/darkweb-osint-automater)

---

## 📊 Project Status

**Development Complete: 15 / 15 Features Implemented**

This project is a fully functional, local-first OSINT pipeline. All 15 features are complete and are orchestrated by a central `main_pipeline.py` script, allowing for end-to-end execution on a local machine.

---

## 🔍 Overview

This project is a **modular, automated OSINT pipeline** designed for dark web monitoring and threat intelligence extraction. It uses a powerful collection of Python-based microservices that run sequentially to collect, parse, enrich, and analyze data from the dark web.

-   **15 Core Features** for a comprehensive intelligence lifecycle.
-   **Local-First Architecture** runs entirely on your machine with no external workflow orchestrators needed.
-   **Master Pipeline Script** (`main_pipeline.py`) to automate the entire workflow from start to finish.
-   **Tor Network Integration** for seamless and anonymous access to `.onion` sites.
-   **Multi-Source Enrichment** using a variety of free-tier threat intelligence APIs.
-   **100% Free-Tier Implementation**, requiring no paid tools or subscriptions to operate.

---

## ⚙️ How It Works: The Local Pipeline

The pipeline is orchestrated by the `main_pipeline.py` script, which executes each feature in a logical sequence. The workflow is file-based, with each script saving its results to the `/output` directory, which can then be used as input for subsequent steps.

1.  **Trigger**: The user runs `python3 main_pipeline.py`.
2.  **Data Collection**: The orchestrator runs the initial data gathering scripts (**Onion Crawler**, **Marketplace Scraper**, **STIX/TAXII Parser**). These scripts save their findings as JSON files in the `/output` directory.
3.  **Extraction & Analysis**: The orchestrator then runs the analysis scripts. These scripts are designed to **read the output files** from the previous stage, perform their analysis (e.g., extracting IOCs, mapping to MITRE), and save their own results back to the `/output` directory.
4.  **Final Report**: After all stages are complete, the `/output` folder contains a complete set of JSON files representing the full intelligence report.

---

## 🎆 Key Features

All 15 core features of the pipeline are fully implemented and integrated into the local workflow:

-   🌐 **Tor Relay Enumeration**: Discovers and lists active Tor network relays.
-   🧅 **Automated .onion Discovery**: Crawls hidden services to find new `.onion` domains.
-   🛍 **Marketplace Scraping**: Extracts listings and raw text from a target `.onion` site.
-   📄 **STIX/TAXII Integration**: Parses structured threat intelligence from public feeds like Abuse.ch.
-   🔎 **IOC Extraction**: Extracts IPs, domains, hashes, and other IOCs from text.
-   🧠 **Named Entity Recognition (NER)**: Identifies People, Organizations, and Groups in text.
-   🔍 **Hash Extraction & Analysis**: Enriches malware hashes with VirusTotal intelligence.
-   📡 **API Enrichment**: Enriches IOCs with data from IP-API, BGPView, OTX, and more.
-   🌐 **Infrastructure Mapping**: Analyzes IP addresses to identify hosting providers and open ports.
-   🌍 **Geolocation Correlation**: Identifies geographic patterns and high-risk IP locations.
-   🔗 **Handle Correlation**: Matches vendor handles against a local database of known threat actors.
-   📊 **Behavioral Analysis**: Analyzes vendor posting frequency, sentiment, and risk keywords.
-   🏆 **Reputation Scoring**: Calculates a reputation score for vendors based on provided data.
-   🎯 **MITRE ATT&CK TTP Mapping**: Maps threat descriptions to the MITRE ATT&CK framework.
-   💰 **Affiliate Recruitment Analysis**: Detects signs of Ransomware-as-a-Service (RaaS) operations.

---

## 🧋 Tech Stack

-   **Python 3.11+** (requests, stem, BeautifulSoup, Flask, spaCy, TextBlob)
-   **Tor Network** (SOCKS5 proxy for `.onion` access)
-   **Free APIs:** IP-API, BGPView, AbuseIPDB, VirusTotal, OTX/AlienVault.

---

## 🚀 Getting Started

### Prerequisites
-   **Python 3.11+** and `pip`
-   **Tor** installed and running as a service.
-   **Git** for cloning the repository.
-   **Curl** command-line tool (required by the onion crawler).

### 1. Initial Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/AmanJ24/darkweb-osint-automater.git
    cd darkweb-osint-automater
    ```

2.  **Configure Tor Control Port:**
    -   You must enable the Tor Control Port for Features 1 and 2 to work. Open your `torrc` file (usually at `/etc/tor/torrc` on Linux).
    -   Generate a hashed password by running `tor --hash-password "your_password_here"`.
    -   Add/uncomment the following lines in your `torrc` file, replacing the hash with the one you generated:
        ```
        ControlPort 9051
        HashedControlPassword YOUR_HASHED_PASSWORD_HERE
        ```
    -   Restart the Tor service: `sudo systemctl restart tor`.

3.  **Set Up Master Environment:**
    ```bash
    # Create the master virtual environment
    python3 -m venv master_venv

    # Activate it
    source master_venv/bin/activate

    # Install all project dependencies
    pip install -r master_requirements.txt

    # Download required NLP models
    python -m spacy download en_core_web_sm
    python -m textblob.download_corpora
    ```

### 2. Configure Your Intelligence & Keys

Before running the pipeline, you must provide it with some initial data and your API keys.

1.  **API Keys:**
    -   Rename `.secrets.env.example` to `.secrets.env`.
    -   Add your free API keys for **VirusTotal**, **AbuseIPDB**, and **Shodan** to this file.

2.  **Tor Password:**
    -   Open `config.py` and update the `TOR_PASSWORD` variable to match the password you used for the `HashedControlPassword`.

3.  **Scraping Target:**
    -   Open `FEAT_3_MARKET_SCRAPE/marketplace_scraper.py` and change the `TARGET_URL` variable to the `.onion` marketplace or forum you wish to scrape.
    -   **Important:** You will likely need to update the CSS selectors in this script to match the HTML structure of your target site.

4.  **Threat Actor & MITRE Data:**
    -   Populate `FEAT_11_HANDLE_CORR/known_handles.json` with known threat actor aliases.
    -   Populate `FEAT_14_MITRE_ATTACK/mitre_attack_data.json` with MITRE TTPs and associated keywords.

### 3. Run the Pipeline

Once setup is complete, you can run the entire pipeline with a single command from the project's root directory.

```bash
# Make sure your master_venv is active
source master_venv/bin/activate

# Execute the master pipeline script
python3 main_pipeline.py
```

The script will execute each feature in sequence. All log files will be written to the `/logs` directory, and all final JSON reports will be saved in the `/output` directory.

---

## 🔒 Security and Disclaimer

-   This tool is intended for **educational and research purposes only**.
-   All `.onion` requests are routed through Tor. Ensure your Tor service is active and properly configured.
-   API keys are stored in a `.secrets.env` file, which is ignored by Git, but it is your responsibility to keep them secure.
-   The user is responsible for complying with all applicable laws and the terms of service of any website they choose to scrape. The authors assume no liability for misuse of this software.

---

**Built with ❤️ for the cybersecurity community**
