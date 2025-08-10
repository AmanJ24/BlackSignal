#!/usr/bin/env python3
"""
Webhook Configuration for Feature 6: IOC Extraction
===================================================

Update the WEBHOOK_URL below with your n8n webhook endpoint.
This file is separate from the main script to make updates easier.
"""

# TODO: Update this with your actual n8n webhook URL
# Format: https://your-n8n-instance.app.n8n.cloud/webhook-test/ioc-extract
WEBHOOK_URL = "YOUR_N8N_WEBHOOK_URL_HERE"

# Webhook configuration
WEBHOOK_CONFIG = {
    "url": WEBHOOK_URL,
    "timeout": 30,
    "headers": {
        "Content-Type": "application/json",
        "User-Agent": "IOC-Extractor/1.0"
    }
}

def get_webhook_url():
    """
    Get the configured webhook URL
    
    Returns:
        str: Webhook URL or None if not configured
    """
    if WEBHOOK_URL == "YOUR_N8N_WEBHOOK_URL_HERE":
        return None
    return WEBHOOK_URL

def is_webhook_configured():
    """
    Check if webhook is properly configured
    
    Returns:
        bool: True if webhook is configured, False otherwise
    """
    return WEBHOOK_URL != "YOUR_N8N_WEBHOOK_URL_HERE"
