#!/usr/bin/env python3
"""
Feature 9: Infrastructure Mapping (Local Version)

Correlates IP addresses with data from Shodan, AbuseIPDB, and BGPView
to build a comprehensive infrastructure profile and risk assessment.
Saves the results to a local JSON file.
"""

import sys
import os
import requests
import json
import socket
import time
import logging
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import get_api_key
except ImportError:
    def get_api_key(key_name):
        return os.environ.get(key_name.upper() + "_API_KEY")

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'infrastructure_mapper.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InfrastructureMapper:
    """Maps the infrastructure of IP addresses using various APIs."""
    
    API_URLS = {
        "shodan": "https://api.shodan.io/shodan/host/",
        "abuseipdb": "https://api.abuseipdb.com/api/v2/check",
        "bgpview": "https://api.bgpview.io/ip/"
    }
    
    def __init__(self, shodan_api_key: str = None, abuseipdb_api_key: str = None):
        self.shodan_key = shodan_api_key
        self.abuseipdb_key = abuseipdb_api_key
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'OSINT-Pipeline-InfraMapper/1.0'})

    def _query_api(self, url: str, headers: Dict = None, params: Dict = None) -> Optional[Dict]:
        """Generic function to query an API with error handling."""
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API query failed for {url}: {e}")
            return None

    def map_ip(self, ip_address: str) -> Dict[str, Any]:
        """Maps infrastructure for a single IP address."""
        if not self._is_valid_ip(ip_address):
            logger.warning(f"Invalid IP address format: {ip_address}")
            return {"ip_address": ip_address, "error": "Invalid IP address"}

        result = {'ip_address': ip_address, 'timestamp': datetime.now().isoformat()}
        
        # --- BGPView (Free) ---
        time.sleep(1) # Rate limit
        bgp_data = self._query_api(f"{self.API_URLS['bgpview']}{ip_address}")
        if bgp_data and bgp_data.get('status') == 'ok':
            result['bgpview'] = bgp_data['data']

        # --- Shodan (API Key Required) ---
        if self.shodan_key:
            time.sleep(1) # Rate limit
            shodan_data = self._query_api(f"{self.API_URLS['shodan']}{ip_address}", params={'key': self.shodan_key})
            if shodan_data:
                result['shodan'] = {
                    'ports': shodan_data.get('ports'), 'os': shodan_data.get('os'),
                    'isp': shodan_data.get('isp'), 'org': shodan_data.get('org'),
                    'vulns': shodan_data.get('vulns')
                }

        # --- AbuseIPDB (API Key Required) ---
        if self.abuseipdb_key:
            time.sleep(1) # Rate limit
            headers = {'Key': self.abuseipdb_key, 'Accept': 'application/json'}
            params = {'ipAddress': ip_address, 'maxAgeInDays': '90'}
            abuse_data = self._query_api(self.API_URLS['abuseipdb'], headers=headers, params=params)
            if abuse_data and 'data' in abuse_data:
                result['abuseipdb'] = abuse_data['data']
        
        result['analysis'] = self._analyze_infrastructure(result)
        return result

    def _is_valid_ip(self, ip: str) -> bool:
        """Validates if a string is a correct IPv4 address."""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def _analyze_infrastructure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes the collected data to generate a risk profile."""
        analysis = {"risk_score": 0, "risk_factors": []}
        
        # AbuseIPDB analysis
        abuse_data = data.get('abuseipdb', {})
        if abuse_data:
            confidence = abuse_data.get('abuseConfidenceScore', 0)
            if confidence > 80:
                analysis['risk_score'] += 50
                analysis['risk_factors'].append("High abuse confidence score (>80)")
            elif confidence > 25:
                analysis['risk_score'] += 20
                analysis['risk_factors'].append("Moderate abuse confidence score (>25)")
        
        # Shodan analysis
        shodan_data = data.get('shodan', {})
        if shodan_data:
            suspicious_ports = {23, 1080, 4444} # Telnet, SOCKS, common backdoor
            open_ports = set(shodan_data.get('ports', []))
            if any(p in open_ports for p in suspicious_ports):
                analysis['risk_score'] += 25
                analysis['risk_factors'].append("Suspicious ports open (e.g., Telnet, SOCKS)")
            if shodan_data.get('vulns'):
                analysis['risk_score'] += 20
                analysis['risk_factors'].append(f"Known vulnerabilities found: {shodan_data['vulns']}")
        
        # BGPView/hosting analysis
        bgp_data = data.get('bgpview', {})
        if bgp_data:
            description = bgp_data.get('asn', {}).get('description', '').lower()
            hosting_keywords = ['hosting', 'datacenter', 'vps', 'cloud']
            if any(kw in description for kw in hosting_keywords):
                analysis['risk_score'] += 10
                analysis['risk_factors'].append("IP is from a hosting provider, not residential.")
        
        # Final risk level
        if analysis['risk_score'] >= 75:
            analysis['risk_level'] = 'CRITICAL'
        elif analysis['risk_score'] >= 50:
            analysis['risk_level'] = 'HIGH'
        elif analysis['risk_score'] >= 25:
            analysis['risk_level'] = 'MEDIUM'
        else:
            analysis['risk_level'] = 'LOW'
            
        return analysis

def save_results(data: List[Dict]):
    """Saves the infrastructure reports to a JSON file."""
    if not data:
        logger.warning("No infrastructure data to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_9_infrastructure_mapping.json')
        
        final_payload = {
            "feature_name": "Infrastructure Mapping",
            "execution_timestamp": datetime.now().isoformat(),
            "ips_analyzed": len(data),
            "results": data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

if __name__ == "__main__":
    # In a real pipeline, this would come from a file (e.g., IOC extractor output)
    sample_ips = ["8.8.8.8", "1.1.1.1", "91.198.174.192"] # Google, Cloudflare, Wikipedia
    
    shodan_key = get_api_key("shodan")
    abuseipdb_key = get_api_key("abuseipdb")
    
    mapper = InfrastructureMapper(shodan_api_key=shodan_key, abuseipdb_api_key=abuseipdb_key)
    
    all_results = []
    logger.info(f"🚀 Starting infrastructure mapping for {len(sample_ips)} IPs...")
    
    for ip in sample_ips:
        logger.info(f"\n--- Mapping IP: {ip} ---")
        result = mapper.map_ip(ip)
        all_results.append(result)
        print(json.dumps(result, indent=2))
        
    if all_results:
        save_results(all_results)
    else:
        logger.warning("No results were generated.")
        
    logger.info("✅ Infrastructure mapping complete.")
