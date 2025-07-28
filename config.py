#!/usr/bin/env python3
"""
Configuration utility for loading environment variables and sensitive data
"""

import os
from dotenv import load_dotenv

# Load environment variables from .secrets.env file
load_dotenv('.secrets.env')

def get_n8n_webhook_url(endpoint_name: str) -> str:
    """
    Construct n8n webhook URL from account and endpoint name
    
    Args:
        endpoint_name: The webhook endpoint name (e.g., 'tor-relays', 'market-scrape')
    
    Returns:
        Complete webhook URL
    """
    account = os.getenv('N8N_ACCOUNT', 'sipiv63984.app.n8n.cloud')
    return f"https://{account}/webhook-test/{endpoint_name}"

def get_tor_password() -> str:
    """Get Tor control password from environment"""
    return os.getenv('TOR_PASSWORD', 'TorRelay123')

def get_api_key(service: str) -> str:
    """
    Get API key for a specific service
    
    Args:
        service: Service name (e.g., 'virustotal', 'abuseipdb', 'shodan')
    
    Returns:
        API key or empty string if not found
    """
    return os.getenv(f'{service.upper()}_API_KEY', '')

# Common configuration
TOR_CONTROL_PORT = 9051
TOR_SOCKS_PROXY = '127.0.0.1:9050'
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
