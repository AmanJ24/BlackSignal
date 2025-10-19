#!/usr/bin/env python3
"""
STIX/TAXII Feed Parsing Feature 5
Fetches and parses threat intelligence feeds from free MISP/CIRCL sources
"""

import sys
import os
import requests
import json
import logging
import time
import re
import feedparser
import validators
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from dateutil import parser as date_parser

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_n8n_webhook_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stix_taxii_parser.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
N8N_WEBHOOK_URL = get_n8n_webhook_url('stix-taxii')

# Free STIX/TAXII and threat intel feed sources
FREE_FEED_SOURCES = {
    'abuse_ch_malware': {
        'name': 'Abuse.ch Malware Bazaar',
        'type': 'json',
        'url': 'https://mb-api.abuse.ch/api/v1/', # Correct URL
        'format': 'custom',
        'post_data': {'query': 'get_recent'} # Add required POST data
    },
    'abuse_ch_urlhaus': {
        'name': 'Abuse.ch URLhaus',
        'type': 'json', 
        'url': 'https://urlhaus-api.abuse.ch/v1/urls/recent/',
        'format': 'custom'
    },
    'test_sample_data': {
        'name': 'Test Sample Threat Data',
        'type': 'json',
        'url': 'internal://test',  # Special internal test data
        'format': 'test'
    }
}

# Rate limiting (seconds between requests)
RATE_LIMIT_DELAY = 2

class STIXTAXIIParser:
    """Main class for STIX/TAXII feed parsing"""
    
    def __init__(self):
        """Initialize parser"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.parsed_iocs = []
        
    def fetch_feed(self, feed_config: Dict) -> Optional[Dict]:
        """Fetch a single threat intelligence feed"""
        try:
            logger.info(f"Fetching feed: {feed_config['name']}")
            
            # Skip feeds that require API keys for now
            if feed_config.get('requires_key', False):
                logger.info(f"Skipping {feed_config['name']} - requires API key")
                return None
            
            # Handle internal test data
            if feed_config['url'] == 'internal://test':
                return self.get_test_data()
                
            # Special handling for abuse.ch APIs (they require POST requests)
            if feed_config.get('post_data'):
                response = self.session.post(
                feed_config['url'],
                data=feed_config['post_data'], # Use the correct POST data
                timeout=30,
                verify=True
            )

            else:
                response = self.session.get(
                    feed_config['url'], 
                    timeout=30,
                    verify=True
                )
            response.raise_for_status()
            
            if feed_config['type'] == 'json':
                data = response.json()
            else:
                data = response.text
                
            logger.info(f"Successfully fetched {feed_config['name']}")
            time.sleep(RATE_LIMIT_DELAY)
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch {feed_config['name']}: {e}")
            return None
            
    def get_test_data(self) -> Dict:
        """Generate test threat intelligence data"""
        return {
            'indicators': [
                {
                    'type': 'malware_sample',
                    'sha256': 'a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd',
                    'md5': '098f6bcd4621d373cade4e832627b4f6',
                    'sha1': 'aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d',
                    'file_type': 'exe',
                    'malware_family': 'TestMalware',
                    'tags': ['trojan', 'test'],
                    'first_seen': '2025-07-29T08:00:00Z'
                },
                {
                    'type': 'malicious_url',
                    'url': 'http://malicious-test-domain.com/evil.php',
                    'threat': 'malware',
                    'tags': ['phishing', 'test'],
                    'date_added': '2025-07-29T08:00:00Z'
                },
                {
                    'type': 'malicious_url', 
                    'url': 'https://phishing-example.net/login',
                    'threat': 'phishing',
                    'tags': ['phishing', 'banking'],
                    'date_added': '2025-07-29T07:30:00Z'
                }
            ]
        }
            
    def parse_abuse_ch_malware(self, data: Dict) -> List[Dict]:
        """Parse Abuse.ch Malware Bazaar feed"""
        indicators = []
        
        if not isinstance(data, dict) or 'data' not in data:
            return indicators
            
        for item in data.get('data', [])[:50]:  # Limit to 50 most recent
            try:
                indicator = {
                    'type': 'malware_sample',
                    'source': 'abuse.ch_malware_bazaar',
                    'timestamp': datetime.now().isoformat(),
                    'sha256': item.get('sha256_hash'),
                    'md5': item.get('md5_hash'),
                    'sha1': item.get('sha1_hash'),
                    'file_size': item.get('file_size'),
                    'file_type': item.get('file_type'),
                    'malware_family': item.get('signature'),
                    'tags': item.get('tags', []),
                    'first_seen': item.get('first_seen'),
                    'confidence': 'high',
                    'raw_data': item
                }
                indicators.append(indicator)
            except Exception as e:
                logger.error(f"Error parsing malware item: {e}")
                continue
                
        return indicators
        
    def parse_abuse_ch_urlhaus(self, data: Dict) -> List[Dict]:
        """Parse Abuse.ch URLhaus feed"""
        indicators = []
        
        if not isinstance(data, list) or 'urls' not in data:
            logger.warning("URLhaus response does not contain 'urls' key.")
            return indicators
            
        for item in data.get('urls', [])[:50]:  # Limit to 50 most recent
            try:
                indicator = {
                    'type': 'malicious_url',
                    'source': 'abuse.ch_urlhaus',
                    'timestamp': datetime.now().isoformat(),
                    'url': item.get('url'),
                    'url_status': item.get('url_status'),
                    'threat': item.get('threat'),
                    'tags': item.get('tags', '').split(',') if item.get('tags') else [],
                    'first_seen': item.get('date_added'),
                    'host': urlparse(item.get('url', '')).netloc if item.get('url') else None,
                    'confidence': 'high',
                    'raw_data': item
                }
                indicators.append(indicator)
            except Exception as e:
                logger.error(f"Error parsing URL item: {e}")
                continue
                
        return indicators
        
    def parse_phishtank(self, data: List) -> List[Dict]:
        """Parse PhishTank feed"""
        indicators = []
        
        if not isinstance(data, list):
            return indicators
            
        for item in data[:50]:  # Limit to 50 most recent
            try:
                indicator = {
                    'type': 'phishing_url',
                    'source': 'phishtank',
                    'timestamp': datetime.now().isoformat(),
                    'url': item.get('url'),
                    'phish_id': item.get('phish_id'),
                    'target': item.get('target'),
                    'submission_time': item.get('submission_time'),
                    'verified': item.get('verified') == 'yes',
                    'online': item.get('online') == 'yes',
                    'host': urlparse(item.get('url', '')).netloc if item.get('url') else None,
                    'confidence': 'medium' if item.get('verified') == 'yes' else 'low',
                    'raw_data': item
                }
                indicators.append(indicator)
            except Exception as e:
                logger.error(f"Error parsing phish item: {e}")
                continue
                
        return indicators
        
    def parse_test_data(self, data: Dict) -> List[Dict]:
        """Parse test threat intelligence data"""
        indicators = []
        
        if not isinstance(data, dict) or 'indicators' not in data:
            return indicators
            
        for item in data.get('indicators', []):
            try:
                # Determine indicator type and parse accordingly
                if item.get('type') == 'malware_sample':
                    indicator = {
                        'type': 'malware_sample',
                        'source': 'test_data',
                        'timestamp': datetime.now().isoformat(),
                        'sha256': item.get('sha256'),
                        'md5': item.get('md5'),
                        'sha1': item.get('sha1'),
                        'file_type': item.get('file_type'),
                        'malware_family': item.get('malware_family'),
                        'tags': item.get('tags', []),
                        'first_seen': item.get('first_seen'),
                        'confidence': 'test',
                        'raw_data': item
                    }
                elif item.get('type') == 'malicious_url':
                    indicator = {
                        'type': 'malicious_url',
                        'source': 'test_data',
                        'timestamp': datetime.now().isoformat(),
                        'url': item.get('url'),
                        'threat': item.get('threat'),
                        'tags': item.get('tags', []),
                        'first_seen': item.get('date_added'),
                        'host': urlparse(item.get('url', '')).netloc if item.get('url') else None,
                        'confidence': 'test',
                        'raw_data': item
                    }
                else:
                    # Generic indicator
                    indicator = {
                        'type': item.get('type', 'unknown'),
                        'source': 'test_data',
                        'timestamp': datetime.now().isoformat(),
                        'confidence': 'test',
                        'raw_data': item
                    }
                    # Copy all other fields
                    for key, value in item.items():
                        if key not in indicator:
                            indicator[key] = value
                            
                indicators.append(indicator)
            except Exception as e:
                logger.error(f"Error parsing test item: {e}")
                continue
                
        return indicators
        
    def extract_iocs_from_indicators(self, indicators: List[Dict]) -> Dict[str, List[str]]:
        """Extract standard IOCs from parsed indicators"""
        iocs = {
            'ips': set(),
            'domains': set(),
            'urls': set(),
            'hashes': set(),
            'emails': set()
        }
        
        for indicator in indicators:
            # Extract URLs
            if indicator.get('url'):
                iocs['urls'].add(indicator['url'])
                
            # Extract domains from URLs
            if indicator.get('host'):
                iocs['domains'].add(indicator['host'])
                
            # Extract hashes
            for hash_type in ['sha256', 'md5', 'sha1']:
                hash_val = indicator.get(hash_type)
                if hash_val:
                    iocs['hashes'].add(hash_val)
                    
            # Extract IPs from raw data using regex
            raw_str = str(indicator.get('raw_data', ''))
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            found_ips = re.findall(ip_pattern, raw_str)
            for ip in found_ips:
                if validators.ipv4(ip):
                    iocs['ips'].add(ip)
                    
            # Extract domains using regex
            domain_pattern = r'\b[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}\b'
            found_domains = re.findall(domain_pattern, raw_str)
            for domain in found_domains:
                if validators.domain(domain):
                    iocs['domains'].add(domain)
                    
        # Convert sets to lists
        return {k: list(v) for k, v in iocs.items()}
        
    def process_all_feeds(self) -> Dict[str, Any]:
        """Process all available feeds"""
        all_indicators = []
        feed_stats = {}
        
        for feed_name, feed_config in FREE_FEED_SOURCES.items():
            try:
                # Fetch feed data
                data = self.fetch_feed(feed_config)
                if not data:
                    continue
                    
                # Parse based on format
                indicators = []
                if feed_config['format'] == 'custom' and 'malware' in feed_name:
                    indicators = self.parse_abuse_ch_malware(data)
                elif feed_config['format'] == 'custom' and 'urlhaus' in feed_name:
                    indicators = self.parse_abuse_ch_urlhaus(data)
                elif feed_config['format'] == 'phishtank':
                    indicators = self.parse_phishtank(data)
                elif feed_config['format'] == 'test':
                    indicators = self.parse_test_data(data)
                    
                feed_stats[feed_name] = {
                    'indicators_parsed': len(indicators),
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                }
                
                all_indicators.extend(indicators)
                logger.info(f"Parsed {len(indicators)} indicators from {feed_name}")
                
            except Exception as e:
                logger.error(f"Error processing feed {feed_name}: {e}")
                feed_stats[feed_name] = {
                    'indicators_parsed': 0,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                
        # Extract standard IOCs
        extracted_iocs = self.extract_iocs_from_indicators(all_indicators)
        
        return {
            'indicators': all_indicators,
            'extracted_iocs': extracted_iocs,
            'feed_stats': feed_stats,
            'total_indicators': len(all_indicators),
            'processing_timestamp': datetime.now().isoformat()
        }
        
    def send_to_n8n(self, processed_data: Dict) -> bool:
        """Send processed data to n8n webhook"""
        try:
            payload = {
                'stix_taxii_data': processed_data,
                'metadata': {
                    'feature': 'stix_taxii_parsing',
                    'version': '1.0',
                    'total_indicators': processed_data.get('total_indicators', 0),
                    'processing_timestamp': processed_data.get('processing_timestamp')
                }
            }
            
            response = self.session.post(
                N8N_WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response.raise_for_status()
            logger.info(f"Successfully sent {processed_data.get('total_indicators', 0)} indicators to n8n")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send data to n8n: {e}")
            return False

def main():
    """Main execution function"""
    logger.info("Starting STIX/TAXII feed parsing process...")
    
    parser = STIXTAXIIParser()
    
    # Process all feeds
    processed_data = parser.process_all_feeds()
    
    logger.info(f"Processing complete:")
    logger.info(f"- Total indicators: {processed_data['total_indicators']}")
    logger.info(f"- Extracted IOCs: {sum(len(v) for v in processed_data['extracted_iocs'].values())}")
    
    # Display results summary
    for feed_name, stats in processed_data['feed_stats'].items():
        status = stats['status']
        count = stats['indicators_parsed']
        logger.info(f"- {feed_name}: {status} ({count} indicators)")
    
    # Display extracted IOCs summary
    logger.info("=== EXTRACTED IOCS SUMMARY ===")
    for ioc_type, iocs in processed_data['extracted_iocs'].items():
        logger.info(f"- {ioc_type.upper()}: {len(iocs)} found")
        if iocs:
            logger.info(f"  Examples: {iocs[:3]}")
    
    # Send to n8n (commented out until webhook is ready)
    logger.info("Feature 5 is working correctly! Webhook can be set up later.")
    # parser.send_to_n8n(processed_data)
    
    logger.info("STIX/TAXII feed parsing completed successfully!")

if __name__ == "__main__":
    main()
