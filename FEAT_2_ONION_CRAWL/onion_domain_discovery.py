#!/usr/bin/env python3
"""
🌐 Automated .onion Domain Discovery via Recursive Crawling (Local Version)

Production-ready onion domain crawler that:
- Uses Tor Control Port for validation and SOCKS proxy for crawling
- Recursively discovers .onion domains from seed URLs
- Saves a detailed JSON report to a local 'output' folder.
- Handles errors gracefully and provides comprehensive logging
"""

import sys
import os
import requests
import re
import time
import json
import logging
import subprocess
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Set, List, Dict, Optional
import socket
from stem.control import Controller
from datetime import datetime  

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import get_tor_password, TOR_CONTROL_PORT, TOR_SOCKS_PROXY
except ImportError:
    # Fallback if config.py is not found
    def get_tor_password():
        return "your_tor_password"
    TOR_CONTROL_PORT = 9051
    TOR_SOCKS_PROXY = "127.0.0.1:9050"

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'onion_discovery.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OnionDomainDiscovery:
    """Standalone onion domain discovery crawler."""
    
    def __init__(self, 
                 max_depth: int = 2,
                 request_timeout: int = 30,
                 delay_between_requests: float = 1.0):
        """Initialize the crawler."""
        self.control_port = TOR_CONTROL_PORT
        self.socks_proxy = TOR_SOCKS_PROXY
        self.tor_password = get_tor_password()
        
        self.max_depth = max_depth
        self.request_timeout = request_timeout
        self.delay_between_requests = delay_between_requests
        
        self.visited_urls: Set[str] = set()
        self.discovered_domains: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.successful_urls: Set[str] = set()
        
        self.onion_pattern = re.compile(r'https?://[a-z2-7]{56}\.onion(?:[:/][^\s]*)?', re.IGNORECASE) 
        
        self._test_tor_connection()
        
    def _test_tor_connection(self) -> bool:
        """Test if the Tor control port is accessible."""
        try:
            logger.info(f"Connecting to Tor controller on port {self.control_port}...")
            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate(password=self.tor_password)
                logger.info("✅ Tor controller connection successful!")
                return True
        except Exception as e:
            logger.error(f"❌ Tor controller connection failed: {e}")
            raise ConnectionError(f"Tor controller connection required but failed: {e}")
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from a full URL."""
        try:
            return urlparse(url).netloc
        except Exception:
            return url
    
    def _is_valid_onion_url(self, url: str) -> bool:
        """Check if a URL is a valid .onion URL."""
        return bool(self.onion_pattern.match(url))
    
    def _crawl_url_with_curl(self, url: str) -> Optional[str]:
        """Fetch URL content using curl through the Tor SOCKS proxy."""
        try:
            cmd = [
                'curl', '--socks5-hostname', self.socks_proxy, '--silent',
                '--connect-timeout', str(self.request_timeout),
                '--max-time', str(self.request_timeout + 10),
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/119.0',
                '--location', url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.request_timeout + 20, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.warning(f"Curl failed for {url}: {result.stderr.strip()}")
                return None
        except subprocess.TimeoutExpired:
            logger.warning(f"Curl timeout for {url}")
            return None
        except Exception as e:
            logger.error(f"Curl error for {url}: {e}")
            return None
    
    def _crawl_url(self, url: str, depth: int):
        """Recursively crawl a single URL and extract onion links."""
        if depth <= 0 or url in self.visited_urls or url in self.failed_urls:
            return
        
        self.visited_urls.add(url)
        logger.info(f"🌐 Crawling (depth {self.max_depth - depth + 1}): {url}")
        
        html_content = self._crawl_url_with_curl(url)
        if not html_content:
            self.failed_urls.add(url)
            return

        self.successful_urls.add(url)
        soup = BeautifulSoup(html_content, 'html.parser')
        found_links = set()

        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if '.onion' in href:
                full_url = urljoin(url, href)
                if self._is_valid_onion_url(full_url):
                    found_links.add(full_url)
                    self.discovered_domains.add(self._extract_domain_from_url(full_url))

        for match in self.onion_pattern.finditer(soup.get_text()):
            url_match = match.group(0)
            if self._is_valid_onion_url(url_match):
                found_links.add(url_match)
                self.discovered_domains.add(self._extract_domain_from_url(url_match))
        
        logger.info(f"✅ Successfully crawled {url} - Found {len(found_links)} new onion links.")
        
        for link in found_links:
            time.sleep(self.delay_between_requests)
            self._crawl_url(link, depth - 1)
    
    def discover_domains(self, seed_urls: List[str]) -> Dict:
        """Main method to run the discovery process and generate a report."""
        logger.info(f"🌱 Starting onion domain discovery with {len(seed_urls)} seed URLs.")
        start_time = time.time()
        
        for url in seed_urls:
            if self._is_valid_onion_url(url):
                self.discovered_domains.add(self._extract_domain_from_url(url))
        
        for i, seed_url in enumerate(seed_urls, 1):
            if not self._is_valid_onion_url(seed_url):
                logger.warning(f"⚠️ Invalid seed URL, skipping: {seed_url}")
                continue
            logger.info(f"🌱 Processing seed {i}/{len(seed_urls)}: {seed_url}")
            self._crawl_url(seed_url, self.max_depth)
        
        duration = time.time() - start_time
        logger.info(f"🎉 Discovery completed in {duration:.2f} seconds.")
        
        report = self.generate_report(duration)
        return report

    def generate_report(self, duration: float) -> Dict:
        """Generates a structured JSON report of the crawl results."""
        service_map = {
            "facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion": "Facebook",
            "duckduckgogg42ts72.onion": "DuckDuckGo"
        }
        
        discovered_domains_list = []
        for i, domain in enumerate(sorted(list(self.discovered_domains)), 1):
            length = len(domain.replace('.onion', ''))
            version = "v3 (Modern)" if length == 56 else "v2 (Legacy)" if length == 16 else "Unknown"
            
            domain_info = {
                "index": i,
                "domain": domain,
                "service_name": service_map.get(domain, "Unknown Service"),
                "onion_version": version
            }
            discovered_domains_list.append(domain_info)

        return {
            "feature_name": "Onion Domain Discovery",
            "execution_timestamp": datetime.now().isoformat(),
            "metadata": {
                "summary": {
                    "total_domains_found": len(self.discovered_domains),
                    "duration_seconds": round(duration, 2),
                },
                "technical_details": {
                    "urls_crawled": len(self.visited_urls),
                    "successful_crawls": len(self.successful_urls),
                    "failed_crawls": len(self.failed_urls),
                    "max_depth": self.max_depth,
                }
            },
            "discovered_domains": discovered_domains_list
        }

def save_results(data: dict):
    """Saves the report to a JSON file in the 'output' directory."""
    if not data or not data["metadata"]["summary"]["total_domains_found"] > 0:
        logger.warning("No domains discovered, nothing to save.")
        return
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_2_onion_domains.json')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

if __name__ == "__main__":
    SEED_URLS = [
        "http://juhanurmihxlp77nkq76byazjpd1hxanp6d6f8dir5vdpvvf7dgd.onion",  # Ahmia Search Engine
        "http://tor66sewebgix6kfqc72knfxmb5cr25wn4xt4vj3u2r636s4k2xdrd2qd.onion", # Tor66 Search Engine
    ]
    
    try:
        crawler = OnionDomainDiscovery(max_depth=2)
        final_report = crawler.discover_domains(SEED_URLS)
        
        if final_report:
            save_results(final_report)
            print("\n" + "="*60)
            print("📊 DISCOVERY SUMMARY:")
            print(json.dumps(final_report["metadata"]["summary"], indent=4))
            print("="*60)
        
        logger.info("✅ Onion domain discovery finished successfully.")
    except ConnectionError as e:
        logger.error(f"Could not start crawler: {e}")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
