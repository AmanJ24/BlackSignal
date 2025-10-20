#!/usr/bin/env python3
"""
Feature 10: Geolocation Correlation

This module correlates IP addresses with geolocation data to identify patterns
and potential threats based on geographic distribution.

Author: OSINT Pipeline Project
Created: 2025-08-01
"""

import requests
import json
import socket
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/geolocation_correlation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import config, handle if not available
try:
    from config import get_n8n_webhook_url, get_api_key
    CONFIG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Config module not available: {e}. Using fallback configuration.")
    CONFIG_AVAILABLE = False

class GeolocationCorrelationError(Exception):
    pass

class GeolocationCorrelator:
    # API endpoints
    IPAPI_API_URL = "http://ip-api.com/json/"
    BGPVIEW_API_URL = "https://api.bgpview.io/ip/"
    SHODAN_API_URL = "https://api.shodan.io/shodan/host/"
    
    # High-risk countries for threat intelligence (example list)
    HIGH_RISK_COUNTRIES = ['RU', 'CN', 'KP', 'IR', 'SY', 'AF']
    
    # Known VPN/Proxy providers (lowercased for comparison)
    VPN_PROVIDERS = ['nordvpn', 'expressvpn', 'surfshark', 'private internet access', 
                     'cyberghost', 'tunnelbear', 'hotspot shield', 'windscribe']
    
    # Request timeout and retry configuration
    REQUEST_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    def __init__(self, shodan_api_key: str = None, use_mock_data: bool = False):
        """Initialize GeolocationCorrelator with proper error handling"""
        try:
            if CONFIG_AVAILABLE:
                self.shodan_api_key = shodan_api_key or get_api_key('shodan')
                self.webhook_url = get_n8n_webhook_url('geo-correlation')
            else:
                self.shodan_api_key = shodan_api_key
                self.webhook_url = "https://sipiv63984.app.n8n.cloud/webhook-test/geo-correlation"
                
            self.use_mock_data = use_mock_data
            
            # Check if API key is valid
            if not self.shodan_api_key or self.shodan_api_key == "your_shodan_api_key":
                logger.warning("No valid Shodan API key provided, using mock data")
                self.use_mock_data = True
                
            logger.info(f"GeolocationCorrelator initialized. Mock data: {self.use_mock_data}")
            
        except Exception as e:
            logger.error(f"Error initializing GeolocationCorrelator: {e}")
            self.use_mock_data = True
            self.webhook_url = "https://sipiv63984.app.n8n.cloud/webhook-test/geo-correlation"

    def correlate_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Correlate geolocation data for a given IP address"""
        result = {
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat(),
            'data_sources': []
        }
        
        try:
            # Basic IP validation
            if not self._is_valid_ip(ip_address):
                raise GeolocationCorrelationError(f"Invalid IP address: {ip_address}")

            if self.use_mock_data:
                print(f"🔄 Using mock data for IP: {ip_address}")
                return self._get_mock_data(ip_address)

            # IP-API call (free geolocation service)
            ipapi_data = self.query_ipapi(ip_address)
            if ipapi_data:
                result['ipapi'] = ipapi_data
                result['data_sources'].append('ipapi')

            # BGPView API call (free ASN/network info)
            bgpview_data = self.query_bgpview(ip_address)
            if bgpview_data:
                result['bgpview'] = bgpview_data
                result['data_sources'].append('bgpview')

            # Shodan API call (requires API key)
            if self.shodan_api_key:
                shodan_data = self.query_shodan(ip_address)
                if shodan_data:
                    result['shodan'] = shodan_data
                    result['data_sources'].append('shodan')

            # Comprehensive geolocation analysis
            result['analysis'] = self._analyze_geolocation(result)

        except Exception as e:
            if self.use_mock_data:
                print(f"🔄 API error, using mock data: {e}")
                return self._get_mock_data(ip_address)
            else:
                raise GeolocationCorrelationError(f"Error correlating geolocation: {e}")

        return result

    def query_ipapi(self, ip_address: str) -> Dict[str, Any]:
        response = requests.get(f"{self.IPAPI_API_URL}{ip_address}")
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def query_bgpview(self, ip_address: str) -> Dict[str, Any]:
        response = requests.get(f"{self.BGPVIEW_API_URL}{ip_address}")
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def query_shodan(self, ip_address: str) -> Dict[str, Any]:
        response = requests.get(f"{self.SHODAN_API_URL}{ip_address}",
                                headers={"API-Key": self.shodan_api_key})
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def _get_mock_data(self, ip_address: str) -> Dict[str, Any]:
        """Generate mock data for testing when APIs are not available"""
        mock_data = {
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat(),
            "data_sources": ["mock_ipapi", "mock_bgpview", "mock_shodan"],
            "ipapi": {
                "country": "US",
                "city": "Mock City",
                "isp": "Mock ISP"
            },
            "bgpview": {
                "data": {
                    "ptr_record": f"mock-ptr-{ip_address.replace('.', '-')}.com",
                    "rir_allocation": {
                        "rir_name": "ARIN",
                        "country_code": "US",
                        "date_allocated": "2000-01-01 00:00:00"
                    },
                    "prefixes": [
                        {
                            "prefix": f"{ip_address}/24",
                            "asn": {
                                "asn": 15169,
                                "name": "Mock AS",
                                "description": "Mock AS",
                                "country_code": "US"
                            }
                        }
                    ]
                }
            },
            "shodan": {
                "os": "Linux",
                "ports": [22, 80, 443],
                "isp": "Mock ISP",
                "country_code": "US"
            },
            "analysis": {}
        }
        mock_data["analysis"] = self._analyze_geolocation(mock_data)
        return mock_data

    def _is_valid_ip(self, ip_address: str) -> bool:
        """Validate IP address format"""
        try:
            socket.inet_aton(ip_address)
            return True
        except socket.error:
            return False

    def _analyze_geolocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        analysis = {
            "geolocation": {},
            "risk_factors": [],
            "is_high_risk_country": False
        }

        # Extract geolocation data
        if "ipapi" in data and data["ipapi"]:
            ipapi_data = data["ipapi"]
            country = ipapi_data.get("country", "unknown")
            analysis["geolocation"] = {
                "country": country,
                "city": ipapi_data.get("city", "unknown"),
                "isp": ipapi_data.get("isp", "unknown")
            }

            # High-risk country check
            if country in self.HIGH_RISK_COUNTRIES:
                analysis["is_high_risk_country"] = True
                analysis["risk_factors"].append("Located in high-risk country")

        return analysis


def send_to_webhook(data: List[Dict[str, Any]]):
    """Sends the geolocation analysis results to the n8n webhook."""
    # Use the URL from the class instance if available
    # This handles the case where config might not be loaded
    webhook_url = GeolocationCorrelator().webhook_url
    if not webhook_url:
        logger.warning("Webhook URL for 'geo-correlation' not configured. Skipping.")
        return False
    try:
        payload = {
            "timestamp": datetime.now().isoformat(),
            "feature": "Geolocation Correlation",
            "results_count": len(data),
            "results": data
        }
        response = requests.post(webhook_url, json=payload, timeout=20)
        response.raise_for_status()
        logger.info(f"✅ Successfully sent {len(data)} geolocation reports to webhook.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send data to webhook: {e}")
        return False



# Main Function
if __name__ == "__main__":
    sample_ips = ["8.8.8.8", "104.26.10.231", "195.154.225.107"] # Google, Cloudflare, Russia
    
    # Load API keys from config/environment
    shodan_key = get_api_key("shodan") if CONFIG_AVAILABLE else None
    
    correlator = GeolocationCorrelator(shodan_api_key=shodan_key)
    
    all_results = []
    print(f"🚀 Starting geolocation correlation for {len(sample_ips)} IPs...")
    
    for ip in sample_ips:
        try:
            print(f"\n--- Correlating IP: {ip} ---")
            result = correlator.correlate_geolocation(ip)
            all_results.append(result)
            print(json.dumps(result, indent=2))
            time.sleep(1) # Rate limit
            
        except GeolocationCorrelationError as e:
            print(f"❗️ Could not correlate IP {ip}: {e}")

    if all_results:
        send_to_webhook(all_results)
    else:
        print("No results to send to webhook.")

    print("\n✅ Geolocation correlation complete.")
