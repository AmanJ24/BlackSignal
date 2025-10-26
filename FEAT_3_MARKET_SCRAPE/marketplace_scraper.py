#!/usr/bin/env python3
"""
Feature 3: Marketplace Scraper
A resilient, local-only scraper for extracting vendor and product intelligence
from .onion marketplaces.
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json
import logging
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import TOR_SOCKS_PROXY
except ImportError:
    TOR_SOCKS_PROXY = "127.0.0.1:9050"

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'marketplace_scraper.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# In a real pipeline, you would pass this URL as an argument
TARGET_URL = "http://dreadytofatroptsdj6io7l3xptbet6onoyno2yv7jicoxknyazubrad.onion/d/Locker01" # Example: Dread Forum

# Request headers to appear more like a regular browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def create_session() -> requests.Session:
    """Creates a requests session with a retry strategy and Tor proxy."""
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    
    if '.onion' in TARGET_URL:
        session.proxies = {
            'http': f'socks5h://{TOR_SOCKS_PROXY}',
            'https': f'socks5h://{TOR_SOCKS_PROXY}'
        }
        logger.info(f"Using Tor proxy ({TOR_SOCKS_PROXY}) for .onion site.")
    else:
        logger.info("Using direct connection (non-onion URL).")
    
    return session

def test_tor_connection() -> bool:
    """Tests the Tor SOCKS proxy connection by checking the external IP."""
    logger.info("Testing Tor connection...")
    try:
        session = create_session()
        response = session.get("http://httpbin.org/ip", timeout=30)
        tor_ip = response.json().get('origin')
        
        # Now check clearnet IP
        clearnet_session = requests.Session()
        response = clearnet_session.get("http://httpbin.org/ip", timeout=10)
        clearnet_ip = response.json().get('origin')

        if tor_ip != clearnet_ip:
            logger.info(f"✅ Tor connection successful. Your IP appears as: {tor_ip}")
            return True
        else:
            logger.error("❌ Tor connection test failed. Scraper is not routing through Tor.")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

def extract_market_data(session: requests.Session) -> List[Dict]:
    """Extracts structured data from the target marketplace URL."""
    try:
        logger.info(f"Starting scrape of {TARGET_URL}")
        response = session.get(TARGET_URL, timeout=60)
        response.raise_for_status()
        logger.info(f"Successfully fetched page (Status: {response.status_code})")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # --- NOTE: The selectors below are generic. They MUST be adapted for a real target site. ---
        marketplace_selectors = ["div.listing", "div.product", "div.item", "article.post"]
        post_blocks = []
        for selector in marketplace_selectors:
            blocks = soup.select(selector)
            if blocks:
                logger.info(f"Found {len(blocks)} items using selector: '{selector}'")
                post_blocks = blocks
                break
        
        if not post_blocks:
            logger.warning("No structured product listings found. The selectors may need to be updated for this specific marketplace.")
            return []

        items = []
        for i, post in enumerate(post_blocks[:20]):  # Limit to 20 items for demonstration
            title_selectors = [".title", "h1", "h2", "h3"]
            author_selectors = [".vendor", ".author", ".seller"]
            price_selectors = [".price", ".cost"]
            
            title = next((post.select_one(s).get_text(strip=True) for s in title_selectors if post.select_one(s)), "Unknown Title")
            author = next((post.select_one(s).get_text(strip=True) for s in author_selectors if post.select_one(s)), "Unknown Vendor")
            price = next((post.select_one(s).get_text(strip=True) for s in price_selectors if post.select_one(s)), "N/A")
            
            # Extract raw text content for later analysis
            full_text = post.get_text(separator=" ", strip=True)

            item_data = {
                "title": title,
                "vendor_handle": author,
                "price": price,
                "full_text_content": full_text,
                "source_url": TARGET_URL,
                "item_index": i
            }
            items.append(item_data)
            logger.info(f"Extracted item {i+1}: '{title[:40]}...' by '{author}'")
        
        return items
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error scraping target: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {e}")
        return []

def save_results(data: List[Dict]):
    """Saves the scraped data to a JSON file in the 'output' directory."""
    if not data:
        logger.warning("No data scraped, nothing to save.")
        return

    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_3_marketplace_scrape.json')
        
        final_payload = {
            "feature_name": "Marketplace Scraper",
            "execution_timestamp": datetime.now().isoformat(),
            "source_url": TARGET_URL,
            "items_scraped": len(data),
            "scraped_items": data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

def main():
    """Main execution function for the marketplace scraper."""
    logger.info("🚀 Starting Feature 3: Marketplace Scraper...")
    if not test_tor_connection():
        logger.critical("Tor is not configured correctly. Aborting scrape.")
        return

    session = create_session()
    scraped_items = extract_market_data(session)
    
    if scraped_items:
        save_results(scraped_items)
    else:
        logger.warning("Scraping finished with no items extracted.")
        
    logger.info("✅ Marketplace scraping process completed.")

if __name__ == "__main__":
    main()
