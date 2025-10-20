#!/usr/bin/env python3
"""
Feature 14: MITRE ATT&CK TTP Mapping
Maps behaviors and findings to MITRE ATT&CK techniques using pattern matching.
"""

import json
import re
import os
from collections import defaultdict
import requests  # Import the requests library for making HTTP requests

N8N_WEBHOOK_URL = "https://sipiv63984.app.n8n.cloud/webhook-test/mitre-attack"

class MitreAttackMapper:
    def __init__(self, dataset_file='mitre_attack_data.json'):
        self.dataset_file = dataset_file
        self.annotations = self.load_attack_data()

    def load_attack_data(self):
        """Load MITRE ATT&CK dataset"""
        if not os.path.exists(self.dataset_file):
            raise FileNotFoundError(f"Dataset file {self.dataset_file} not found. Please download it.")

        with open(self.dataset_file, 'r') as f:
            data = json.load(f)
        return data

    def map_to_ttp(self, description):
        """Map threat description to ATT&CK TTPs"""
        ttp_matches = defaultdict(list)
        
        for item in self.annotations:
            ttp_id = item['id']
            technique = item['technique']
            keywords = item['keywords']
            for keyword in keywords:
                if re.search(keyword, description, re.I):
                    ttp_matches[ttp_id].append(technique)

        return [{'ttp_id': ttp_id, 'techniques': list(set(techn))} for ttp_id, techn in ttp_matches.items()]

    def analyze(self, description):
        """Analyze the description and return TTP mappings"""
        matches = self.map_to_ttp(description)
        if matches:
            return {'description': description, 'mappings': matches}
        else:
            return {'description': description, 'mappings': []}
            
    def send_to_webhook(self, data):
        """Sends data to the configured n8n webhook."""
        try:
            response = requests.post(N8N_WEBHOOK_URL, json=data, timeout=10)
            # The following line will raise an exception for 4xx/5xx errors
            response.raise_for_status()  
            print(f"Successfully sent data to n8n. Status: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending data to n8n webhook: {e}")
            return False


if __name__ == '__main__':
    # Example usage
    example_description = "Threat actor utilized spear-phishing and credential dumping to gain initial access and escalate privileges."
    mapper = MitreAttackMapper()
    analysis = mapper.analyze(example_description)

    print("--- Analysis Result ---")
    print(json.dumps(analysis, indent=2))
    print("\n-------------------------\n")

    # --- START: Sending the result to the webhook ---
    print("Attempting to send result to n8n webhook...")
    if analysis.get('mappings'):  # Only send if there are actual matches
        mapper.send_to_webhook(analysis)
    else:
        print("No MITRE ATT&CK mappings found, skipping webhook.")
    # --- END: Sending the result to the webhook ---
