#!/usr/bin/env python3
"""
Feature 8: Hash Extraction and Malware IOC Analysis (Local Version)

Extracts MD5, SHA1, and SHA256 hashes from text data, enriches them
with threat intelligence from the VirusTotal API, and saves the results
to a local JSON file.
"""

import re
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests

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
        logging.FileHandler(os.path.join(log_dir, 'hash_extractor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HashExtractor:
    """Extracts and enriches file hashes with threat intelligence."""
    
    def __init__(self):
        self.virustotal_api_key = get_api_key('virustotal')
        self.hash_patterns = {
            'md5': re.compile(r'\b[a-fA-F0-9]{32}\b'),
            'sha1': re.compile(r'\b[a-fA-F0-9]{40}\b'),
            'sha256': re.compile(r'\b[a-fA-F0-9]{64}\b')
        }
        self.virustotal_base_url = 'https://www.virustotal.com/api/v3/files'
        
    def extract_hashes(self, text: str) -> Dict[str, List[str]]:
        """Extracts hashes from text using regex patterns."""
        extracted = {}
        for hash_type, pattern in self.hash_patterns.items():
            matches = list(dict.fromkeys(pattern.findall(text)))
            if matches:
                extracted[hash_type] = matches
        return extracted
    
    def query_virustotal(self, hash_value: str) -> Optional[Dict[str, Any]]:
        """Queries VirusTotal for threat intelligence on a given hash."""
        if not self.virustotal_api_key:
            logger.warning(f"No VirusTotal API key found. Skipping enrichment for {hash_value}")
            return {"hash": hash_value, "status": "skipped", "message": "API key not configured"}
            
        headers = {'x-apikey': self.virustotal_api_key}
        
        try:
            # Rate limit before the request
            time.sleep(16)
            response = requests.get(f'{self.virustotal_base_url}/{hash_value}', headers=headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json().get('data', {}).get('attributes', {})
                stats = data.get('last_analysis_stats', {})
                return {
                    "hash": hash_value,
                    "status": "found",
                    "malicious": stats.get('malicious', 0),
                    "suspicious": stats.get('suspicious', 0),
                    "harmless": stats.get('harmless', 0),
                    "first_seen": data.get('first_submission_date'),
                    "names": data.get('names', [])[:5]
                }
            elif response.status_code == 404:
                return {"hash": hash_value, "status": "not_found"}
            else:
                logger.error(f"VirusTotal returned status {response.status_code} for {hash_value}")
                return {"hash": hash_value, "status": "error", "error_code": response.status_code}
                
        except requests.RequestException as e:
            logger.error(f"VirusTotal request failed for {hash_value}: {e}")
            return {"hash": hash_value, "status": "error", "message": str(e)}
    
    def process_data(self, source_data: List[Dict[str, Any]]) -> List[Dict]:
        """Processes a list of text entries to find and enrich hashes."""
        all_results = []
        
        for entry in source_data:
            logger.info(f"🔍 Processing data from source: {entry.get('source', 'unknown')}...")
            text_content = entry.get("data", "")
            
            extracted_hashes = self.extract_hashes(text_content)
            total_hashes = sum(len(h) for h in extracted_hashes.values())
            
            if total_hashes == 0:
                logger.info("No hashes found in this entry.")
                continue
            
            logger.info(f"📊 Found {total_hashes} unique hashes.")
            
            enriched_hashes = []
            for hash_type, hashes in extracted_hashes.items():
                for hash_value in hashes:
                    enrichment = self.query_virustotal(hash_value)
                    enrichment['hash_type'] = hash_type
                    enriched_hashes.append(enrichment)
            
            entry_result = {
                'source': entry.get('source', 'unknown'),
                'source_timestamp': entry.get('timestamp'),
                'analysis_timestamp': datetime.now().isoformat(),
                'hashes_found': total_hashes,
                'enrichment_results': enriched_hashes
            }
            all_results.append(entry_result)
            
        return all_results

def save_results(data: List[Dict]):
    """Saves the enriched hash data to a JSON file."""
    if not data:
        logger.warning("No enriched hashes to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_8_hash_analysis.json')
        
        final_payload = {
            "feature_name": "Hash Extraction & Analysis",
            "execution_timestamp": datetime.now().isoformat(),
            "total_entries_analyzed": len(data),
            "analysis_results": data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Feature 8: Hash Extraction & Analysis...")
    
    # In a pipeline, this file would be the output of a previous feature.
    # We create a dummy version here for standalone testing.
    INPUT_FILE = "sample_hash_input_data.json"
    if not os.path.exists(INPUT_FILE):
        logger.warning(f"'{INPUT_FILE}' not found. Creating a dummy file for testing.")
        dummy_data = [
            {
                "source": "MarketplaceScrape",
                "timestamp": "2025-08-01T12:00:00Z",
                "data": "Download our new tool. SHA256: 275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f. Also an old md5: d41d8cd98f00b204e9800998ecf8427e."
            },
            {
                "source": "ForumPost",
                "timestamp": "2025-08-01T13:00:00Z",
                "data": "Avoid this file, VT says it's bad: aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d (SHA1)"
            }
        ]
        with open(INPUT_FILE, 'w') as f:
            json.dump(dummy_data, f, indent=2)

    try:
        input_data = json.load(open(INPUT_FILE, 'r'))
        extractor = HashExtractor()
        results = extractor.process_data(input_data)
        
        if results:
            save_results(results)
            print("\n--- Hash Analysis Complete ---")
            print(f"Processed {len(results)} entries containing hashes.")
            print("------------------------------")
        else:
            logger.info("No hashes were found or processed.")
            
    except FileNotFoundError:
        logger.error(f"Input file '{INPUT_FILE}' not found.")
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}")

    logger.info("✅ Hash extraction process finished.")
