#!/usr/bin/env python3
"""
Feature 10: Geolocation Correlation (Local Version)

This module correlates IP addresses with geolocation data to identify patterns
and potential threats based on geographic distribution. It saves the results
to a local JSON file.
"""

import sys
import os
import requests
import json
import socket
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import get_api_key
except ImportError:
    def get_api_key(key_name):
        return None

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'geolocation_correlation.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeolocationCorrelator:
    """Correlates IP addresses with geolocation data."""
    
    IPAPI_URL = "http://ip-api.com/json/"
    HIGH_RISK_COUNTRIES = ['RU', 'CN', 'KP', 'IR'] # Example list
    VPN_PROVIDERS = ['nordvpn', 'expressvpn', 'private internet access', 'cyberghost']

    def __init__(self, use_mock_data: bool = False):
        self.use_mock_data = use_mock_data
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'OSINT-Pipeline-GeoCorrelator/1.0'})

    def _is_valid_ip(self, ip_address: str) -> bool:
        """Validates if a string is a correct IPv4 address."""
        try:
            socket.inet_aton(ip_address)
            return True
        except socket.error:
            return False

    def correlate_ip(self, ip_address: str) -> Dict[str, Any]:
        """Correlates geolocation data for a single IP address."""
        if not self._is_valid_ip(ip_address):
            logger.warning(f"Invalid IP address format, skipping: {ip_address}")
            return {"ip_address": ip_address, "error": "Invalid IP format"}

        if self.use_mock_data:
            logger.info(f"Using mock data for IP: {ip_address}")
            return self._get_mock_data(ip_address)
            
        result = {'ip_address': ip_address, 'timestamp': datetime.now().isoformat()}
        
        try:
            time.sleep(1.5) # Rate limit
            response = self.session.get(f"{self.IPAPI_URL}{ip_address}", timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'success':
                result['geolocation'] = {
                    'country_code': data.get('countryCode'),
                    'country_name': data.get('country'),
                    'city': data.get('city'),
                    'isp': data.get('isp'),
                    'org': data.get('org')
                }
                result['analysis'] = self._analyze_geolocation(result['geolocation'])
            else:
                result['error'] = data.get('message', 'Failed to geolocate IP')

        except requests.RequestException as e:
            logger.error(f"API query failed for {ip_address}: {e}")
            result['error'] = str(e)
            
        return result

    def _analyze_geolocation(self, geo_data: Dict) -> Dict:
        """Analyzes the collected geolocation data for risk factors."""
        analysis = {"risk_factors": []}
        
        # High-risk country check
        country_code = geo_data.get('country_code')
        if country_code and country_code in self.HIGH_RISK_COUNTRIES:
            analysis['risk_factors'].append(f"Located in high-risk country: {country_code}")
            
        # VPN/Proxy provider check
        isp_name = geo_data.get('isp', '').lower()
        if any(vpn in isp_name for vpn in self.VPN_PROVIDERS):
            analysis['risk_factors'].append("ISP is a known VPN/Proxy provider.")
            
        if not analysis['risk_factors']:
            analysis['risk_factors'].append("No obvious geographic risk factors detected.")
            
        return analysis

    def _get_mock_data(self, ip_address: str) -> Dict:
        """Generates mock data for testing."""
        is_risky = ip_address.startswith("195")
        mock = {
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat(),
            "data_sources": ["mock_ipapi"],
            "geolocation": {
                "country_code": "RU" if is_risky else "US",
                "country_name": "Russia" if is_risky else "United States",
                "city": "Moscow" if is_risky else "Mountain View",
                "isp": "Mock Hosting Provider" if is_risky else "Google LLC",
                "org": "Mock Org" if is_risky else "Google"
            }
        }
        mock['analysis'] = self._analyze_geolocation(mock['geolocation'])
        return mock

def save_results(data: List[Dict]):
    """Saves the correlation results to a JSON file."""
    if not data:
        logger.warning("No correlation results to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_10_geolocation_correlation.json')
        
        final_payload = {
            "feature_name": "Geolocation Correlation",
            "execution_timestamp": datetime.now().isoformat(),
            "ips_analyzed": len(data),
            "correlation_results": data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

def main():
    """Main execution function for the Geolocation Correlator."""
    logger.info("🚀 Starting Feature 10: Geolocation Correlation...")
    
    # In a real pipeline, this would come from a file (e.g., IOC extractor output)
    sample_ips = ["8.8.8.8", "1.1.1.1", "195.154.225.107", "89.248.167.143"]  # Google, Cloudflare, Russia, NordVPN
    
    # Using mock data if API keys for other services are not present
    # This feature itself doesn't need a key, but we can use the existence of other keys to decide
    use_mock = not get_api_key("shodan") 
    
    correlator = GeolocationCorrelator(use_mock_data=use_mock)
    
    all_results = []
    logger.info(f"Analyzing {len(sample_ips)} IPs...")
    
    for ip in sample_ips:
        logger.info(f"--- Correlating IP: {ip} ---")
        result = correlator.correlate_ip(ip)
        all_results.append(result)
        print(json.dumps(result, indent=2))
        
    if all_results:
        save_results(all_results)
    
    logger.info("✅ Geolocation correlation complete.")

if __name__ == "__main__":
    main()
