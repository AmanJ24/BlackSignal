#!/usr/bin/env python3
"""
Feature 4: API Enrichment (Local Version)
Enriches various Indicators of Compromise (IOCs) using free-tier threat 
intelligence APIs and saves the results to a local JSON file.
"""

import sys
import os
import requests
import json
import logging
import time
import re
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import get_api_key
except ImportError:
    # Fallback if config.py is not found
    def get_api_key(key_name):
        return os.environ.get(key_name.upper() + "_API_KEY")

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'api_enrichment.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Configuration ---
API_ENDPOINTS = {
    'ip_api': 'http://ip-api.com/json/',
    'bgpview_ip': 'https://api.bgpview.io/ip/',
    'abuseipdb': 'https://api.abuseipdb.com/api/v2/check',
    'virustotal_v2': 'https://www.virustotal.com/vtapi/v2/file/report', # Kept for compatibility
    'otx_ip': 'https://otx.alienvault.com/api/v1/indicators/IPv4/',
    'otx_domain': 'https://otx.alienvault.com/api/v1/indicators/domain/',
    'otx_hash': 'https://otx.alienvault.com/api/v1/indicators/file/',
}

RATE_LIMITS = {
    'ip_api': 1.5,
    'bgpview': 1.5,
    'abuseipdb': 2,
    'virustotal': 16,  # 4 requests/min = 15s, add a buffer
    'otx': 1.5
}

class APIEnricher:
    """Enriches IOCs by querying various threat intelligence APIs."""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        self.api_keys = api_keys or {}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'OSINT-Pipeline-Enricher/1.0'})
        
    def enrich_ip(self, ip: str) -> Dict:
        """Enriches an IP address using multiple free-tier APIs."""
        results = {'ioc': ip, 'ioc_type': 'ip', 'enrichment_timestamp': datetime.now().isoformat()}
        
        # --- IP-API (Geolocation) ---
        try:
            time.sleep(RATE_LIMITS['ip_api'])
            response = self.session.get(f"{API_ENDPOINTS['ip_api']}{ip}", timeout=10)
            if response.ok and response.json().get('status') == 'success':
                data = response.json()
                results['ip_api'] = {k: data.get(k) for k in ['country', 'regionName', 'city', 'isp', 'org']}
        except requests.RequestException as e:
            logger.error(f"IP-API query failed for {ip}: {e}")

        # --- BGPView (Network Info) ---
        try:
            time.sleep(RATE_LIMITS['bgpview'])
            response = self.session.get(f"{API_ENDPOINTS['bgpview_ip']}{ip}", timeout=10)
            if response.ok and response.json().get('status') == 'ok':
                data = response.json().get('data', {})
                results['bgpview'] = {'asn': data.get('asn'), 'description': data.get('description_short')}
        except requests.RequestException as e:
            logger.error(f"BGPView query failed for {ip}: {e}")

        # --- AbuseIPDB (Abuse Score) ---
        if 'abuseipdb' in self.api_keys:
            try:
                time.sleep(RATE_LIMITS['abuseipdb'])
                headers = {'Key': self.api_keys['abuseipdb'], 'Accept': 'application/json'}
                params = {'ipAddress': ip, 'maxAgeInDays': '90'}
                response = self.session.get(API_ENDPOINTS['abuseipdb'], headers=headers, params=params, timeout=10)
                if response.ok and 'data' in response.json():
                    data = response.json()['data']
                    results['abuseipdb'] = {'abuse_score': data.get('abuseConfidenceScore'), 'usage_type': data.get('usageType')}
            except requests.RequestException as e:
                logger.error(f"AbuseIPDB query failed for {ip}: {e}")
        
        return results
        
    def enrich_domain(self, domain: str) -> Dict:
        """Enriches a domain using OTX."""
        results = {'ioc': domain, 'ioc_type': 'domain', 'enrichment_timestamp': datetime.now().isoformat()}
        
        # --- OTX (AlienVault) ---
        try:
            time.sleep(RATE_LIMITS['otx'])
            response = self.session.get(f"{API_ENDPOINTS['otx_domain']}{domain}/general", timeout=10)
            if response.ok:
                data = response.json()
                results['otx'] = {'pulse_count': len(data.get('pulse_info', {}).get('pulses', []))}
        except requests.RequestException as e:
            logger.error(f"OTX query failed for domain {domain}: {e}")
        
        return results
        
    def enrich_hash(self, hash_value: str) -> Dict:
        """Enriches a file hash using VirusTotal and OTX."""
        results = {'ioc': hash_value, 'ioc_type': 'hash', 'enrichment_timestamp': datetime.now().isoformat()}
        
        # --- VirusTotal ---
        if 'virustotal' in self.api_keys:
            try:
                time.sleep(RATE_LIMITS['virustotal'])
                params = {'apikey': self.api_keys['virustotal'], 'resource': hash_value}
                response = self.session.get(API_ENDPOINTS['virustotal_v2'], params=params, timeout=15)
                if response.ok and response.json().get('response_code') == 1:
                    data = response.json()
                    results['virustotal'] = {'positives': data.get('positives', 0), 'total': data.get('total', 0)}
            except requests.RequestException as e:
                logger.error(f"VirusTotal query failed for hash {hash_value}: {e}")

        # --- OTX (AlienVault) ---
        try:
            time.sleep(RATE_LIMITS['otx'])
            response = self.session.get(f"{API_ENDPOINTS['otx_hash']}{hash_value}/general", timeout=10)
            if response.ok:
                data = response.json()
                results['otx'] = {'pulse_count': len(data.get('pulse_info', {}).get('pulses', []))}
        except requests.RequestException as e:
            logger.error(f"OTX query failed for hash {hash_value}: {e}")
            
        return results

def save_results(data: List[Dict]):
    """Saves the enriched data to a JSON file in the 'output' directory."""
    if not data:
        logger.warning("No enriched data to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_4_api_enrichment.json')
        
        final_payload = {
            "feature_name": "API Enrichment",
            "execution_timestamp": datetime.now().isoformat(),
            "iocs_enriched": len(data),
            "enriched_results": data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

def main():
    """Main execution function for API enrichment."""
    logger.info("🚀 Starting Feature 4: API Enrichment...")
    
    # In a real pipeline, these IOCs would come from a previous step's output file.
    # For this standalone script, we define a sample set.
    test_iocs = {
        'ips': ['8.8.8.8', '1.1.1.1', '185.220.101.43'], # Google, Cloudflare, known malicious
        'domains': ['google.com', 'evil-site.net'],
        'hashes': ['275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f'] # WannaCry hash
    }
    
    # Load API keys from config or environment variables
    api_keys = {
        'abuseipdb': get_api_key('abuseipdb'),
        'virustotal': get_api_key('virustotal'),
    }
    api_keys = {k: v for k, v in api_keys.items() if v}
    
    enricher = APIEnricher(api_keys)
    all_enriched_results = []
    
    logger.info("--- Enriching IP Addresses ---")
    for ip in test_iocs['ips']:
        logger.info(f"Enriching IP: {ip}")
        all_enriched_results.append(enricher.enrich_ip(ip))
    
    logger.info("--- Enriching Domains ---")
    for domain in test_iocs['domains']:
        logger.info(f"Enriching domain: {domain}")
        all_enriched_results.append(enricher.enrich_domain(domain))
    
    logger.info("--- Enriching Hashes ---")
    for hash_val in test_iocs['hashes']:
        logger.info(f"Enriching hash: {hash_val}")
        all_enriched_results.append(enricher.enrich_hash(hash_val))
    
    if all_enriched_results:
        save_results(all_enriched_results)
    else:
        logger.warning("No IOCs were enriched.")
        
    logger.info("✅ API Enrichment finished successfully.")

if __name__ == "__main__":
    main()
