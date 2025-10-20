#!/usr/bin/env python3
"""
API Enrichment Feature 4
Enriches IOCs using free threat intelligence APIs
"""

import sys
import requests
import json
import logging
import time
import re
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_n8n_webhook_url, get_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/api_enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
N8N_WEBHOOK_URL = get_n8n_webhook_url('api-enrich')

# Free API endpoints
API_ENDPOINTS = {
    'ip_api': 'http://ip-api.com/json/',
    'bgpview_ip': 'https://api.bgpview.io/ip/',
    'bgpview_asn': 'https://api.bgpview.io/asn/',
    'abuseipdb': 'https://api.abuseipdb.com/api/v2/check',
    'virustotal': 'https://www.virustotal.com/vtapi/v2/file/report',
    'shodan': 'https://api.shodan.io/shodan/host/',
    'otx_ip': 'https://otx.alienvault.com/api/v1/indicators/IPv4/',
    'otx_domain': 'https://otx.alienvault.com/api/v1/indicators/domain/',
    'otx_hash': 'https://otx.alienvault.com/api/v1/indicators/file/',
}

# Rate limiting delays (seconds)
RATE_LIMITS = {
    'ip_api': 1,
    'bgpview': 1,
    'abuseipdb': 1,
    'virustotal': 15,  # VT has strict rate limits
    'shodan': 1,
    'otx': 1
}

class APIEnricher:
    """Main class for API enrichment"""
    
    def __init__(self, api_keys: Dict[str, str] = None):
        """Initialize with optional API keys"""
        self.api_keys = api_keys or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def validate_ioc(self, ioc: str, ioc_type: str) -> bool:
        """Validate IOC format"""
        patterns = {
            'ip': r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$',
            'domain': r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,}|onion)$',
            'hash_md5': r'^[a-fA-F0-9]{32}$',
            'hash_sha256': r'^[a-fA-F0-9]{64}$',
            'btc': r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        }
        
        pattern = patterns.get(ioc_type)
        if pattern:
            return bool(re.match(pattern, ioc))
        return False
        
    def enrich_ip(self, ip: str) -> Dict:
        """Enrich IP address using multiple APIs"""
        results = {'ip': ip, 'enrichment_timestamp': datetime.now().isoformat()}
        
        # IP-API (free geolocation)
        try:
            response = self.session.get(f"{API_ENDPOINTS['ip_api']}{ip}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results['geolocation'] = {
                        'country': data.get('country'),
                        'region': data.get('regionName'),
                        'city': data.get('city'),
                        'isp': data.get('isp'),
                        'org': data.get('org'),
                        'timezone': data.get('timezone'),
                        'lat': data.get('lat'),
                        'lon': data.get('lon')
                    }
            time.sleep(RATE_LIMITS['ip_api'])
        except Exception as e:
            logger.error(f"IP-API error for {ip}: {e}")
            
        # BGPView (free ASN/network info)
        try:
            response = self.session.get(f"{API_ENDPOINTS['bgpview_ip']}{ip}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    bgp_data = data.get('data', {})
                    results['network'] = {
                        'asn': bgp_data.get('asn'),
                        'name': bgp_data.get('name'),
                        'description': bgp_data.get('description_short'),
                        'country': bgp_data.get('country_code'),
                        'prefixes': bgp_data.get('prefixes', [])[:5]  # Limit to 5
                    }
            time.sleep(RATE_LIMITS['bgpview'])
        except Exception as e:
            logger.error(f"BGPView error for {ip}: {e}")
            
        # AbuseIPDB (requires free API key)
        if 'abuseipdb' in self.api_keys:
            try:
                headers = {'Key': self.api_keys['abuseipdb']}
                params = {'ipAddress': ip, 'maxAgeInDays': 90, 'verbose': ''}
                response = self.session.get(API_ENDPOINTS['abuseipdb'], 
                                          headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data: # Check if 'data' key exists
                        abuse_data = data.get('data', {})
                        results['abuse'] = {
                            'confidence': abuse_data.get('abuseConfidenceScore'), # Correct key
                            'is_whitelisted': abuse_data.get('isWhitelisted'),
                            'country_code': abuse_data.get('countryCode'),
                            'usage_type': abuse_data.get('usageType'),
                            'total_reports': abuse_data.get('totalReports')
                        }
                time.sleep(RATE_LIMITS['abuseipdb'])
            except Exception as e:
                logger.error(f"AbuseIPDB error for {ip}: {e}")
                
        # OTX (free threat intelligence)
        try:
            response = self.session.get(f"{API_ENDPOINTS['otx_ip']}{ip}/general", timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['otx'] = {
                    'pulse_count': len(data.get('pulse_info', {}).get('pulses', [])),
                    'base_indicator': data.get('base_indicator', {}),
                    'reputation': data.get('reputation', 0)
                }
            time.sleep(RATE_LIMITS['otx'])
        except Exception as e:
            logger.error(f"OTX error for {ip}: {e}")
            
        return results
        
    def enrich_domain(self, domain: str) -> Dict:
        """Enrich domain using multiple APIs"""
        results = {'domain': domain, 'enrichment_timestamp': datetime.now().isoformat()}
        
        # OTX domain intelligence
        try:
            response = self.session.get(f"{API_ENDPOINTS['otx_domain']}{domain}/general", timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['otx'] = {
                    'pulse_count': len(data.get('pulse_info', {}).get('pulses', [])),
                    'base_indicator': data.get('base_indicator', {}),
                    'reputation': data.get('reputation', 0)
                }
            time.sleep(RATE_LIMITS['otx'])
        except Exception as e:
            logger.error(f"OTX domain error for {domain}: {e}")
            
        # Basic domain analysis
        results['analysis'] = {
            'is_onion': domain.endswith('.onion'),
            'length': len(domain),
            'subdomain_count': domain.count('.') - 1,
            'suspicious_tld': domain.split('.')[-1] in ['tk', 'ml', 'ga', 'cf']
        }
        
        return results
        
    def enrich_hash(self, hash_value: str) -> Dict:
        """Enrich file hash using multiple APIs"""
        results = {'hash': hash_value, 'enrichment_timestamp': datetime.now().isoformat()}
        
        # Determine hash type
        if len(hash_value) == 32:
            results['hash_type'] = 'md5'
        elif len(hash_value) == 64:
            results['hash_type'] = 'sha256'
        else:
            results['hash_type'] = 'unknown'
            
        # VirusTotal (requires free API key)
        if 'virustotal' in self.api_keys:
            try:
                params = {'apikey': self.api_keys['virustotal'], 'resource': hash_value}
                response = self.session.get(API_ENDPOINTS['virustotal'], params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    results['virustotal'] = {
                        'response_code': data.get('response_code'),
                        'positives': data.get('positives', 0),
                        'total': data.get('total', 0),
                        'scan_date': data.get('scan_date'),
                        'permalink': data.get('permalink')
                    }
                time.sleep(RATE_LIMITS['virustotal'])
            except Exception as e:
                logger.error(f"VirusTotal error for {hash_value}: {e}")
                
        # OTX hash intelligence
        try:
            response = self.session.get(f"{API_ENDPOINTS['otx_hash']}{hash_value}/general", timeout=10)
            if response.status_code == 200:
                data = response.json()
                results['otx'] = {
                    'pulse_count': len(data.get('pulse_info', {}).get('pulses', [])),
                    'base_indicator': data.get('base_indicator', {}),
                    'reputation': data.get('reputation', 0)
                }
            time.sleep(RATE_LIMITS['otx'])
        except Exception as e:
            logger.error(f"OTX hash error for {hash_value}: {e}")
            
        return results
        
    def enrich_btc_address(self, btc_address: str) -> Dict:
        """Enrich Bitcoin address (basic analysis)"""
        results = {'btc_address': btc_address, 'enrichment_timestamp': datetime.now().isoformat()}
        
        # Basic BTC address analysis
        results['analysis'] = {
            'address_type': 'legacy' if btc_address.startswith('1') else 
                           'script' if btc_address.startswith('3') else 
                           'bech32' if btc_address.startswith('bc1') else 'unknown',
            'length': len(btc_address),
            'first_seen': datetime.now().isoformat()  # Would need blockchain API for real data
        }
        
        return results
        
    def enrich_email(self, email: str) -> Dict:
        """Enrich email address (basic analysis)"""
        results = {'email': email, 'enrichment_timestamp': datetime.now().isoformat()}
        
        domain = email.split('@')[-1] if '@' in email else ''
        results['analysis'] = {
            'domain': domain,
            'is_disposable': domain in ['temp-mail.org', '10minutemail.com', 'guerrillamail.com'],
            'suspicious_domain': domain.endswith('.onion') or domain in ['protonmail.com', 'tutanota.com']
        }
        
        return results

    def send_to_n8n(self, enriched_data: List[Dict]) -> bool:
        """Send enriched data to n8n webhook"""
        try:
            payload = {
                'enriched_data': enriched_data,
                'metadata': {
                    'total_items': len(enriched_data),
                    'enrichment_timestamp': datetime.now().isoformat(),
                    'enricher_version': '1.0'
                }
            }
            
            response = self.session.post(
                N8N_WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response.raise_for_status()
            logger.info(f"Successfully sent {len(enriched_data)} enriched items to n8n")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send data to n8n: {e}")
            return False

def extract_iocs_from_text(text: str) -> Dict[str, List[str]]:
    """Extract IOCs from raw text"""
    iocs = {
        'ips': [],
        'domains': [],
        'hashes': [],
        'btc_addresses': [],
        'emails': []
    }
    
    # IP addresses
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    iocs['ips'] = list(set(re.findall(ip_pattern, text)))
    
    # Domains (including .onion)
    domain_pattern = r'\b[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.(?:[a-zA-Z]{2,}|onion)\b'
    iocs['domains'] = list(set(re.findall(domain_pattern, text)))
    
    # Hashes (MD5 and SHA256)
    hash_pattern = r'\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{64}\b'
    iocs['hashes'] = list(set(re.findall(hash_pattern, text)))
    
    # Bitcoin addresses
    btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|\bbc1[a-z0-9]{39,59}\b'
    iocs['btc_addresses'] = list(set(re.findall(btc_pattern, text)))
    
    # Email addresses
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    iocs['emails'] = list(set(re.findall(email_pattern, text)))
    
    return iocs

def main():
    """Main execution function"""
    logger.info("Starting API enrichment process...")
    
    # Sample IOCs for testing
    test_iocs = {
        'ips': ['8.8.8.8', '1.1.1.1'],
        'domains': ['google.com', 'facebook.com'],
        'hashes': ['d41d8cd98f00b204e9800998ecf8427e'],  # MD5 of empty string
        'btc_addresses': ['1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'],
        'emails': ['test@example.com']
    }
    
    # Initialize enricher (load API keys from environment)
    api_keys = {
        'abuseipdb': get_api_key('abuseipdb'),
        'virustotal': get_api_key('virustotal'),
        'shodan': get_api_key('shodan')
    }
    # Remove empty keys
    api_keys = {k: v for k, v in api_keys.items() if v}
    
    enricher = APIEnricher(api_keys)
    enriched_results = []
    
    # Enrich IPs
    for ip in test_iocs['ips']:
        if enricher.validate_ioc(ip, 'ip'):
            logger.info(f"Enriching IP: {ip}")
            result = enricher.enrich_ip(ip)
            enriched_results.append(result)
    
    # Enrich domains
    for domain in test_iocs['domains']:
        if enricher.validate_ioc(domain, 'domain'):
            logger.info(f"Enriching domain: {domain}")
            result = enricher.enrich_domain(domain)
            enriched_results.append(result)
    
    # Enrich hashes
    for hash_val in test_iocs['hashes']:
        if enricher.validate_ioc(hash_val, 'hash_md5') or enricher.validate_ioc(hash_val, 'hash_sha256'):
            logger.info(f"Enriching hash: {hash_val}")
            result = enricher.enrich_hash(hash_val)
            enriched_results.append(result)
    
    # Enrich BTC addresses
    for btc in test_iocs['btc_addresses']:
        if enricher.validate_ioc(btc, 'btc'):
            logger.info(f"Enriching BTC address: {btc}")
            result = enricher.enrich_btc_address(btc)
            enriched_results.append(result)
    
    # Enrich emails
    for email in test_iocs['emails']:
        if enricher.validate_ioc(email, 'email'):
            logger.info(f"Enriching email: {email}")
            result = enricher.enrich_email(email)
            enriched_results.append(result)
    
    logger.info(f"Enriched {len(enriched_results)} IOCs")
    
    # Print results for verification and send to webhook
    if enriched_results:
        logger.info("=== ENRICHMENT RESULTS ===")
        # Pretty print for console verification
        print(json.dumps(enriched_results, indent=2))
        
        logger.info("Attempting to send data to n8n webhook...")
        enricher.send_to_n8n(enriched_results)
    else:
        logger.warning("No IOCs were enriched")

if __name__ == "__main__":
    main()
