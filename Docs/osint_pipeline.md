# 🕵️ OSINT + Threat Intel Automation Pipeline (Free-Tier Version)

This project automates 15 core features for dark web monitoring, threat intelligence extraction, and threat actor profiling using **n8n**, **Python**, and **Free/Public APIs** only.

---

## 📦 Feature-wise Breakdown

Each section includes:

- ✅ What the feature does
- 🧰 Required tools/libraries
- 🔧 Implementation strategy (code + n8n)
- 🔗 API/webhook integration

---

### 1. **Tor Relay Enumeration**

**What It Does:**  
Discovers active Tor relays (entry/middle/exit) using Tor control protocol.

**Required Tools:**
- `Tor` (Running locally)
- `stem` (Python lib)
- `Flask` (to serve API)
- `n8n webhook`

**How to Implement:**
- Use Python with `stem.Controller` to fetch relay info.
- Serve data on `/relays` endpoint via Flask.
- Push data to n8n using HTTP Request node.

---

### 2. **Automated .onion Domain Discovery**

**What It Does:**  
Crawls known `.onion` domains, discovers other hidden services recursively.

**Required Tools:**
- `Tor SOCKS5 Proxy`
- `requests`, `BeautifulSoup`
- `Flask` for webhook integration

**How to Implement:**
- Start with seed URLs.
- Crawl pages via Tor.
- Extract new `.onion` links.
- Send results to n8n webhook for tracking.

---

### 3. **Hidden Services Marketplace Scraping**

**What It Does:**  
Scrapes listings from darknet marketplaces for vendor, BTC, and product info.

**Required Tools:**
- `BeautifulSoup`
- `requests` via Tor proxy
- `Flask` + `n8n webhook`

**How to Implement:**
- Scrape listing pages.
- Extract title, author, price, BTC address.
- Format data as JSON and send to n8n.

---

### 4. **API Enrichment (Free-tier APIs)**

**What It Does:**  
Enriches scraped data using free threat intelligence APIs.

**Required APIs:**
- [OTX](https://otx.alienvault.com)
- [Shodan](https://shodan.io)
- [AbuseIPDB](https://abuseipdb.com)
- [VirusTotal](https://www.virustotal.com)
- [IP-API](http://ip-api.com)
- [BGPView](https://bgpview.io/api)

**How to Implement:**
- Extract indicators (IP, BTC, hash) in n8n code node.
- Call external APIs using HTTP Request.
- Merge enriched data for further analysis.

---

### 5. **STIX/TAXII Feed Parsing**

**What It Does:**  
Fetches threat intel feeds from free MISP/CIRCL and parses into n8n-compatible format.

**Required Tools:**
- CIRCL’s TAXII STIX feeds
- `n8n HTTP Request` + JSON/CSV parsing nodes

**How to Implement:**
- Pull feed URLs.
- Parse JSON or XML feeds.
- Normalize IOCs to same structure as rest of pipeline.

---

### 6. **IOC Extraction with Regex**

**What It Does:**  
Uses regex to pull out emails, IPs, hashes, BTC addresses from raw data.

**Required Tools:**
- Python `re` OR `n8n code node (JS)`
- Patterns for BTC, SHA256, Email

**How to Implement:**
- Apply regex match on scraped/enriched data.
- Append findings as new keys in n8n.

---

### 7. **Named Entity Recognition (NER)**

**What It Does:**  
Detects handles, names, organization names from scraped content.

**Required Tools:**
- `spaCy` (`en_core_web_sm`)
- `Flask` API (if doing externally)

**How to Implement:**
- Pass content to spaCy.
- Extract PERSON/ORG/NORP entities.
- Return as JSON to n8n for tagging.

---

### 8. **Hash Extraction (Malware IOCs)**

**What It Does:**  
Identifies file hashes (MD5/SHA256) from scraped logs or dumps.

**Required Tools:**
- Regex in `Python` or `n8n`
- Enrichment via `VirusTotal`

**How to Implement:**
- Regex extract hash patterns.
- Lookup in VirusTotal.
- Add threat score or signature name.

---

### 9. **Infrastructure Mapping**

**What It Does:**  
Correlates IPs/domains to detect C2, VPN exit, or bulletproof hosting.

**Required APIs:**
- Shodan (Free)
- AbuseIPDB
- BGPView
- Passive DNS (optional)

**How to Implement:**
- Input domain/IP into APIs.
- Use n8n to log location, ISP, and ASN details.

---

### 10. **Geolocation Correlation**

**What It Does:**  
Matches infrastructure and actor details to geolocation/IP metadata.

**Tools:**
- `IP-API.com`
- `BGPView`
- `Shodan`

**How to Implement:**
- Query IPs via HTTP node.
- Map ASN, location, network owner fields.

---

### 11. **Handle Correlation**

**What It Does:**  
Cross-matches scraped actor handles across marketplaces.

**Tools:**
- Store usernames in n8n
- Compare new handles with existing memory

**How to Implement:**
- Use n8n Code node to compare current usernames to previous workflows.
- Flag as known/unknown.

---

### 12. **Behavioral Analysis**

**What It Does:**  
Detects patterns from vendor posts — sentiment, frequency, writing style.

**Tools:**
- `TextBlob` (Free)
- `Vader` (Optional)

**How to Implement:**
- Analyze titles/descriptions.
- Run sentiment score or frequency analysis in Python.
- Send to n8n for flagging risk levels.

---

### 13. **Reputation Scoring**

**What It Does:**  
Assigns score to each vendor based on feedback, BTC reuse, profile mentions.

**How to Implement:**
- Score = 10 (New) → 90 (Known affiliate)
- Add logic in n8n Code Node to weight score from scraped params

---

### 14. **MITRE ATT&CK TTP Mapping**

**What It Does:**  
Links behavior and findings to MITRE techniques.

**Tools:**
- MITRE ATT&CK JSON
- Keyword matching logic

**How to Implement:**
- Download MITRE dataset locally
- Match listing description against TTPs
- Return matches to n8n

---

### 15. **Affiliate Recruitment/Payment Analysis**

**What It Does:**  
Detects RaaS structure — BTC reuse, affiliate referrals, promo posts.

**Tools:**
- BTC pattern matches
- Handle reuse logic
- Custom parser

**How to Implement:**
- Analyze pricing, BTC, and author metadata
- Score if author mentions “affiliate”, “partner”, etc.

---

## 🧰 Summary of Free Tools

| Tool | Type |
|------|------|
| Tor, Stem | Network |
| Flask, Requests, BeautifulSoup | Python Web |
| n8n Cloud (limited) | Workflow automation |
| VirusTotal, OTX, AbuseIPDB | API enrichment |
| spaCy, TextBlob | NLP |
| CIRCL / MISP | TAXII feeds |
| Shodan (free) | Infra scan |
| IP-API / BGPView | IP metadata |

---

## ✅ Deployment Advice

- Local test via Flask → Send to n8n webhook
- Format + enrich in n8n
- Expand to DB/storage later

---

Let’s build this block by block!
