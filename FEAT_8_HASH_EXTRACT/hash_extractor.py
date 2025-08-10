#!/usr/bin/env python3
"""
Hash Extraction and Malware IOC Analysis - Feature 8

Extracts MD5, SHA1, and SHA256 hashes from collected data and enriches
them with threat intelligence using VirusTotal API.

Author: Dark Web OSINT Pipeline
Date: 2025-07-31
"""

import re
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from dotenv import load_dotenv

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_n8n_webhook_url, get_api_key

class HashExtractor:
    """Extracts and enriches file hashes with threat intelligence"""
    
    def __init__(self):
        self.virustotal_api_key = get_api_key('virustotal')
        self.webhook_url = get_n8n_webhook_url('hash-extract')
        self.hash_patterns = {
            'MD5': r'\b[a-fA-F0-9]{32}\b',
            'SHA1': r'\b[a-fA-F0-9]{40}\b',
            'SHA256': r'\b[a-fA-F0-9]{64}\b'
        }
        self.virustotal_base_url = 'https://www.virustotal.com/api/v3/files'
        
    def extract_hashes(self, text: str) -> Dict[str, List[str]]:
        """Extract hashes from text using regex patterns."""
        extracted_hashes = {}
        for hash_type, pattern in self.hash_patterns.items():
            matches = re.findall(pattern, text)
            # Remove duplicates while preserving order
            unique_matches = list(dict.fromkeys(matches))
            extracted_hashes[hash_type] = unique_matches
        return extracted_hashes
    
    def query_virustotal(self, hash_value: str) -> Optional[Dict[str, Any]]:
        """Query VirusTotal for threat intelligence on a given hash."""
        if not self.virustotal_api_key:
            print(f"⚠️  No VirusTotal API key found. Skipping enrichment for {hash_value}")
            return {
                "error": "No API key",
                "hash": hash_value,
                "message": "VirusTotal API key not configured"
            }
            
        headers = {
            'x-apikey': self.virustotal_api_key
        }
        
        try:
            response = requests.get(
                f'{self.virustotal_base_url}/{hash_value}', 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract key information
                return {
                    "hash": hash_value,
                    "malicious": data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {}).get('malicious', 0),
                    "suspicious": data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {}).get('suspicious', 0),
                    "harmless": data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {}).get('harmless', 0),
                    "first_seen": data.get('data', {}).get('attributes', {}).get('first_submission_date'),
                    "last_seen": data.get('data', {}).get('attributes', {}).get('last_submission_date'),
                    "names": data.get('data', {}).get('attributes', {}).get('names', [])[:5]  # First 5 names
                }
            elif response.status_code == 404:
                return {
                    "hash": hash_value,
                    "status": "not_found",
                    "message": "Hash not found in VirusTotal database"
                }
            else:
                return {
                    "hash": hash_value,
                    "error": f"HTTP {response.status_code}",
                    "message": "Failed to query VirusTotal"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "hash": hash_value,
                "error": "Request failed",
                "message": str(e)
            }
            
        # Rate limiting - VirusTotal free tier allows 4 requests per minute
        time.sleep(15)  # Wait 15 seconds between requests
    
    def send_to_webhook(self, data: Dict[str, Any]) -> bool:
        """Send processed data to n8n webhook"""
        try:
            response = requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully sent data to webhook: {self.webhook_url}")
                return True
            else:
                print(f"⚠️  Webhook returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send to webhook: {e}")
            return False
    
    def process_data(self, source_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process input data for hash extraction and enrichment."""
        results = []
        
        for entry in source_data:
            print(f"🔍 Processing data from {entry.get('source', 'unknown')}...")
            
            # Extract hashes
            hash_details = self.extract_hashes(entry['data'])
            total_hashes = sum(len(hashes) for hashes in hash_details.values())
            
            print(f"📊 Found {total_hashes} hashes:")
            for hash_type, hashes in hash_details.items():
                if hashes:
                    print(f"   - {hash_type}: {len(hashes)} hashes")
            
            # Enrich with VirusTotal data (only if hashes found)
            enriched_data = {}
            if total_hashes > 0:
                print("🔬 Enriching with VirusTotal data...")
                for hash_type, hashes in hash_details.items():
                    if hashes:
                        enriched_data[hash_type] = []
                        for hash_value in hashes:
                            vt_result = self.query_virustotal(hash_value)
                            enriched_data[hash_type].append(vt_result)
            
            # Create result structure
            result = {
                'timestamp': datetime.utcnow().isoformat(),
                'feature': 'Hash Extraction (Malware IOCs)',
                'input_text': entry['data'][:200] + "..." if len(entry['data']) > 200 else entry['data'],
                'hashes_found': total_hashes,
                'hashes': hash_details,
                'virustotal_enrichment': enriched_data,
                'source': entry.get('source', 'unknown'),
                'source_timestamp': entry.get('timestamp', datetime.utcnow().isoformat()),
                'webhook_url': self.webhook_url
            }
            
            results.append(result)
            
        return results


def load_sample_data(filename: str = 'sample_hash_data.json') -> List[Dict[str, Any]]:
    """Load sample data from JSON file"""
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            print(f"📂 Loaded {len(data)} entries from {filename}")
            return data
    except FileNotFoundError:
        print(f"❌ File {filename} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return []


if __name__ == "__main__":
    print("🚀 Hash Extraction Feature 8 - Starting...")
    print("=" * 50)
    
    # Initialize hash extractor
    extractor = HashExtractor()
    
    # Load sample input data
    sample_data = load_sample_data()
    
    if not sample_data:
        print("❌ No sample data available. Exiting.")
        sys.exit(1)
    
    # Process data
    result_data = extractor.process_data(sample_data)
    
    # Print results in readable format
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print("=" * 50)
    
    for result in result_data:
        print(f"\n🎯 Source: {result['source']}")
        print(f"📅 Timestamp: {result['timestamp']}")
        print(f"🔢 Hashes Found: {result['hashes_found']}")
        
        if result['hashes_found'] > 0:
            for hash_type, hashes in result['hashes'].items():
                if hashes:
                    print(f"   {hash_type}: {hashes}")
        
        # Show VirusTotal enrichment summary
        if result.get('virustotal_enrichment'):
            print("🔬 VirusTotal Analysis:")
            for hash_type, enrichments in result['virustotal_enrichment'].items():
                for enrichment in enrichments:
                    if 'malicious' in enrichment:
                        malicious = enrichment.get('malicious', 0)
                        suspicious = enrichment.get('suspicious', 0)
                        status = "🚨 MALICIOUS" if malicious > 0 else "🟡 SUSPICIOUS" if suspicious > 0 else "✅ CLEAN"
                        print(f"   {enrichment['hash'][:16]}... -> {status} (M:{malicious}, S:{suspicious})")
                    elif 'error' in enrichment:
                        print(f"   {enrichment['hash'][:16]}... -> ⚠️  {enrichment.get('message', 'Error')}")
    
    print(f"\n🔗 Webhook URL: {extractor.webhook_url}")
    print("✅ Hash extraction completed!")
    
    # Uncomment to send to webhook in production
    # for result in result_data:
    #     extractor.send_to_webhook(result)
