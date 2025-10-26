#!/usr/bin/env python3
"""
Feature 6: IOC Extraction with Regex (Local Version)
Extracts Indicators of Compromise (IOCs) from raw text data using regex patterns
and saves the results to a local JSON file.
"""

import re
import sys
import json
import logging
from typing import Dict, List
from datetime import datetime
import os

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'ioc_extractor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IOCExtractor:
    """An IOC extraction engine using comprehensive regex patterns."""
    
    def __init__(self):
        """Initialize IOC extractor with compiled regex patterns."""
        self.patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compiles regex patterns for various IOC types."""
        return {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE),
            'ipv4': re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
            'bitcoin': re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|\bbc1[a-z0-9]{39,59}\b'),
            'ethereum': re.compile(r'\b0x[a-fA-F0-9]{40}\b'),
            'md5': re.compile(r'\b[a-fA-F0-9]{32}\b'),
            'sha1': re.compile(r'\b(?<!0x)[a-fA-F0-9]{40}\b', re.IGNORECASE),
            'sha256': re.compile(r'\b[a-fA-F0-9]{64}\b'),
            'url': re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?', re.IGNORECASE),
            'onion': re.compile(r'\b[a-z2-7]{16,56}\.onion\b', re.IGNORECASE),
            'domain': re.compile(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'),
            'cve': re.compile(r'\bCVE-\d{4}-\d{4,7}\b', re.IGNORECASE),
        }
    
    def extract_iocs(self, text: str) -> Dict[str, List[str]]:
        """Extracts all IOCs from the given text."""
        if not text or not isinstance(text, str):
            logger.warning("Empty or invalid text provided for IOC extraction.")
            return {}
        
        results = {}
        for ioc_type, pattern in self.patterns.items():
            matches = list(dict.fromkeys(pattern.findall(text)))
            if matches:
                results[ioc_type] = matches
        return results
    
    def validate_iocs(self, iocs: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Applies additional filtering to reduce false positives."""
        validated = {}
        for ioc_type, values in iocs.items():
            valid_values = [value for value in values if self._is_valid_ioc(ioc_type, value)]
            if valid_values:
                validated[ioc_type] = valid_values
        return validated
    
    def _is_valid_ioc(self, ioc_type: str, value: str) -> bool:
        """Additional validation logic for specific IOC types."""
        if ioc_type == 'ipv4':
            octets = [int(x) for x in value.split('.')]
            if (octets[0] == 10 or (octets[0] == 172 and 16 <= octets[1] <= 31) or
                (octets[0] == 192 and octets[1] == 168) or octets[0] in [0, 127, 224]):
                return False
        
        if ioc_type == 'domain' and (len(value) < 4 or value.count('.') < 1):
            return False
        
        if ioc_type in ['md5', 'sha1', 'sha256'] and len(set(value.lower())) < 4:
            return False
            
        return True
    
    def process_text(self, text: str) -> Dict:
        """Runs the complete IOC extraction and validation pipeline."""
        logger.info("Starting IOC extraction process...")
        raw_iocs = self.extract_iocs(text)
        if not raw_iocs:
            logger.warning("No potential IOCs found in the provided text.")
            return {}
        
        valid_iocs = self.validate_iocs(raw_iocs)
        logger.info(f"Extraction complete. Found {sum(len(v) for v in valid_iocs.values())} valid IOCs.")
        return valid_iocs

def save_results(data: Dict, source_identifier: str = "local_text"):
    """Saves the extracted IOCs to a JSON file in the 'output' directory."""
    if not data:
        logger.warning("No valid IOCs found, nothing to save.")
        return

    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_6_extracted_iocs.json')
        
        final_payload = {
            "feature_name": "IOC Extractor",
            "execution_timestamp": datetime.now().isoformat(),
            "source": source_identifier,
            "total_iocs_found": sum(len(values) for values in data.values()),
            "ioc_counts": {k: len(v) for k, v in data.items()},
            "iocs": data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

if __name__ == "__main__":
    sample_text = """
    From: attacker@evil-corp.com, related to CVE-2021-44228.
    Our C2 server is at 198.51.100.25 and also malicious-site.net.
    Download from http://phishing-link.com/download.exe.
    File hash is d41d8cd98f00b204e9800998ecf8427e.
    Payment address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
    Also check our hidden service at 3g2upl4pq6kufc4m.onion.
    """
    
    logger.info("🚀 Initializing IOC Extractor...")
    extractor = IOCExtractor()
    
    # Process the text
    extracted_iocs = extractor.process_text(sample_text)
    
    if extracted_iocs:
        save_results(extracted_iocs, source_identifier="main_script_sample_text")
        print("\n--- IOC Extraction Complete ---")
        print(json.dumps(extracted_iocs, indent=2))
        print("------------------------------")
    else:
        logger.info("No IOCs were extracted from the sample text.")
