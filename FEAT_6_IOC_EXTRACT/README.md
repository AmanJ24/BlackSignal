# Feature 6: IOC Extraction with Regex

**Author:** Aman
**Date:** 2025-07-30

## 1. Description

This feature provides a powerful IOC (Indicator of Compromise) extraction engine using comprehensive regex patterns. It is designed to parse raw text from various sources—such as forum posts, chat logs, intelligence reports, or scraped web content—and identify multiple types of IOCs.

The script is lightweight, efficient, and easily extensible to support new IOC patterns.

## 2. Key Features

- **Comprehensive IOC Coverage**: Extracts a wide range of IOCs, including:
  - Network Indicators: IPv4, IPv6, URLs, Domains, `.onion` addresses
  - Cryptocurrency: Bitcoin (BTC) and Ethereum (ETH) addresses
  - File Hashes: MD5, SHA1, SHA256
  - PII: Emails, Phone Numbers, Credit Card Numbers, SSNs
  - System Artifacts: Windows Registry Keys, File Paths
  - Security Identifiers: CVEs, MAC Addresses
- **Advanced Validation**: Implements post-extraction checks to reduce false positives (e.g., filtering out private IP ranges, weak hashes, and common non-domain strings).
- **Webhook Integration**: Sends structured JSON output to a pre-configured n8n webhook for seamless integration into the OSINT pipeline.
- **Rich Metadata**: Enriches the output with timestamps, statistics (total IOCs, counts per type), and samples for better context.
- **Configurable & Extensible**: Uses a central `config.py` for managing webhook URLs and other settings. New regex patterns can be easily added.
- **Logging**: Detailed logging to `../logs/ioc_extractor.log` for monitoring and debugging.

## 3. How It Works

The script follows a simple four-step process:

1.  **Compile Patterns**: Initializes a dictionary of compiled regex patterns for efficiency.
2.  **Extract**: Scans the input text with all patterns to find potential matches.
3.  **Validate**: Filters the raw matches to remove common false positives.
4.  **Enrich & Send**: Packages the valid IOCs into a structured JSON object with metadata and sends it to the configured webhook.

## 4. Dependencies

- `requests`: For sending data to the n8n webhook.

Install dependencies with:
```bash
pip install -r requirements.txt
```

## 5. Setup and Configuration

1. **Configure Webhook URL**
   ```bash
   # Edit webhook_config.py
   nano webhook_config.py
   
   # Replace YOUR_N8N_WEBHOOK_URL_HERE with your actual n8n webhook URL
   # Example: https://your-n8n-instance.app.n8n.cloud/webhook-test/ioc-extract
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Use the IOCExtractor Class**
   ```python
   from ioc_extractor import IOCExtractor
   
   extractor = IOCExtractor()
   results = extractor.process_text(your_text_data)
   ```

## 6. Webhook Output Format

The script sends a POST request to the n8n webhook with a JSON payload in the following format:

```json
{
  "timestamp": "2025-07-30T18:04:46Z",
  "total_iocs": 10,
  "ioc_types_found": ["email", "ipv4", "bitcoin", ...],
  "iocs": {
    "email": ["admin@darkmarket.onion", "backup@evil-corp.com"],
    "ipv4": ["203.0.113.42"],
    "bitcoin": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
    ...
  },
  "statistics": {
    "email": {
      "count": 2,
      "unique_count": 2,
      "sample": ["admin@darkmarket.onion", "backup@evil-corp.com"]
    },
    ...
  }
}
```

