import os
import sys
import json
import glob
import time
import logging
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import settings as config
except ImportError:
    import config

from core.tor.tor_manager import TorManager

class BaseEnricher:
    """
    Base class to handle reading normalized data and saving enriched results.
    """
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        
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
            # Unique session isolation token based on the enricher's name
            self.session = self.tm.session(purpose=self.name.lower())
            self.logger.info(f"🛡️  Tor Session established for {self.name}")
        except Exception as e:
            self.logger.warning(f"⚠️ Tor connection failed for {self.name}: {e}")
            if getattr(config, "ALLOW_CLEARNET_FALLBACK", False):
                self.logger.info("Fallback: using direct clearnet connection.")
                self.session = requests.Session()
                self.session.headers.update({"User-Agent": "DarkWeb-OSINT-Pipeline/2.0"})
            else:
                self.logger.critical("🛑 Tor is required but unreachable. Aborting.")
                raise RuntimeError(f"Tor unreachable for {self.name}")

    def get_normalized_files(self):
        """Finds most recent normalized files that haven't been enriched by this stage."""
        from core.state_tracker import StateTracker
        tracker = StateTracker(config.STATE_DB_PATH)
        all_files = glob.glob(os.path.join(config.BASE_DIR, "data", "normalized", "*.json"))
        return [f for f in all_files if not tracker.is_processed(self.name, f)]

    def load_data(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def save_enriched(self, data, source_file):
        if not data:
            return
            
        timestamp = int(time.time())
        filename = f"enriched_{self.name.lower()}_{timestamp}_{os.path.basename(source_file)}"
        out_path = os.path.join(config.BASE_DIR, "data", "enriched", filename)
        
        output = {
            "meta": {
                "enricher": self.name,
                "source": os.path.basename(source_file),
                "timestamp": timestamp,
                "count": len(data)
            },
            "data": data
        }

        with open(out_path, 'w') as f:
            json.dump(output, f, indent=4)
        
        self.logger.info(f"✅ Saved enriched data to {filename}")

        # Mark source file as enriched in SQLite DB
        from core.state_tracker import StateTracker
        StateTracker(config.STATE_DB_PATH).mark_processed(self.name, source_file)

