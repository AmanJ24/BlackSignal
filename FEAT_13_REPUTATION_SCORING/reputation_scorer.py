#!/usr/bin/env python3
"""
Feature 13: Reputation Scoring Service
Calculates reputation scores for vendors based on feedback and transaction data.
Receives data via API endpoint and sends results to an n8n webhook.
"""

import json
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import sys
import os

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_n8n_webhook_url

# --- Flask App Setup ---
app = Flask(__name__)

# --- Webhook Configuration ---
N8N_WEBHOOK_URL = get_n8n_webhook_url('reputation-scoring')

def calculate_reputation(vendor_data):
    """Calculates a more robust reputation score."""
    # Base score starts at 50 (neutral)
    score = 50
    
    positive = vendor_data.get('positive_feedback', 0)
    negative = vendor_data.get('negative_feedback', 0)
    total_feedback = positive + negative
    
    # Heavily penalize negative feedback
    score -= negative * 5
    
    # Reward positive feedback, but less heavily
    score += positive * 2
    
    # Factor in the ratio of positive to negative feedback
    if total_feedback > 0:
        feedback_ratio = positive / total_feedback
        if feedback_ratio > 0.95:
            score += 10 # Bonus for excellent ratio
        elif feedback_ratio < 0.8:
            score -= 15 # Penalty for poor ratio

    # Add points for vendor history (e.g., age in months)
    first_seen_str = vendor_data.get('first_seen')
    if first_seen_str:
        try:
            first_seen_date = datetime.fromisoformat(first_seen_str.replace('Z', ''))
            age_months = (datetime.now() - first_seen_date).days / 30
            score += min(age_months, 12) # Add 1 point per month, capped at 12
        except:
            pass # Ignore if date format is wrong
            
    # Cap the score between 0 and 100
    return max(0, min(100, int(score)))

def send_to_webhook(data):
    """Sends the processed data to the n8n webhook."""
    if not N8N_WEBHOOK_URL:
        print("Webhook URL not configured. Skipping.")
        return
    try:
        payload = {
            "feature": "Reputation Scoring",
            "timestamp": datetime.now().isoformat(),
            "vendor_scores": data
        }
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=15)
        response.raise_for_status()
        print(f"✅ Successfully sent {len(data)} reputation scores to n8n.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send data to webhook: {e}")

@app.route('/calculate-reputation', methods=['POST'])
def process_vendor_data():
    """API endpoint to process vendor data and calculate reputation."""
    vendor_data_list = request.get_json()
    if not isinstance(vendor_data_list, list):
        return jsonify({"error": "Request body must be a JSON array of vendor objects"}), 400
        
    results = []
    for vendor in vendor_data_list:
        try:
            reputation_score = calculate_reputation(vendor)
            vendor['reputation_score'] = reputation_score
            results.append(vendor)
        except Exception as e:
            print(f"Could not process vendor '{vendor.get('vendor_handle')}': {e}")

    # Send the results to the next webhook in the pipeline
    if results:
        send_to_webhook(results)
    
    return jsonify(results)

if __name__ == '__main__':
    # This block allows you to test the service locally
    # To use: run `python reputation_scorer.py`
    # Then, send a POST request to http://127.0.0.1:5001/calculate-reputation
    # with a JSON body like the content of 'vendor_data.json'.
    print("🚀 Reputation Scoring Service running on http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001)```
