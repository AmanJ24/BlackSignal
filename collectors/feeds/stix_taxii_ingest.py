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
logging.basicConfig(level=logging.INFO)

class STIXIngest:
    """
    Fetches public threat feeds (URLHaus, MalwareBazaar) for baseline intelligence.
    """
    FEEDS = {
        "urlhaus": "https://urlhaus-api.abuse.ch/v1/urls/recent/",
        # Add other free feeds here
    }

    def run(self):
        for name, url in self.FEEDS.items():
            try:
                logger.info(f"📥 Fetching feed: {name}")
                resp = requests.get(url, timeout=30)
                
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
