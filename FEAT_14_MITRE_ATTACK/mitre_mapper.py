#!/usr/bin/env python3
"""
Feature 14: MITRE ATT&CK TTP Mapping
Maps behaviors and findings to MITRE ATT&CK techniques using pattern matching.
"""

import json
import re
import os
from collections import defaultdict

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


if __name__ == '__main__':
    # Example usage
    example_description = "Threat actor utilized spear-phishing and credential dumping."
    mapper = MitreAttackMapper()
    analysis = mapper.analyze(example_description)

    print("Analysis Result:")
    print(json.dumps(analysis, indent=2))
