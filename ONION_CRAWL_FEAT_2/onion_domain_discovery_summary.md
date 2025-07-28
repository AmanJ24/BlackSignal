
# 🌐 Automated .onion Domain Discovery via Recursive Crawling

## 🔧 Purpose
This feature implements a **Tor-based domain crawler** that starts from one or more seed `.onion` URLs and recursively explores their hyperlinks to **discover additional `.onion` domains**. These domains are then collected and sent to an external automation pipeline (n8n) for further processing, analysis, or enrichment.

---

## 🎯 Objective
Build a **recursive crawler script** that:
- Connects through the **Tor network** via SOCKS5 proxy (`127.0.0.1:9050`)
- Sends HTTP GET requests to `.onion` websites
- Parses the returned HTML for embedded `.onion` links
- Resolves and normalizes URLs
- Recursively visits newly found links up to a defined depth (e.g. 2)
- Outputs a de-duplicated set of `.onion` domains
- Sends the results to an n8n **Webhook URL** as a JSON payload

---

## 📡 Why This Is Needed (Automation Context)
This crawler forms the **foundation of an OSINT pipeline** that:
- Actively discovers **hidden services** on the dark web
- Maps `.onion` networks that are not indexed
- Provides data for follow-up analysis (e.g., scraping marketplaces, forums, or paste sites)
- Supports broader goals like **threat actor tracking**, **IOC extraction**, and **dark web threat intelligence**

---

## 🔁 Input & Output
- **Input:** List of seed `.onion` domains
- **Output:** JSON array of discovered `.onion` domains
- **Trigger:** Can be run manually or via schedule (e.g., cron or n8n trigger)
- **Transmission:** Pushes data to a webhook on the cloud via HTTP POST request

---

## 🛠️ Execution Dependencies
- Python 3
- `requests[socks]` (for Tor proxy)
- `beautifulsoup4` (for HTML parsing)
- Local Tor daemon running with SOCKS5 port enabled (default: `127.0.0.1:9050`)

---

## ✅ Success Criteria
- At least one new `.onion` link is found from seed URLs
- Output is pushed to a valid n8n Webhook endpoint
- Errors are gracefully handled (timeouts, bad URLs, Tor connection issues)
- The crawler avoids revisiting URLs and respects a recursion depth limit
