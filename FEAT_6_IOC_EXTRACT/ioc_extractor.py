#!/usr/bin/env python3
"""
Feature 6: IOC Extraction with Regex
=====================================

This script extracts Indicators of Compromise (IOCs) from raw text data using regex patterns.
Supports: Email addresses, IP addresses, Bitcoin addresses, file hashes (MD5/SHA256/SHA1),
URLs, domains, phone numbers, credit card numbers, and more.

Author: Aman
Date: 2025-07-30
"""

import re
import sys
import json
import requests
import logging
from typing import Dict, List, Set, Any
from datetime import datetime
import os
from webhook_config import get_webhook_url, is_webhook_configured, WEBHOOK_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/ioc_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IOCExtractor:
    """
    Advanced IOC extraction engine using comprehensive regex patterns
    """
    
    def __init__(self):
        """Initialize IOC extractor with compiled regex patterns"""
        self.patterns = self._compile_patterns()
        self.webhook_url = get_webhook_url()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """
        Compile all regex patterns for different IOC types
        
        Returns:
            Dictionary of compiled regex patterns
        """
        patterns = {
            # Email addresses
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            
            # IPv4 addresses
            'ipv4': re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),
            
            # IPv6 addresses (simplified pattern)
            'ipv6': re.compile(
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|' +
                r'\b::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b|' +
                r'\b[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}\b'
            ),
            
            # Bitcoin addresses (Legacy, SegWit, Bech32)
            'bitcoin': re.compile(
                r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|' +  # Legacy P2PKH/P2SH
                r'\bbc1[a-z0-9]{39,59}\b'                   # Bech32 SegWit
            ),
            
            # Ethereum addresses
            'ethereum': re.compile(
                r'\b0x[a-fA-F0-9]{40}\b'
            ),
            
            # MD5 hashes
            'md5': re.compile(
                r'\b[a-fA-F0-9]{32}\b'
            ),
            
            # SHA1 hashes
            'sha1': re.compile(
                 r'\b(?<!0x)[a-fA-F0-9]{40}\b', re.IGNORECASE
            ),
            
            # SHA256 hashes
            'sha256': re.compile(
                r'\b[a-fA-F0-9]{64}\b'
            ),
            
            # URLs (HTTP/HTTPS)
            'url': re.compile(
                r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
                re.IGNORECASE
            ),
            
            # .onion domains
            'onion': re.compile(
                r'\b[a-z2-7]{16,56}\.onion\b',
                re.IGNORECASE
            ),
            
            # Domain names
            'domain': re.compile(
                r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
            ),
            
            # Phone numbers (international format)
            'phone': re.compile(
                r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b|' +
                r'\+[1-9]\d{1,14}\b'
            ),
            
            # Credit card numbers (basic pattern)
            'credit_card': re.compile(
                r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'
            ),
            
            # Social Security Numbers (US format)
            'ssn': re.compile(
                r'\b\d{3}-\d{2}-\d{4}\b'
            ),
            
            # Registry keys (Windows)
            'registry': re.compile(
                r'HKEY_(?:CLASSES_ROOT|CURRENT_USER|LOCAL_MACHINE|USERS|CURRENT_CONFIG)\\[\\a-zA-Z0-9_\s-]+',
                re.IGNORECASE
            ),
            
            # File paths (Windows/Unix)
            'filepath': re.compile(
                r'(?:[a-zA-Z]:\\[\\\w\s.-]+|/[\w\s./-]+)',
                re.IGNORECASE
            ),
            
            # MAC addresses
            'mac_address': re.compile(
                r'\b[0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}\b'
            ),
            
            # CVE identifiers
            'cve': re.compile(
                r'\bCVE-\d{4}-\d{4,7}\b',
                re.IGNORECASE
            ),
            
            # User agents (partial pattern)
            'user_agent': re.compile(
                r'(?:Mozilla|Chrome|Safari|Opera|Edge)/[\d.]+',
                re.IGNORECASE
            )
        }
        
        return patterns
    
    def extract_iocs(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all IOCs from the given text
        
        Args:
            text: Raw text data to analyze
            
        Returns:
            Dictionary containing lists of extracted IOCs by type
        """
        if not text or not isinstance(text, str):
            logger.warning("Empty or invalid text provided for IOC extraction")
            return {}
        
        results = {}
        
        # Extract IOCs for each pattern type
        for ioc_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Remove duplicates while preserving order
                unique_matches = list(dict.fromkeys(matches))
                results[ioc_type] = unique_matches
                logger.info(f"Extracted {len(unique_matches)} {ioc_type} IOCs")
        
        return results
    
    def validate_iocs(self, iocs: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Validate and filter extracted IOCs
        
        Args:
            iocs: Dictionary of extracted IOCs
            
        Returns:
            Dictionary of validated IOCs
        """
        validated = {}
        
        for ioc_type, values in iocs.items():
            valid_values = []
            
            for value in values:
                if self._is_valid_ioc(ioc_type, value):
                    valid_values.append(value)
                else:
                    logger.debug(f"Invalid {ioc_type} IOC filtered: {value}")
            
            if valid_values:
                validated[ioc_type] = valid_values
        
        return validated
    
    def _is_valid_ioc(self, ioc_type: str, value: str) -> bool:
        """
        Additional validation for specific IOC types
        
        Args:
            ioc_type: Type of IOC
            value: IOC value to validate
            
        Returns:
            True if IOC is valid, False otherwise
        """
        # Skip validation for private/reserved IP ranges for IPv4
        if ioc_type == 'ipv4':
            octets = [int(x) for x in value.split('.')]
            # Skip private ranges: 10.x.x.x, 172.16-31.x.x, 192.168.x.x
            # Skip localhost, multicast, etc.
            if (octets[0] == 10 or 
                (octets[0] == 172 and 16 <= octets[1] <= 31) or
                (octets[0] == 192 and octets[1] == 168) or
                octets[0] in [127, 169, 224, 239, 255]):
                return False
        
        # Skip short domains that might be false positives
        if ioc_type == 'domain':
            if len(value) < 4 or value.count('.') < 1:
                return False
            # Skip common file extensions misidentified as domains
            if value.split('.')[-1].lower() in ['exe', 'dll', 'bat', 'cmd', 'ps1', 'sh']:
                return False
        
        # Skip weak hashes (all same character, too short, etc.)
        if ioc_type in ['md5', 'sha1', 'sha256']:
            if len(set(value.lower())) < 3:  # Too few unique characters
                return False
        
        return True
    
    def enrich_iocs(self, iocs: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Add metadata and context to extracted IOCs
        
        Args:
            iocs: Dictionary of extracted IOCs
            
        Returns:
            Enriched IOC data with metadata
        """
        enriched = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_iocs': sum(len(values) for values in iocs.values()),
            'ioc_types_found': list(iocs.keys()),
            'iocs': iocs,
            'statistics': {}
        }
        
        # Generate statistics
        for ioc_type, values in iocs.items():
            enriched['statistics'][ioc_type] = {
                'count': len(values),
                'unique_count': len(set(values)),
                'sample': values[:3] if values else []  # First 3 as sample
            }
        
        return enriched
    
    def send_to_webhook(self, data: Dict[str, Any]) -> bool:
        """
        Send extracted IOCs to n8n webhook
        
        Args:
            data: IOC data to send
            
        Returns:
            True if successful, False otherwise
        """
        if not is_webhook_configured():
            logger.warning("Webhook is not configured. Skipping sending data.")
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=data,
                headers=WEBHOOK_CONFIG['headers'],
                timeout=WEBHOOK_CONFIG['timeout']
            )
            response.raise_for_status()
            
            logger.info(f"Successfully sent IOC data to webhook: {response.status_code}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send data to webhook: {e}")
            return False
    
    def process_text(self, text: str, send_webhook: bool = True) -> Dict[str, Any]:
        """
        Complete IOC extraction pipeline
        
        Args:
            text: Raw text to process
            send_webhook: Whether to send results to n8n webhook
            
        Returns:
            Complete extraction results
        """
        logger.info("Starting IOC extraction process")
        
        # Step 1: Extract IOCs
        raw_iocs = self.extract_iocs(text)
        
        if not raw_iocs:
            logger.warning("No IOCs found in provided text")
            return {'message': 'No IOCs found', 'timestamp': datetime.utcnow().isoformat()}
        
        # Step 2: Validate IOCs
        valid_iocs = self.validate_iocs(raw_iocs)
        
        # Step 3: Enrich with metadata
        enriched_data = self.enrich_iocs(valid_iocs)
        
        # Step 4: Send to webhook if requested
        if send_webhook:
            self.send_to_webhook(enriched_data)
        
        logger.info(f"IOC extraction completed. Found {enriched_data['total_iocs']} IOCs across {len(enriched_data['ioc_types_found'])} types")
        
        return enriched_data

if __name__ == "__main__":
    # Sample text containing various IOCs for demonstration
    sample_text = """
    From: attacker@evil-corp.com
    To: victim@example.com
    
    Please review the attached invoice. It is not a virus.
    Our new payment address is 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa.
    
    Our C2 server is located at 198.51.100.25 and also at malicious-site.net.
    You can download the file from http://phishing-link.com/download.exe.
    The file hash is d41d8cd98f00b204e9800998ecf8427e.
    Also check our hidden service at 3g2upl4pq6kufc4m.onion.
    """
    
    logger.info("Initializing IOC Extractor...")
    extractor = IOCExtractor()
    
    # Process the text and send results to the webhook
    results = extractor.process_text(sample_text, send_webhook=True)
    
    logger.info("--- IOC Extraction Complete ---")
    print(json.dumps(results, indent=2))
    logger.info("--- End of Report ---")
