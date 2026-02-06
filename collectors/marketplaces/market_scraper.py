import sys
import os
import json
import logging
import time
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tor_manager import TorManager
import config

# Configure Logging
logger = logging.getLogger("MarketScraper")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class MarketScraper:
    def __init__(self, target_url):
        self.target_url = target_url
        self.tm = TorManager(
            config.TOR_CONTROL_PORT,
            config.TOR_SOCKS_HOST,
            config.TOR_SOCKS_PORT,
            config.TOR_PASSWORD
        )
        # Unique purpose ensures this Scraper gets its OWN Tor Circuit
        # distinct from the Crawler
        self.session = self.tm.session(purpose=f"market_scrape_{target_url[-10:]}")

    def run(self):
        try:
            self.tm.ensure_alive()
            logger.info(f"🛡️  Tor Circuit Established. Scraping: {self.target_url}")
            
            html = self._fetch_page(self.target_url)
            if html:
                items = self._extract_data(html)
                self._save_results(items)
            
        except Exception as e:
            logger.critical(f"🔥 Scrape failed: {e}")

    def _fetch_page(self, url):
        """Fetches page with retry logic."""
        attempts = 0
        max_retries = 3
        
        while attempts < max_retries:
            try:
                resp = self.session.get(url, timeout=30)
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code in [429, 503]:
                    logger.warning("⚠️  Rate limited. Sleeping...")
                    time.sleep(5)
                else:
                    logger.error(f"❌ HTTP {resp.status_code}")
                    return None
            except Exception as e:
                logger.error(f"⚠️  Network error: {str(e)}")
            
            attempts += 1
            time.sleep(2 * attempts) # Exponential backoff
            
        return None

    def _extract_data(self, html):
        """
        Generic extraction logic. 
        NOTE: In a real deployment, this needs specific selectors per marketplace.
        """
        soup = BeautifulSoup(html, 'html.parser')
        extracted_items = []
        
        # Generic strategy: Look for product-like containers
        # This scans for common class names used in dark web markets
        potential_products = soup.find_all(lambda tag: tag.name == 'div' and 
                                         any(c in (tag.get('class') or []) for c in ['product', 'item', 'listing', 'card']))
        
        logger.info(f"🔎 Found {len(potential_products)} potential product blocks.")

        for item in potential_products:
            # Extract basic text to feed into NER/NLP later
            text_content = item.get_text(separator=" ", strip=True)
            
            # Simple heuristic extraction
            title = item.find(['h3', 'h4', 'strong'])
            price = item.find(string=lambda s: '$' in s if s else False)
            
            extracted_items.append({
                "raw_text": text_content,
                "title": title.get_text().strip() if title else "Unknown",
                "price": price.strip() if price else "Unknown",
                "selector_match": item.get('class')
            })
            
        return extracted_items

    def _save_results(self, items):
        output = {
            "meta": {
                "feature": "market_scraper",
                "target": self.target_url,
                "timestamp": time.time(),
                "count": len(items)
            },
            "data": items
        }
        
        os.makedirs(os.path.join(config.OUTPUT_DIR, "raw"), exist_ok=True)
        filename = f"scrape_{int(time.time())}.json"
        path = os.path.join(config.OUTPUT_DIR, "raw", filename)
        
        with open(path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"💾 Scraped data saved to {path}")

if __name__ == "__main__":
    # Example Target (DuckDuckGo Onion as a safe test)
    # Replace with a real market URL in production
    TARGET = "https://duckduckgogg42ts72.onion/" 
    
    scraper = MarketScraper(TARGET)
    scraper.run()
