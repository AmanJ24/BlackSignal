#!/usr/bin/env python3
"""
Feature 5: STIX/TAXII Feed Parser (Local Version)
Fetches and parses threat intelligence feeds from various public sources,
extracts key indicators, and saves the results to a local JSON file.
"""

import sys
import os
import requests
import json
import logging
import time
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Config import is optional, as this version has no dependencies on it

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'stix_taxii_parser.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Configuration ---
FREE_FEED_SOURCES = {
    'abuse_ch_malware': {
        'name': 'Abuse.ch Malware Bazaar',
        'type': 'json',
        'url': 'https://mb-api.abuse.ch/api/v1/',
        'format': 'custom',
        'post_data': {'query': 'get_recent'}
    },
    'abuse_ch_urlhaus': {
        'name': 'Abuse.ch URLhaus',
        'type': 'json', 
        'url': 'https://urlhaus-api.abuse.ch/v1/urls/recent/',
        'format': 'custom'
    }
}
RATE_LIMIT_DELAY = 2

class FeedParser:
    """Parses various threat intelligence feeds."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OSINT-Pipeline-Feed-Parser/1.0'
        })
        
    def fetch_feed(self, feed_config: Dict) -> Optional[Dict]:
        """Fetches data from a single threat feed."""
        logger.info(f"Fetching feed: {feed_config['name']}")
        try:
            if feed_config.get('post_data'):
                response = self.session.post(feed_config['url'], data=feed_config['post_data'], timeout=30)
            else:
                response = self.session.get(feed_config['url'], timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully fetched {feed_config['name']}")
            time.sleep(RATE_LIMIT_DELAY)
            return response.json() if feed_config['type'] == 'json' else response.text
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {feed_config['name']}: {e}")
            return None
            
    def parse_abuse_ch_malware(self, data: Dict) -> List[Dict]:
        """Parses the Abuse.ch Malware Bazaar feed format."""
        indicators = []
        if not data or 'data' not in data:
            return indicators
            
        for item in data.get('data', [])[:50]: # Limit to 50 most recent
            indicator = {
                'type': 'malware_sample',
                'source': 'abuse.ch_malware_bazaar',
                'sha256': item.get('sha256_hash'),
                'md5': item.get('md5_hash'),
                'signature': item.get('signature'),
                'tags': item.get('tags', []),
                'first_seen': item.get('first_seen')
            }
            indicators.append(indicator)
        return indicators
        
    def parse_abuse_ch_urlhaus(self, data: Dict) -> List[Dict]:
        """Parses the Abuse.ch URLhaus feed format."""
        indicators = []
        if not data or 'urls' not in data:
            logger.warning("URLhaus response format is unexpected.")
            return indicators
            
        for item in data.get('urls', [])[:50]: # Limit to 50 most recent
            indicator = {
                'type': 'malicious_url',
                'source': 'abuse.ch_urlhaus',
                'url': item.get('url'),
                'threat': item.get('threat'),
                'tags': item.get('tags', []),
                'first_seen': item.get('date_added'),
                'host': urlparse(item.get('url', '')).netloc
            }
            indicators.append(indicator)
        return indicators
        
    def extract_iocs_from_indicators(self, indicators: List[Dict]) -> Dict[str, List[str]]:
        """Extracts standard IOC formats from a list of parsed indicators."""
        iocs = {'ips': set(), 'domains': set(), 'urls': set(), 'hashes': set()}
        
        for indicator in indicators:
            if indicator.get('url'):
                iocs['urls'].add(indicator['url'])
            if indicator.get('host'):
                iocs['domains'].add(indicator['host'])
            for hash_type in ['sha256', 'md5']:
                if indicator.get(hash_type):
                    iocs['hashes'].add(indicator[hash_type])
            
            # Simple regex to find any IPs in the raw data
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            raw_str = json.dumps(indicator)
            found_ips = re.findall(ip_pattern, raw_str)
            iocs['ips'].update(found_ips)
                    
        return {k: sorted(list(v)) for k, v in iocs.items()}
        
    def process_all_feeds(self) -> Dict[str, Any]:
        """Processes all configured feeds and returns a consolidated report."""
        all_indicators = []
        feed_stats = {}
        
        for feed_name, feed_config in FREE_FEED_SOURCES.items():
            data = self.fetch_feed(feed_config)
            if not data:
                feed_stats[feed_name] = {'status': 'error', 'parsed_count': 0}
                continue
                
            indicators = []
            if 'malware' in feed_name:
                indicators = self.parse_abuse_ch_malware(data)
            elif 'urlhaus' in feed_name:
                indicators = self.parse_abuse_ch_urlhaus(data)
            
            feed_stats[feed_name] = {'status': 'success', 'parsed_count': len(indicators)}
            all_indicators.extend(indicators)
            logger.info(f"Parsed {len(indicators)} indicators from {feed_name}")
                
        extracted_iocs = self.extract_iocs_from_indicators(all_indicators)
        
        return {
            "feature_name": "STIX/TAXII Feed Parser",
            "execution_timestamp": datetime.now().isoformat(),
            "feed_summary": feed_stats,
            "total_indicators_parsed": len(all_indicators),
            "consolidated_iocs": extracted_iocs
        }

def save_results(data: Dict):
    """Saves the final report to a JSON file in the 'output' directory."""
    if not data or data['total_indicators_parsed'] == 0:
        logger.warning("No indicators parsed, nothing to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_5_stix_taxii_feeds.json')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Feature 5: STIX/TAXII Feed Parsing...")
    
    parser = FeedParser()
    report = parser.process_all_feeds()
    
    if report:
        save_results(report)
        print("\n--- Feed Processing Summary ---")
        print(json.dumps(report["feed_summary"], indent=4))
        print(f"\nTotal Indicators: {report['total_indicators_parsed']}")
        print("------------------------------")
    
    logger.info("✅ STIX/TAXII feed parsing completed.")
