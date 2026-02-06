import sys
import os
import json
import logging
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

# Add parent directory to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tor_manager import TorManager
import config

# Configure Logging
logger = logging.getLogger("OnionCrawler")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class OnionCrawler:
    def __init__(self, start_urls, max_depth=2):
        self.start_urls = start_urls
        self.max_depth = max_depth
        self.visited = set()
        self.discovered_domains = set()
        
        # Initialize Tor Manager
        self.tm = TorManager(
            control_port=config.TOR_CONTROL_PORT,
            socks_proxy_host=config.TOR_SOCKS_HOST,
            socks_proxy_port=config.TOR_SOCKS_PORT,
            control_password=config.TOR_PASSWORD
        )
        
        # Get an ISOLATED session specifically for crawling
        # "onion_crawler" string creates a unique hash for the SOCKS username
        self.session = self.tm.session(purpose="onion_crawler")
        
        # Regex for V3 Onion Addresses
        self.onion_pattern = re.compile(r'[a-z2-7]{56}\.onion')

    def start(self):
        """Main execution method."""
        try:
            self.tm.ensure_alive()
            logger.info(f"🛡️  Tor Connection Verified. IP: {self.tm.get_current_ip(self.session)}")
            
            for url in self.start_urls:
                self._crawl(url, depth=0)
                
            self._save_results()
            
        except Exception as e:
            logger.critical(f"🔥 Critical Crawl Failure: {e}")

    def _crawl(self, url, depth):
        if depth > self.max_depth:
            return
        if url in self.visited:
            return
        
        self.visited.add(url)
        logger.info(f"🕷️  Crawling [D{depth}]: {url}")

        try:
            response = self.session.get(url, timeout=20)
            if response.status_code == 200:
                self._parse_html(url, response.text, depth)
            else:
                logger.warning(f"⚠️  Status {response.status_code} for {url}")
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch {url}: {str(e).split('Stack')[0]}")

    def _parse_html(self, base_url, html, depth):
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Regex Scan for text-based onions
        text_matches = self.onion_pattern.findall(html)
        for match in text_matches:
            self.discovered_domains.add(match)

        # 2. Link Extraction for recursion
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Handle relative URLs
            full_url = urljoin(base_url, href)
            
            # Check if it's an onion link
            if '.onion' in full_url:
                domain = urlparse(full_url).netloc
                self.discovered_domains.add(domain)
                
                # Recursive call
                # Only recurse if we haven't hit depth limit
                time.sleep(1) # Polite delay
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
        
        # Ensure output directory exists
        os.makedirs(os.path.join(config.OUTPUT_DIR, "raw"), exist_ok=True)
        file_path = os.path.join(config.OUTPUT_DIR, "raw", "onion_discovery.json")
        
        with open(file_path, 'w') as f:
            json.dump(output_data, f, indent=4)
        
        logger.info(f"💾 Results saved to {file_path}")

if __name__ == "__main__":
    # Seed URLs (Example: Ahmia, Hidden Wiki mirrors)
    # In production, these should come from a config file or database
    SEEDS = [
        "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/", # Ahmia
    ]
    
    crawler = OnionCrawler(start_urls=SEEDS, max_depth=1)
    crawler.start()
