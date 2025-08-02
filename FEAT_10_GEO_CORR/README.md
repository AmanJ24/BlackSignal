# 🌐 Feature 10: Geolocation Correlation

**Directory:** `GEO_CORR_FEAT_10/`
**Status:** 🚧 In Progress

## 🎯 What It Does

This feature matches infrastructure and actor details to geolocation/IP metadata to identify potential risks:
- **Enhanced Geolocation Analysis**: Cross-references geographic data with actor behavior
- **IP Correlation**: Links IP geolocation to known threat activities

## 🔧 How It Works

1. **Input**: IP addresses from Infrastructure Mapping (Feature 9)
2. **Enrichment**: Queries multiple geolocation APIs (IP-API, BGPView, Shodan)
3. **Analysis**: Correlates location information to suspect patterns
4. **Output**: Structured JSON with enhanced geolocation insights

## 📊 API Data Sources

| API       | Purpose                     | Status                  |
|-----------|-----------------------------|-------------------------|
| **IP-API**| Geolocation data            | 🔑 API Key Required      |
| **BGPView** | ASN info, network routing  | ✅ Free (No Key)         |
| **Shodan** | Network scan, IP geolocation | 🔑 API Key Required      |

## 🚀 Usage

### Basic Usage
```python
from geolocation_correlator import GeolocationCorrelator

# Initialize with API keys
correlator = GeolocationCorrelator(
    ipapi_api_key="your_ipapi_key",
    shodan_api_key="your_shodan_key"
)

# Correlate single IP
result = correlator.correlate_geolocation("8.8.8.8")
print(f"Geolocation: {result['analysis']['geolocation']}")
```

### Testing
```bash
# Run test script with mock IP data
python3 test_geolocation_correlator.py
```

## 📁 Files Overview

- **`geolocation_correlator.py`**: Main correlation class with API integration
- **`test_geolocation_correlator.py`**: Test script for function validation
- **`example_data.json`**: Mock input data
- **`requirements.txt`**: Python dependencies

## 📋 Next Steps

1. **Add Real API Keys** - Set up API keys in environment
2. **Implement n8n Webhook** - Automate data flow
3. **Integrate with Pipeline** - Consume data from Feature 9
4. **Enhance Analysis** - Develop complex geographic patterns assessment

## 🔗 Integration with Other Features

**Input Sources:**
- Feature 9: Infrastructure Mapping (IP addresses)

---

**Status**: In progress, requires coding and API integration.
**Last Updated**: 2025-08-01 
**Author**: OSINT Pipeline Project
