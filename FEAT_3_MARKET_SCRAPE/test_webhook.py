#!/usr/bin/env python3
"""
Test script to verify n8n webhook functionality
"""
import sys
import os
import requests
import json
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_n8n_webhook_url

# n8n Webhook URL
WEBHOOK_URL = get_n8n_webhook_url('market-scrape')

def test_webhook():
    """Test the n8n webhook with sample data"""
    test_payload = {
        "scraped_data": [
            {
                "title": "Test Product 1",
                "author": "Test Vendor",
                "price": "$50.00",
                "btc_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "scraped_at": datetime.now().isoformat(),
                "timestamp": 1234567890,
                "source_url": "test",
                "item_index": 0
            },
            {
                "title": "Test Product 2",
                "author": "Another Vendor",
                "price": "$75.00",
                "btc_address": "N/A",
                "scraped_at": datetime.now().isoformat(),
                "timestamp": 1234567891,
                "source_url": "test",
                "item_index": 1
            }
        ],
        "metadata": {
            "total_items": 2,
            "scrape_timestamp": datetime.now().isoformat(),
            "source_url": "test",
            "scraper_version": "1.0"
        }
    }
    
    try:
        print("Testing n8n webhook...")
        print(f"Webhook URL: {WEBHOOK_URL}")
        print(f"Payload: {json.dumps(test_payload, indent=2)}")
        
        response = requests.post(
            WEBHOOK_URL,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Webhook test SUCCESSFUL!")
        else:
            print("\n❌ Webhook test FAILED!")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_webhook()
