#!/usr/bin/env python3
"""
Feature 14: MITRE ATT&CK TTP Mapping (Local Version)

Maps threat descriptions to MITRE ATT&CK techniques using keyword pattern matching
and saves the results to a local JSON file.
"""

import json
import re
import os
import sys
import logging
from collections import defaultdict
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'mitre_mapper.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MitreAttackMapper:
    """Maps text to MITRE ATT&CK techniques."""

    def __init__(self, dataset_file: str = 'mitre_attack_data.json'):
        """Initializes the mapper with a dataset of techniques and keywords."""
        self.dataset_file = os.path.join(os.path.dirname(__file__), dataset_file)
        self.ttp_data = self._load_attack_data()
        logger.info(f"Loaded {len(self.ttp_data)} MITRE ATT&CK techniques.")

    def _load_attack_data(self) -> List[Dict]:
        """Loads the MITRE ATT&CK dataset from a local JSON file."""
        if not os.path.exists(self.dataset_file):
            # --- REMOVE DUMMY DATA CREATION ---
            logger.critical(f"CRITICAL: MITRE dataset '{self.dataset_file}' not found. This feature cannot run.")
            raise FileNotFoundError(f"'{self.dataset_file}' is required for MITRE mapping.")
        
        with open(self.dataset_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyzes a text description and returns any TTP mappings."""
        ttp_matches = defaultdict(lambda: {'techniques': set()})
        
        for item in self.ttp_data:
            ttp_id = item['id']
            technique = item['technique']
            for keyword in item['keywords']:
                if re.search(keyword, text, re.IGNORECASE):
                    ttp_matches[ttp_id]['techniques'].add(technique)

        # Convert sets to sorted lists for consistent JSON output
        mappings = [
            {'ttp_id': ttp_id, 'techniques': sorted(list(details['techniques']))}
            for ttp_id, details in ttp_matches.items()
        ]

        return {
            "text_snippet": text[:250] + "..." if len(text) > 250 else text,
            "mappings_found": len(mappings),
            "mappings": mappings
        }

def save_results(data: List[Dict]):
    """Saves the MITRE mapping results to a JSON file."""
    if not any(item['mappings_found'] > 0 for item in data):
        logger.warning("No MITRE mappings were found, nothing to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_14_mitre_attack_mappings.json')
        
        final_payload = {
            "feature_name": "MITRE ATT&CK TTP Mapping",
            "execution_timestamp": datetime.now().isoformat(),
            "entries_analyzed": len(data),
            "analysis_results": data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Feature 14: MITRE ATT&CK TTP Mapping...")
    
    # In a pipeline, this would come from the output of another feature.
    # We create a dummy list of texts for standalone testing.
    sample_texts = [
        {
            "source": "Threat Report #1",
            "text": "The threat actor gained initial access via a spear-phishing campaign. Later, they performed OS credential dumping using PowerShell scripts."
        },
        {
            "source": "Marketplace Post",
            "text": "Selling a new exploit that uses cmd.exe to escalate privileges. No phishing needed."
        },
        {
            "source": "Forum Comment",
            "text": "This is a generic comment with no indicators."
        }
    ]

    try:
        mapper = MitreAttackMapper()
        all_results = []
        
        logger.info(f"Analyzing {len(sample_texts)} text entries...")
        for entry in sample_texts:
            logger.info(f"--- Analyzing text from '{entry['source']}' ---")
            analysis = mapper.analyze_text(entry['text'])
            analysis['source'] = entry['source'] # Add source context to the result
            all_results.append(analysis)
            print(json.dumps(analysis, indent=2))
        
        if all_results:
            save_results(all_results)
            
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}")

    logger.info("✅ MITRE ATT&CK mapping complete.")
