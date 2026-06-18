import os
import sys
import json
import time
import logging
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from config import settings as config
except ImportError:
    import config

logger = logging.getLogger("STIXIngest")

from core.tor.tor_manager import TorManager

class STIXIngest:
    """
    Fetches public threat feeds (URLHaus, MalwareBazaar) for baseline intelligence.
    """
    FEEDS = {
        "urlhaus": "https://urlhaus-api.abuse.ch/v1/urls/recent/",
        # Add other free feeds here
    }

    def __init__(self):
        self.tm = TorManager(
            control_port=config.TOR_CONTROL_PORT,
            socks_proxy_host=config.TOR_SOCKS_HOST,
            socks_proxy_port=config.TOR_SOCKS_PORT,
            control_password=config.TOR_PASSWORD
        )
        self.session = None
        self._init_session()

    def _init_session(self):
        try:
            self.tm.ensure_alive()
            self.session = self.tm.session(purpose="stix_ingest")
            logger.info("🛡️  Tor Session established for STIX Ingest")
        except Exception as e:
            logger.warning(f"⚠️ Tor connection failed for STIX Ingest: {e}")
            if getattr(config, "ALLOW_CLEARNET_FALLBACK", False):
                logger.info("Fallback: using direct clearnet connection.")
                self.session = requests.Session()
                self.session.headers.update({"User-Agent": "DarkWeb-OSINT-Pipeline/2.0"})
            else:
                logger.critical("🛑 Tor is required but unreachable. Aborting STIX ingest.")
                raise RuntimeError("Tor unreachable for STIX Ingest")

    def run(self):
        for name, url in self.FEEDS.items():
            try:
                logger.info(f"📥 Fetching feed: {name}")
                resp = self.session.get(url, timeout=30)
                
                if resp.status_code == 200:
                    data = resp.json()
                    self._save(name, data)
                else:
                    logger.warning(f"⚠️ Feed {name} returned status {resp.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to fetch {name}: {e}")

    def _save(self, name, data):
        output = {
            "meta": {
                "feature": "stix_ingest",
                "feed": name,
                "timestamp": int(time.time())
            },
            "data": data # Raw feed data
        }
        
        filename = f"feed_{name}_{int(time.time())}.json"
        path = os.path.join(config.BASE_DIR, "data", "raw", filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"💾 Saved feed data to {path}")

if __name__ == "__main__":
    STIXIngest().run()
