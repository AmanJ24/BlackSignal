#!/usr/bin/env python3
"""
Feature 13: Reputation Scoring Service
Calculates reputation scores for vendors based on feedback and transaction data.
Receives data via API endpoint and sends results to an n8n webhook.
"""

import json
import os
from datetime import datetime

def calculate_reputation(vendor_data):
    """Calculates a more robust reputation score."""
    score = 50
    positive = vendor_data.get('positive_feedback', 0)
    negative = vendor_data.get('negative_feedback', 0)
    total_feedback = positive + negative
    score -= negative * 5
    score += positive * 2
    if total_feedback > 0:
        feedback_ratio = positive / total_feedback
        if feedback_ratio > 0.95:
            score += 10
        elif feedback_ratio < 0.8:
            score -= 15
    first_seen_str = vendor_data.get('first_seen')
    if first_seen_str:
        try:
            first_seen_date = datetime.fromisoformat(first_seen_str.replace('Z', ''))
            age_months = (datetime.now() - first_seen_date).days / 30
            score += min(age_months, 12)
        except:
            pass
    return max(0, min(100, int(score)))

def process_vendor_data(input_file, output_file):
    """Processes vendor data and calculates reputation score"""
    try:
        with open(input_file, 'r') as file:
            vendors = json.load(file)
        
        results = []
        for vendor in vendors:
            reputation_score = calculate_reputation(vendor)
            vendor['reputation_score'] = reputation_score
            results.append(vendor)
        
        # --- Make sure the output directory exists ---
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as file:
            json.dump(results, file, indent=4)
        
        print(f"🎉 Reputation scores calculated and saved to {output_file}")
        
    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found")
    except json.JSONDecodeError:
        print(f"❌ Error: Failed to decode JSON from {input_file}")

if __name__ == "__main__":
    # Define paths relative to the project root
    # NOTE: This assumes you have a sample 'vendor_data.json' in an 'input' or 'docs' folder
    # For now, we will assume it's in the feature folder for simplicity of testing.
    input_file = 'vendor_data.json' 
    output_file = os.path.join(os.path.dirname(__file__), '..', 'output', 'vendor_reputation_scores.json')
    
    # Create a dummy input file if it doesn't exist for testing
    if not os.path.exists(input_file):
        dummy_data = [{"vendor_handle": "TestVendor", "positive_feedback": 100, "negative_feedback": 2, "first_seen": "2023-01-01T12:00:00Z"}]
        with open(input_file, 'w') as f:
            json.dump(dummy_data, f)
        print(f"Created dummy '{input_file}' for testing.")
            
    process_vendor_data(input_file, output_file)
