
import sys
import os
import requests
from bs4 import BeautifulSoup

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_n8n_webhook_url, TOR_SOCKS_PROXY
from datetime import datetime
import time
import json
import logging
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('marketplace_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Proxy configuration to route through Tor
proxies = {
    'http': f'socks5h://{TOR_SOCKS_PROXY}',
    'https': f'socks5h://{TOR_SOCKS_PROXY}'
}

# Target .onion site for testing - using legitimate site
# For actual marketplace, replace with your specific .onion URL
TARGET_URL = "https://3g2upl4pq6kufc4m.onion"  # DuckDuckGo onion (legitimate test)

# n8n Webhook URL
WEBHOOK_URL = get_n8n_webhook_url('market-scrape')

# Request headers to appear more like a regular browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def create_session(use_tor=False):
    """Create a requests session with retry strategy and proper configuration"""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set headers
    session.headers.update(headers)
    
    # Only use Tor proxy for .onion sites
    if use_tor or '.onion' in TARGET_URL:
        session.proxies.update(proxies)
        logger.info("Using Tor proxy for connection")
    else:
        logger.info("Using direct connection (no proxy)")
    
    return session

def test_connection():
    """Test if connection is working"""
    try:
        session = create_session()
        response = session.get("http://httpbin.org/ip", timeout=30)
        ip = response.json().get('origin')
        logger.info(f"Connection test successful - IP: {ip}")
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

def extract_market_data():
    """Extract market data from the target marketplace"""
    try:
        logger.info(f"Starting scrape of {TARGET_URL}")
        session = create_session()
        
        # Make request with proper error handling
        response = session.get(TARGET_URL, timeout=60)
        response.raise_for_status()
        
        logger.info(f"Successfully fetched page - Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Log page structure for debugging
        logger.info(f"Page title: {soup.title.string if soup.title else 'No title'}")
        logger.info(f"Page contains {len(soup.find_all())} HTML elements")
        
        # Extract marketplace data - Dark web marketplace selectors
        items = []
        
        # Common dark web marketplace selectors for product listings
        marketplace_selectors = [
            "div.listing",          # Common marketplace listing
            "div.product",          # Product container
            "div.item",             # Item container
            "tr.listing-row",       # Table row format
            "div[class*='listing']", # Any class containing 'listing'
            "div[class*='product']", # Any class containing 'product'
            "div[class*='item']",    # Any class containing 'item'
            ".post",                # Post format
            "article",              # Article elements
            "[data-item]",          # Data attributes
            "[id*='item']",         # IDs containing 'item'
        ]
        
        post_blocks = []
        for selector in marketplace_selectors:
            try:
                blocks = soup.select(selector)
                if blocks and len(blocks) > 1:  # Ensure we have multiple items
                    logger.info(f"Found {len(blocks)} items using marketplace selector: {selector}")
                    # Debug: show first item structure
                    if blocks:
                        first_item = blocks[0]
                        logger.debug(f"First item classes: {first_item.get('class', [])}")
                        logger.debug(f"First item HTML snippet: {str(first_item)[:300]}...")
                    post_blocks = blocks
                    break
            except Exception as e:
                logger.debug(f"Marketplace selector {selector} failed: {e}")
        
        # If no structured listings found, try to find any content blocks
        if not post_blocks:
            logger.warning("No structured listings found, analyzing page content...")
            # Look for any divs that might contain listings
            all_divs = soup.find_all("div", limit=50)
            logger.debug(f"Found {len(all_divs)} div elements total")
            
            # Try to find divs with multiple similar patterns
            potential_listings = []
            for div in all_divs:
                text = div.get_text(strip=True)
                # Look for divs that might contain price/bitcoin indicators
                if any(keyword in text.lower() for keyword in ['btc', 'bitcoin', '$', 'price', 'vendor', 'seller']):
                    potential_listings.append(div)
            
            if potential_listings:
                logger.info(f"Found {len(potential_listings)} potential listing elements")
                post_blocks = potential_listings[:20]  # Limit to first 20
        
        if not post_blocks:
            logger.warning("No product listings found with any selector")
            return []
        
        logger.info(f"Processing {len(post_blocks)} potential listings...")
        
        for i, post in enumerate(post_blocks[:20]):  # Limit to first 20 items
            try:
                # Dark web marketplace selectors for required fields
                title_selectors = [
                    "h1", "h2", "h3", "h4", "h5",       # Standard headings
                    ".title", ".name", ".product-name",  # Common title classes
                    "[class*='title']", "[class*='name']", # Any class with title/name
                    ".listing-title", ".item-title",      # Listing specific
                    "a",                                 # Links might contain titles
                    "strong", "b",                       # Bold text
                    "[data-title]", "[title]"             # Data attributes
                ]
                
                author_selectors = [
                    ".author", ".vendor", ".seller",       # Standard author/vendor classes
                    "[class*='author']", "[class*='vendor']", "[class*='seller']",
                    ".user", ".username", ".by",          # User identification
                    "[class*='user']", "[data-vendor]"    # Data attributes
                ]
                
                price_selectors = [
                    ".price", ".cost", ".amount",         # Standard price classes
                    "[class*='price']", "[class*='cost']", # Any class with price/cost
                    ".btc-price", ".usd-price",          # Crypto specific
                    "[data-price]", "[data-cost]"         # Data attributes
                ]
                
                btc_selectors = [
                    ".btc", ".bitcoin", ".btc-address",   # Bitcoin specific classes
                    "[class*='btc']", "[class*='bitcoin']", # Any class with btc/bitcoin
                    ".address", ".wallet",               # Wallet/address classes
                    "[class*='address']", "[class*='wallet']",
                    "[data-btc]", "[data-bitcoin]"        # Data attributes
                ]
                
                # Extract title
                title = "Unknown"
                for selector in title_selectors:
                    element = post.select_one(selector)
                    if element and element.get_text(strip=True):
                        title_text = element.get_text(strip=True)
                        if len(title_text) > 5 and len(title_text) < 200:  # Reasonable title length
                            title = title_text
                            break
                
                # Extract author/vendor
                author = "Unknown"
                for selector in author_selectors:
                    element = post.select_one(selector)
                    if element and element.get_text(strip=True):
                        author_text = element.get_text(strip=True)
                        if len(author_text) > 1 and len(author_text) < 50:  # Reasonable author length
                            author = author_text
                            break
                
                # Extract price
                price = "N/A"
                for selector in price_selectors:
                    element = post.select_one(selector)
                    if element and element.get_text(strip=True):
                        price_text = element.get_text(strip=True)
                        # Look for currency symbols or 'btc'
                        if any(symbol in price_text.lower() for symbol in ['$', '€', '£', 'btc', 'usd', 'eur']):
                            price = price_text
                            break
                
                # Also search in the full text for price patterns
                if price == "N/A":
                    full_text = post.get_text()
                    # Look for price patterns like $XX.XX, XXX BTC, etc.
                    price_patterns = [
                        r'\$\d+(?:\.\d+)?',          # $XX.XX
                        r'\d+(?:\.\d+)?\s*BTC',      # XX.XX BTC
                        r'\d+(?:\.\d+)?\s*USD',      # XX.XX USD
                        r'\d+(?:\.\d+)?\s*EUR',      # XX.XX EUR
                    ]
                    for pattern in price_patterns:
                        match = re.search(pattern, full_text, re.IGNORECASE)
                        if match:
                            price = match.group()
                            break
                
                # Extract BTC address
                btc_address = "N/A"
                for selector in btc_selectors:
                    element = post.select_one(selector)
                    if element and element.get_text(strip=True):
                        btc_text = element.get_text(strip=True)
                        # Basic BTC address validation (starts with 1, 3, or bc1)
                        if (btc_text.startswith(('1', '3', 'bc1')) and 
                            len(btc_text) >= 26 and len(btc_text) <= 62):
                            btc_address = btc_text
                            break
                
                # Also search in full text for BTC addresses
                if btc_address == "N/A":
                    full_text = post.get_text()
                    # Bitcoin address pattern
                    btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|\bbc1[a-z0-9]{39,59}\b'
                    match = re.search(btc_pattern, full_text)
                    if match:
                        btc_address = match.group()
                
                # Skip items with no meaningful data
                if title == "Unknown" and author == "Unknown" and price == "N/A":
                    logger.debug(f"Skipping item {i} - no meaningful data found")
                    continue
                
                # Create item data according to instructions
                item_data = {
                    "title": title,
                    "author": author,
                    "price": price,
                    "btc_address": btc_address,
                    "scraped_at": datetime.now().isoformat(),
                    "timestamp": time.time(),
                    "source_url": TARGET_URL,
                    "item_index": i
                }
                
                items.append(item_data)
                logger.info(f"Extracted item {i+1}: '{title[:30]}...' by '{author}' - {price}")
                
            except Exception as e:
                logger.error(f"Error extracting data from listing {i}: {e}")
                continue
        
        logger.info(f"Successfully extracted {len(items)} items")
        return items
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error scraping target: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error scraping target: {e}")
        return []

def send_to_n8n(data):
    """Send scraped data to n8n webhook with proper error handling"""
    try:
        logger.info(f"Sending {len(data)} items to n8n webhook")
        
        # Prepare the payload
        payload = {
            "scraped_data": data,
            "metadata": {
                "total_items": len(data),
                "scrape_timestamp": datetime.now().isoformat(),
                "source_url": TARGET_URL,
                "scraper_version": "1.0"
            }
        }
        
        # Send to webhook
        response = requests.post(
            WEBHOOK_URL, 
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        response.raise_for_status()
        
        logger.info(f"Successfully sent data to n8n webhook - Status: {response.status_code}")
        logger.debug(f"Webhook response: {response.text[:500]}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error sending to webhook: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to webhook: {e}")
        return False

def send_test_data():
    """Send test data to webhook for debugging"""
    test_data = [
        {
            "title": "Test Item 1",
            "author": "Test Vendor",
            "price": "$100",
            "btc_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "scraped_at": datetime.now().isoformat(),
            "timestamp": time.time(),
            "source_url": "test",
            "item_index": 0
        },
        {
            "title": "Test Item 2",
            "author": "Test Vendor 2",
            "price": "$200",
            "btc_address": "N/A",
            "scraped_at": datetime.now().isoformat(),
            "timestamp": time.time(),
            "source_url": "test",
            "item_index": 1
        }
    ]
    
    logger.info("Sending test data to webhook...")
    return send_to_n8n(test_data)

def main():
    """Main execution function"""
    logger.info("Starting marketplace scraper...")
    
    # Test connection first
    if not test_connection():
        logger.error("Connection test failed. Please check your internet connection.")
        return
    
    # Extract market data
    results = extract_market_data()
    
    if results:
        logger.info(f"Successfully scraped {len(results)} items")
        
        # Send to n8n webhook
        if send_to_n8n(results):
            logger.info("Data successfully sent to n8n webhook")
        else:
            logger.error("Failed to send data to n8n webhook")
    else:
        logger.warning("No data scraped - sending test data instead")
        send_test_data()

if __name__ == "__main__":
    main()
