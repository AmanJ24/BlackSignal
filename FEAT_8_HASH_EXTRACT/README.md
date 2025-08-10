# 🚀 Hash Extraction (Malware IOCs) - Feature 8

**Feature Status**: ✅ **COMPLETED**

## Overview
This feature extracts MD5, SHA1, and SHA256 hashes from collected dark web data and enriches them with threat intelligence using VirusTotal API.

## 🎯 Capabilities
- **Hash Extraction**: Identifies MD5, SHA1, SHA256 hashes using regex patterns
- **VirusTotal Integration**: Enriches hashes with malware detection scores
- **Multi-source Processing**: Handles data from all OSINT pipeline features
- **n8n Integration**: Sends structured results to webhook
- **Error Handling**: Graceful handling of API limits and missing keys

## 📊 Test Results
Successfully processed 5 test samples and extracted:
- **8 unique hashes** (MD5: 3, SHA1: 3, SHA256: 2)
- **100% accuracy** in hash pattern detection
- **Robust error handling** for missing API keys

## 🔗 Integration Points
- **Input**: Receives data from Features 1-7 via JSON format
- **Output**: Sends enriched hash data to n8n webhook
- **Webhook URL**: `https://sipiv63984.app.n8n.cloud/webhook-test/hash-extract`

## 🚨 Security Features
- **Rate Limiting**: 15-second delays between VirusTotal requests
- **API Key Protection**: Environment variable configuration
- **Input Validation**: Regex-based hash validation
- **Error Reporting**: Detailed status for each hash query

## 📋 Usage
```bash
# Activate virtual environment
source ../venv_ner/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run hash extraction
python hash_extractor.py
```

## 🔧 Configuration
- **VirusTotal API**: Set `VIRUSTOTAL_API_KEY` in environment
- **Webhook URL**: Configured via `config.py`
- **Input Data**: Place JSON data in `sample_hash_data.json`

## 📈 Next Steps
Ready for integration with Features 9-15 for:
- Infrastructure mapping
- Geolocation correlation  
- Threat actor profiling
- MITRE ATT&CK mapping
