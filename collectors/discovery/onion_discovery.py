import sys
import os
import json
import logging
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from pathlib import Path

# Fix Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from core.tor.tor_manager import TorManager
import config.settings as config

logger = logging.getLogger("OnionCrawler")

class OnionCrawler:
    def __init__(self, start_urls, max_depth=2):
        self.start_urls = start_urls
        self.max_depth = max_depth
        self.visited = set()
        self.discovered_domains = set()
        
        self.tm = TorManager(
            control_port=config.TOR_CONTROL_PORT,
            socks_proxy_host=config.TOR_SOCKS_HOST,
            socks_proxy_port=config.TOR_SOCKS_PORT,
            control_password=config.TOR_PASSWORD
        )
        self.session = self.tm.session(purpose="onion_crawler")
        self.onion_pattern = re.compile(r'[a-z2-7]{56}\.onion')

    def start(self):
        try:
            try:
                self.tm.ensure_alive()
                logger.info(f"🛡️  Tor Connection Verified.")
            except Exception as e:
                if getattr(config, "ALLOW_CLEARNET_FALLBACK", False):
                    logger.warning("⚠️ Tor connection failed. Fallback: using direct clearnet connection.")
                    self.session = requests.Session()
                    self.session.headers.update({"User-Agent": "DarkWeb-OSINT-Pipeline/2.0"})
                else:
                    raise e
            
            for url in self.start_urls:
                self._crawl(url, depth=0)
                
            self._save_results()
            
        except Exception as e:
            if getattr(config, "ALLOW_CLEARNET_FALLBACK", False):
                logger.warning(f"⚠️ Crawl failed but clearnet fallback is enabled: {e}")
            else:
                logger.critical(f"🔥 Critical Crawl Failure: {e}")
                raise

    def _crawl(self, url, depth):
        if depth > self.max_depth: return
        if url in self.visited: return
        
        self.visited.add(url)
        logger.info(f"🕷️  Crawling [D{depth}]: {url}")

        try:
            response = self.session.get(url, timeout=20)
            if response.status_code == 200:
                self._parse_html(url, response.text, depth)
            else:
                logger.warning(f"⚠️  Status {response.status_code} for {url}")
        except Exception as e:
            logger.error(f"❌ Failed to fetch {url}: {e}")

    def _parse_html(self, base_url, html, depth):
        soup = BeautifulSoup(html, 'html.parser')
        
        text_matches = self.onion_pattern.findall(html)
        for match in text_matches:
            self.discovered_domains.add(match)

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            
            # BeautifulSoup safety checks
            if isinstance(href, list):
                href = href[0]  # Take first item if it's a list
            
            if isinstance(href, str):
                # Now it is safe to join
                full_url = urljoin(str(base_url), href)
                
                if '.onion' in full_url:
                    self.discovered_domains.add(full_url)
                    time.sleep(1)
                    self._crawl(full_url, depth + 1)

    def _save_results(self):
        output_data = {
            "meta": {
                "feature": "onion_crawler",
                "timestamp": time.time(),
                "total_found": len(self.discovered_domains)
            },
            "data": list(self.discovered_domains)
        }
        
        # Use config.DATA_DIR correctly
        raw_dir = os.path.join(config.DATA_DIR, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        file_path = os.path.join(raw_dir, "onion_discovery.json")
        
        with open(file_path, 'w') as f:
            json.dump(output_data, f, indent=4)
        
        logger.info(f"💾 Results saved to {file_path}")

if __name__ == "__main__":
    crawler = OnionCrawler(start_urls=config.ONION_SEEDS, max_depth=1)
    crawler.start()
