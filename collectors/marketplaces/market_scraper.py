import sys
import os
import json
import logging
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Fix Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from core.tor.tor_manager import TorManager
import config.settings as config

logger = logging.getLogger("MarketScraper")

class MarketScraper:
    def __init__(self, target_url):
        self.target_url = target_url
        self.tm = TorManager(
            config.TOR_CONTROL_PORT,
            config.TOR_SOCKS_HOST,
            config.TOR_SOCKS_PORT,
            config.TOR_PASSWORD
        )
        self.session = self.tm.session(purpose=f"market_scrape_{target_url[-10:]}")

    def run(self):
        try:
            try:
                self.tm.ensure_alive()
                logger.info(f"🛡️  Tor Circuit Established. Scraping: {self.target_url}")
            except Exception as e:
                if getattr(config, "ALLOW_CLEARNET_FALLBACK", False):
                    logger.warning("⚠️ Tor connection failed. Fallback: using direct clearnet connection.")
                    self.session = requests.Session()
                    self.session.headers.update({"User-Agent": "DarkWeb-OSINT-Pipeline/2.0"})
                else:
                    raise e
            
            html = self._fetch_page(self.target_url)
            if html:
                items = self._extract_data(html)
                self._save_results(items)
            
        except Exception as e:
            if getattr(config, "ALLOW_CLEARNET_FALLBACK", False):
                logger.warning(f"⚠️ Scrape failed but clearnet fallback is enabled: {e}")
            else:
                logger.critical(f"🔥 Scrape failed: {e}")
                raise

    def _fetch_page(self, url):
        attempts = 0
        while attempts < 3:
            try:
                resp = self.session.get(url, timeout=30)
                if resp.status_code == 200: return resp.text
            except Exception as e:
                logger.error(f"⚠️  Network error: {e}")
            attempts += 1
            time.sleep(2 * attempts)
        return None

    def _extract_data(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        extracted_items = []
        
        potential_products = soup.find_all('div')
        for item in potential_products:
            text = item.get_text(separator=" ", strip=True)
            if len(text) > 20:
                extracted_items.append({"raw_text": text})
            
        return extracted_items

    def _save_results(self, items):
        output = {
            "meta": {"feature": "market_scraper", "timestamp": time.time(), "count": len(items)},
            "data": items
        }
        
        # Use config.DATA_DIR correctly
        raw_dir = os.path.join(config.DATA_DIR, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        filename = f"scrape_{int(time.time())}.json"
        path = os.path.join(raw_dir, filename)
        
        with open(path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"💾 Scraped data saved to {path}")

if __name__ == "__main__":
    for t in config.MARKET_TARGETS:
        MarketScraper(t).run()
