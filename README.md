# 🕵️ darkweb-osint-automator

**Private Threat Intelligence Automation Toolkit built with n8n, Python, and free-tier threat intel APIs**

---

## 🔍 Overview

This project is a modular, fully automated **Dark Web Threat Intelligence Pipeline** that uses a combination of:
- Python-based scrapers & crawlers
- Tor network integration
- IOC extraction and enrichment
- Threat actor profiling
- All orchestrated through **n8n workflows**

It fetches actionable indicators like .onion domains, BTC addresses, malware hashes, ransomware TTPs, and correlates them across free OSINT sources.

---

## 🚀 Features

- 🌐 **Tor Relay Enumeration**
- 🧅 **Automated .onion Domain Discovery**
- 🛒 **Hidden Marketplace Scraping**
- 🧠 **IOC Extraction & Parsing**
- 🧬 **Threat Actor Profiling**
- 📡 **API Integration with VirusTotal, OTX, AbuseIPDB, etc.**
- 🧰 **Built with n8n Cloud & Python microservices**
- 🔐 100% Free-tier implementation (no paid tools)

---

## 🧱 Tech Stack

- Python (requests, stem, BeautifulSoup, re, Flask)
- n8n (Cloud for automation)
- Tor Proxy (SOCKS5)
- Free-tier APIs: VirusTotal, OTX, BGPView, AbuseIPDB

---

## 📁 Project Structure

```bash
darkweb-osint-automator/
├── README.md
├── LICENSE
├── .gitignore
├── n8n_workflows/
├── crawlers/
├── scrapers/
├── docs/
├── samples/
└── utils/

