#!/usr/bin/env python3
"""
Test SOCKS connection through Tor
"""
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Proxy configuration
proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

def test_regular_connection():
    """Test regular connection through Tor"""
    try:
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=30)
        logger.info(f"Regular connection - IP: {response.json()}")
        return True
    except Exception as e:
        logger.error(f"Regular connection failed: {e}")
        return False

def test_onion_connection():
    """Test onion connection"""
    # Try a few different known .onion addresses
    onion_sites = [
        "http://duckduckgogg42ts72.onion",
        "http://3g2upl4pq6kufc4m.onion",  # Old DuckDuckGo
        "http://facebookcorewwwi.onion",  # Facebook
    ]
    
    for site in onion_sites:
        try:
            logger.info(f"Testing {site}")
            response = requests.get(site, proxies=proxies, timeout=60)
            logger.info(f"Success! {site} - Status: {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"Failed {site}: {e}")
    
    return False

if __name__ == "__main__":
    logger.info("Testing SOCKS connection...")
    
    if test_regular_connection():
        logger.info("✅ Regular connection through Tor works!")
    else:
        logger.error("❌ Regular connection failed")
    
    if test_onion_connection():
        logger.info("✅ Onion connection works!")
    else:
        logger.error("❌ All onion connections failed")
