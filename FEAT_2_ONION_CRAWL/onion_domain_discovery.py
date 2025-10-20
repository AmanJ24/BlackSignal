#!/usr/bin/env python3
"""
🌐 Automated .onion Domain Discovery via Recursive Crawling

Production-ready onion domain crawler that:
- Uses Tor Control Port for validation and SOCKS proxy for crawling
- Recursively discovers .onion domains from seed URLs
- Sends results to n8n webhook for automation pipeline
- Handles errors gracefully and provides comprehensive logging
"""

import sys
import os
import requests

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_n8n_webhook_url, get_tor_password, TOR_CONTROL_PORT, TOR_SOCKS_PROXY
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/onion_discovery_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OnionDomainDiscoveryFinal:
    """
    Final working version of onion domain discovery crawler
    """
    
    def __init__(self, 
                 control_port: int = 9051,
                 socks_proxy: str = "127.0.0.1:9050",
                 webhook_url: Optional[str] = None,
                 max_depth: int = 2,
                 request_timeout: int = 30,
                 delay_between_requests: float = 1.0,
                 tor_password: str = "TorRelay123"):
        """
        Initialize the onion domain discovery crawler
        """
        self.control_port = control_port
        self.socks_proxy = socks_proxy
        self.webhook_url = webhook_url
        self.max_depth = max_depth
        self.request_timeout = request_timeout
        self.delay_between_requests = delay_between_requests
        self.tor_password = tor_password
        
        # State tracking
        self.visited_urls: Set[str] = set()
        self.discovered_domains: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.successful_urls: Set[str] = set()
        
        # Setup session with Tor SOCKS proxy
        self.session = self._setup_session()
        
        # Test Tor connection
        self._test_tor_connection()
        
        # Onion URL regex pattern
        self.onion_pattern = re.compile(
            r'https?://[a-z2-7]{16,56}\.onion(?:[:/][^\s]*)?', 
            re.IGNORECASE
        )
        
    def _setup_session(self) -> requests.Session:
        """Setup requests session with Tor SOCKS proxy"""
        session = requests.Session()
        
        # Configure SOCKS5 proxy for Tor
        session.proxies = {
            'http': f'socks5h://{self.socks_proxy}',
            'https': f'socks5h://{self.socks_proxy}'
        }
        
        # Set realistic headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'DNT': '1'
        })
        
        return session
        
    def _test_tor_connection(self) -> bool:
        """Test if Tor control port is accessible"""
        try:
            print("Connecting to Tor controller...")
            with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
                print("Authenticating...")
                controller.authenticate(password=get_tor_password())
                print("✅ Tor controller connection successful!")
                logger.info("✅ Tor controller is accessible")
                return True
                
        except Exception as e:
            print(f"Error connecting to Tor controller: {str(e)}")
            logger.error(f"❌ Tor controller connection failed: {e}")
            raise Exception(f"Tor controller connection required but failed: {e}")
    
    def _get_known_onion_services(self) -> List[str]:
        """Get list of known legitimate onion services as starting points"""
        return [
            "duckduckgogg42ts72.onion",  # DuckDuckGo
            "facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion",  # Facebook
            "zqktlwiuavvvqqt4ybvgvi7tyo4hjl5xgfuvpdf6otjiycgwqbym2qad.onion",  # ProPublica
        ]
    
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from full URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return url
    
    def _is_valid_onion_url(self, url: str) -> bool:
        """Check if URL is a valid .onion URL"""
        return bool(self.onion_pattern.match(url))
    
    def _crawl_url_with_curl(self, url: str) -> str:
        """Fetch URL content using curl through Tor SOCKS proxy"""
        try:
            cmd = [
                'curl',
                '--socks5-hostname', '127.0.0.1:9050',
                '--silent',
                '--connect-timeout', '20',
                '--max-time', '40',
                '--user-agent', 'Mozilla/5.0 (compatible; OnionCrawler/1.0)',
                '--location',  # Follow redirects
                url
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=50
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.warning(f"Curl failed for {url}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Curl timeout for {url}")
            return None
        except Exception as e:
            logger.error(f"Curl error for {url}: {e}")
            return None
    
    def _crawl_url(self, url: str, depth: int) -> bool:
        """Crawl a single URL and extract onion links using curl"""
        if depth <= 0 or url in self.visited_urls or url in self.failed_urls:
            return False
        
        self.visited_urls.add(url)
        logger.info(f"🌐 Crawling (depth {self.max_depth - depth + 1}): {url}")
        
        # Use curl for reliable onion connections
        try:
            html_content = self._crawl_url_with_curl(url)
            
            if not html_content:
                self.failed_urls.add(url)
                return False
            
            # Extract onion links from HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            onion_links = set()
            
            # Find all anchor tags with href attributes
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').strip()
                if '.onion' in href:
                    try:
                        # Normalize URL
                        if href.startswith('//'):
                            href = 'http:' + href
                        elif href.startswith('/'):
                            base_parsed = urlparse(url)
                            href = f"{base_parsed.scheme}://{base_parsed.netloc}{href}"
                        elif not href.startswith(('http://', 'https://')):
                            href = urljoin(url, href)
                        
                        if self._is_valid_onion_url(href):
                            onion_links.add(href)
                            domain = self._extract_domain_from_url(href)
                            if domain.endswith('.onion'):
                                self.discovered_domains.add(domain)
                                
                    except Exception as e:
                        logger.debug(f"Error processing link {href}: {e}")
                        continue
            
            # Also search for onion URLs in page text
            page_text = soup.get_text()
            for match in self.onion_pattern.finditer(page_text):
                url_match = match.group(0)
                if self._is_valid_onion_url(url_match):
                    onion_links.add(url_match)
                    domain = self._extract_domain_from_url(url_match)
                    if domain.endswith('.onion'):
                        self.discovered_domains.add(domain)
            
            logger.info(f"✅ Successfully crawled {url} - Found {len(onion_links)} onion links")
            self.successful_urls.add(url)
            
            # Recursively crawl found links if depth allows
            if depth > 1:
                for link in onion_links:
                    if link not in self.visited_urls and link not in self.failed_urls:
                        time.sleep(self.delay_between_requests)
                        self._crawl_url(link, depth - 1)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Unexpected error crawling {url}: {e}")
            self.failed_urls.add(url)
            return False
    
    def discover_domains(self, seed_urls: List[str]) -> List[str]:
        """
        Main method to discover .onion domains from seed URLs
        """
        logger.info(f"🌱 Starting onion domain discovery with {len(seed_urls)} seed URLs")
        logger.info("🌐 Running in REAL MODE (Tor controller connected)")
        
        # Add seed domains to discovered set
        for url in seed_urls:
            domain = self._extract_domain_from_url(url)
            if domain.endswith('.onion'):
                self.discovered_domains.add(domain)
        
        # Start crawling from seed URLs
        successful_seeds = 0
        for i, seed_url in enumerate(seed_urls, 1):
            if not self._is_valid_onion_url(seed_url):
                logger.warning(f"⚠️ Invalid seed URL: {seed_url}")
                continue
                
            logger.info(f"🌱 Processing seed {i}/{len(seed_urls)}: {seed_url}")
            
            if self._crawl_url(seed_url, self.max_depth):
                successful_seeds += 1
            
            # Delay between seed URLs
            if i < len(seed_urls):
                time.sleep(self.delay_between_requests)
        
        
        # Convert set to sorted list
        discovered_list = sorted(list(self.discovered_domains))
        
        logger.info(f"🎉 Discovery completed!")
        logger.info(f"📊 Seeds successful: {successful_seeds}/{len(seed_urls)}")
        logger.info(f"📄 URLs visited: {len(self.visited_urls)}")
        logger.info(f"✅ URLs successful: {len(self.successful_urls)}")
        logger.info(f"❌ URLs failed: {len(self.failed_urls)}")
        logger.info(f"🔗 Domains discovered: {len(discovered_list)}")
        
        return discovered_list
    
    def send_to_webhook(self, domains: List[str]) -> bool:
        """Send discovered domains to n8n webhook with beautiful formatting"""
        if not self.webhook_url:
            logger.warning("⚠️ No webhook URL configured")
            return False
        
        if not domains:
            logger.warning("⚠️ No domains to send")
            return False
        
        # Get current timestamp for consistent formatting
        current_time = time.time()
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(current_time))
        
        # Known service mappings for better context
        service_map = {
            "facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion": "Facebook",
            "3g2upl4pq6kufc4m.onion": "DuckDuckGo (Legacy)",
            "zqktlwiuavvvqqt4ybvgvi7tyo4hjl5xgfuvpdf6otjiycgwqbym2qad.onion": "ProPublica",
            "juhanurmihxlp77nkq76byazjpd1hxanp6d6f8dir5vdpvvf7dgd.onion": "Ahmia Search",
            "duckduckgogg42ts72.onion": "DuckDuckGo"
        }
        
        # Create beautiful structured payload
        payload = {
            "🌐 onion_discovery_report": {
                "metadata": {
                    "📊 summary": {
                        "total_domains_found": len(domains),
                        "discovery_timestamp": formatted_time,
                        "unix_timestamp": current_time,
                        "discovery_mode": "🔴 LIVE (Real Tor Network)",
                        "crawler_version": "OnionDiscovery v2.0",
                        "source": "🕷️ Automated Tor Crawler"
                    },
                    "🔧 technical_details": {
                        "urls_crawled": len(self.visited_urls),
                        "successful_crawls": len(self.successful_urls),
                        "failed_crawls": len(self.failed_urls),
                        "max_depth": self.max_depth,
                        "tor_proxy": self.socks_proxy,
                        "request_timeout": f"{self.request_timeout}s"
                    }
                },
                "🧅 discovered_domains": []
            }
        }
        
        # Add each domain with rich metadata
        for i, domain in enumerate(domains, 1):
            service_name = service_map.get(domain, "Unknown Service")
            domain_length = len(domain.replace('.onion', ''))
            
            # Determine onion version based on domain length
            if domain_length == 16:
                onion_version = "v2 (Legacy)"
                security_level = "⚠️ Medium"
            elif domain_length == 56:
                onion_version = "v3 (Modern)"
                security_level = "🔒 High"
            else:
                onion_version = "Unknown"
                security_level = "❓ Unknown"
            
            domain_info = {
                "🏷️ index": i,
                "🌐 domain": domain,
                "🏢 service_name": service_name,
                "🔗 full_url": f"http://{domain}",
                "📊 details": {
                    "onion_version": onion_version,
                    "security_level": security_level,
                    "domain_length": domain_length,
                    "is_known_service": domain in service_map
                },
                "⏰ discovered_at": formatted_time,
                "🔍 discovery_method": "recursive_crawling"
            }
            
            payload["🌐 onion_discovery_report"]["🧅 discovered_domains"].append(domain_info)
        
        try:
            print(f"Sending to webhook: {self.webhook_url}")
            logger.info(f"📤 Sending {len(domains)} domains to webhook...")
            
            # Use same approach as working tor_api.py
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.webhook_url, 
                json=payload, 
                headers=headers, 
                timeout=30
            )
            
            print(f"Webhook response - Status: {response.status_code}, Text: {response.text}")
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully sent data to webhook (HTTP {response.status_code})")
                return True
            else:
                logger.error(f"❌ Webhook returned status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to send data to webhook: {e}")
            return False
    
    def run_discovery(self, seed_urls: List[str]) -> Dict:
        """Complete discovery pipeline: crawl + send to webhook"""
        start_time = time.time()
        
        try:
            # Discover domains
            discovered_domains = self.discover_domains(seed_urls)
            
            # Send to webhook if configured
            webhook_success = False
            if self.webhook_url and discovered_domains:
                webhook_success = self.send_to_webhook(discovered_domains)
            
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                "status": "success",
                "discovered_domains": discovered_domains,
                "domain_count": len(discovered_domains),
                "urls_visited": len(self.visited_urls),
                "urls_successful": len(self.successful_urls),
                "urls_failed": len(self.failed_urls),
                "webhook_sent": webhook_success,
                "duration_seconds": round(duration, 2),
                "demo_mode": False,
                "timestamp": time.time()
            }
            
            logger.info(f"🏁 Discovery pipeline completed in {duration:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"💥 Discovery pipeline failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "discovered_domains": [],
                "domain_count": 0,
                "demo_mode": False,
                "timestamp": time.time()
            }


def main():
    """Main execution function"""
    
    SEED_URLS = [
        "http://darkfailllnkf4vf.onion",
        "http://hss3uro2hsxfogfq.onion",
        "http://dppmfxaacucguzpc.onion",
        "http://torlinkbgs6aabns.onion",
        "http://ahmiafiaduknq7cz.onion"
    ]
    
    # N8N Webhook URL - using config module
    WEBHOOK_URL = get_n8n_webhook_url('onion-crawl')
    
    # Initialize crawler using same patterns as working tor_api.py
    crawler = OnionDomainDiscoveryFinal(
        control_port=9051,  # Same as tor_api.py
        socks_proxy="127.0.0.1:9050",
        webhook_url=WEBHOOK_URL,
        max_depth=3,
        request_timeout=30,
        delay_between_requests=1.0,
        tor_password="TorRelay123"  # Same as tor_api.py
    )
    
    print("🌐 Automated .onion Domain Discovery (FINAL VERSION)")
    print("=" * 60)
    print(f"🌱 Seed URLs: {len(SEED_URLS)}")
    print(f"🔄 Max depth: {crawler.max_depth}")
    print(f"⏱️  Timeout: {crawler.request_timeout}s")
    print(f"📡 Webhook: {'✅ Active' if WEBHOOK_URL else 'Not configured'}")
    print(f"🔌 Tor Control: 127.0.0.1:{crawler.control_port}")
    print(f"🧅 SOCKS Proxy: {crawler.socks_proxy}")
    print(f"🎭 Demo Mode: No")
    print("=" * 60)
    
    # Run discovery pipeline
    result = crawler.run_discovery(SEED_URLS)
    
    # Print results (same format as working tor_api.py)
    print("\n📊 DISCOVERY RESULTS")
    print("=" * 60)
    
    if result["status"] == "success":
        print(f"✅ Discovery completed successfully")
        print(f"🌐 Mode: REAL (Through Tor network)")
        print(f"🔗 Domains discovered: {result['domain_count']}")
        print(f"📄 URLs visited: {result['urls_visited']}")
        print(f"✅ URLs successful: {result['urls_successful']}")
        print(f"❌ URLs failed: {result['urls_failed']}")
        print(f"📤 Webhook sent: {'✅ Yes' if result['webhook_sent'] else '❌ No'}")
        print(f"⏱️  Duration: {result['duration_seconds']} seconds")
        
        if result["discovered_domains"]:
            print(f"\n📋 Discovered .onion domains:")
            for i, domain in enumerate(result["discovered_domains"], 1):
                print(f"{i:3d}. {domain}")
        else:
            print("\n😕 No onion domains were discovered")
            
                
    else:
        print(f"❌ Discovery failed: {result.get('error', 'Unknown error')}")
    
    print("\n🎆 Discovery pipeline completed!")


if __name__ == "__main__":
    main()
