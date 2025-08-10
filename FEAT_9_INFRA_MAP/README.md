# 🏗️ Feature 9: Infrastructure Mapping

**Directory:** `INFRA_MAP_FEAT_9/`  
**Status:** ✅ COMPLETED with Mock Data  
**Integration:** Ready for n8n webhook + API key integration

## 🎯 What It Does

This feature correlates IPs and domains to detect:
- **C2 Infrastructure**: Command & Control servers
- **VPN Exit Nodes**: Anonymization services  
- **Bulletproof Hosting**: Malicious hosting providers
- **Threat Actor Infrastructure**: Associated network resources

## 🔧 How It Works

1. **Input**: IP addresses from other pipeline features (IOC extraction, marketplace scraping, etc.)
2. **Enrichment**: Queries multiple threat intelligence APIs
3. **Analysis**: Risk scoring based on infrastructure patterns
4. **Output**: Structured JSON with risk assessment and recommendations

## 📊 API Data Sources

| API | Purpose | Status |
|-----|---------|--------|
| **Shodan** | Port scanning, service detection, vulnerabilities | 🔑 API Key Required |
| **AbuseIPDB** | Abuse reports, reputation scoring | 🔑 API Key Required |
| **BGPView** | ASN info, network allocation, routing | ✅ Free (No Key) |

## 🚀 Usage

### Basic Usage
```python
from infrastructure_mapper import InfrastructureMapper

# Initialize with API keys
mapper = InfrastructureMapper(
    shodan_api_key="your_shodan_key",
    abuseipdb_api_key="your_abuseipdb_key"
)

# Map single IP
result = mapper.map_infrastructure("8.8.8.8")
print(f"Risk Score: {result['analysis']['risk_score']}")
```

### Process Sample Data
```python
# Process batch of IPs from sample data
results = mapper.process_sample_data("sample_data.json")
print(f"Processed {len(results)} IP addresses")
```

### Testing (Mock Mode)
```bash
# Run test script with mock data
python3 test_infrastructure_mapper.py
```

## 📁 Files Overview

- **`infrastructure_mapper.py`**: Main mapping class with API integration
- **`test_infrastructure_mapper.py`**: Comprehensive test script
- **`sample_data.json`**: Sample input data from other features
- **`infrastructure_mapping_results.json`**: Example output results
- **`requirements.txt`**: Python dependencies

## 🔍 Output Structure

```json
{
  "ip_address": "8.8.8.8",
  "timestamp": "2025-07-31T14:37:37.689997",
  "data_sources": ["shodan", "abuseipdb", "bgpview"],
  "analysis": {
    "risk_score": 10,
    "risk_factors": ["Hosting/Data center IP"],
    "infrastructure_type": "hosting/datacenter",
    "geolocation": {
      "country": "US",
      "isp": "Mock ISP",
      "usage_type": "Data Center/Web Hosting/Transit"
    },
    "recommendations": ["Low risk IP"]
  },
  "shodan": { /* Shodan API data */ },
  "abuseipdb": { /* AbuseIPDB API data */ },
  "bgpview": { /* BGPView API data */ }
}
```

## 🎯 Risk Scoring Logic

| Risk Level | Score Range | Criteria |
|------------|-------------|----------|
| **Low** | 0-25 | Clean reputation, standard infrastructure |
| **Medium** | 26-50 | Some risk factors, hosting/VPN usage |  
| **High** | 51-100 | Multiple abuse reports, suspicious ports, known C2 |

### Risk Factors
- **High Abuse Confidence** (+50 points)
- **Suspicious Ports Open** (+15 points per port)
- **Known Vulnerabilities** (+10 points per CVE)
- **Hosting/Data Center** (+10 points)

## 🌐 n8n Webhook Integration

**Webhook URL:** `https://sipiv63984.app.n8n.cloud/webhook-test/infra-mapping`

**Payload Structure:**
```json
{
  "feature": "infrastructure_mapping",
  "data": { /* Full mapping result */ },
  "summary": {
    "ip": "8.8.8.8",
    "risk_score": 10,
    "risk_level": "low",
    "infrastructure_type": "hosting/datacenter"
  }
}
```

## 🔑 API Key Setup

### Shodan API
1. Register at: https://account.shodan.io/register
2. Get free API key (100 queries/month)
3. Add to environment: `SHODAN_API_KEY=your_key`

### AbuseIPDB API  
1. Register at: https://www.abuseipdb.com/register
2. Get free API key (1000 queries/day)
3. Add to environment: `ABUSEIPDB_API_KEY=your_key`

## 🧪 Testing Results

**Test Summary:**
- ✅ 10 IP addresses processed successfully
- ✅ Mock data generation working
- ✅ Risk analysis algorithm functional
- ✅ JSON output properly structured
- ✅ Webhook integration ready

**Mock Data Test:**
```bash
🚀 Testing Infrastructure Mapping Feature 9
==================================================
✅ Successfully processed 10 IP addresses
📈 Summary Report:
Total IPs processed: 10
🔴 High risk IPs: 0
🟡 Medium risk IPs: 0  
🟢 Low risk IPs: 10
💾 Results saved to: infrastructure_mapping_results.json
```

## 🔗 Integration with Other Features

**Input Sources:**
- Feature 6: IOC Extraction (IP addresses)
- Feature 3: Marketplace Scraping (extracted IPs)
- Feature 2: Onion Crawling (exit node IPs)
- Feature 5: STIX/TAXII Feeds (threat IPs)

**Output Consumers:**
- Feature 10: Geolocation Correlation
- Feature 11: Handle Correlation  
- Feature 14: MITRE ATT&CK Mapping

## 📋 Next Steps

1. **Add Real API Keys** - Replace mock data with live API responses
2. **Configure n8n Webhook** - Set up automated data forwarding
3. **Integrate with Pipeline** - Connect to other features
4. **Set Up Monitoring** - Automated alerts for high-risk IPs
5. **Enhance Analysis** - Add more sophisticated risk algorithms

## 🚨 Security Notes

- Store API keys in environment variables, never in code
- Implement rate limiting to avoid API quota exhaustion
- Log all high-risk IP detections for security monitoring
- Consider implementing caching to reduce API calls
- Monitor for false positives in risk scoring

---

**Status**: Ready for production with API keys  
**Last Updated**: 2025-07-31  
**Author**: OSINT Pipeline Project
