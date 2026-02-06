import os
import sys
import json
import time
import logging
from datetime import datetime

# Path adjustments for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.tor.tor_manager import TorManager
# Assuming config is moved to config/settings.py based on your structure
# If it's still in root, change to 'import config'
try:
    from config import settings as config
except ImportError:
    import config

logger = logging.getLogger("RelayInventory")
logging.basicConfig(level=logging.INFO)

class RelayInventory:
    """
    Collects active Tor relay data (Entry, Middle, Exit nodes) directly from the Tor Consensus.
    """

    def __init__(self):
        self.tm = TorManager(
            control_port=config.TOR_CONTROL_PORT,
            socks_proxy_host=config.TOR_SOCKS_HOST,
            socks_proxy_port=config.TOR_SOCKS_PORT,
            control_password=config.TOR_PASSWORD
        )

    def run(self):
        try:
            self.tm.connect()
            logger.info("📡 Fetching Tor Network Consensus...")
            
            # Fetch all network statuses
            # This is a heavy operation, returns thousands of relays
            relays = self.tm._controller.get_network_statuses()
            
            inventory = []
            for relay in relays:
                inventory.append({
                    "fingerprint": relay.fingerprint,
                    "nickname": relay.nickname,
                    "address": relay.address,
                    "or_port": relay.or_port,
                    "flags": list(relay.flags),
                    "bandwidth": relay.bandwidth,
                    "version": str(relay.version) if relay.version else "unknown"
                })
            
            logger.info(f"✅ Collected {len(inventory)} active relays.")
            self._save_results(inventory)

        except Exception as e:
            logger.critical(f"❌ Relay inventory failed: {e}")

    def _save_results(self, data):
        timestamp = datetime.utcnow().isoformat()
        output = {
            "meta": {
                "feature": "relay_inventory",
                "timestamp": timestamp,
                "count": len(data)
            },
            "data": data
        }

        # Save to data/raw/
        filename = f"tor_relays_{int(time.time())}.json"
        filepath = os.path.join(config.BASE_DIR, "data", "raw", filename)
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=4)
        
        logger.info(f"💾 Saved relay inventory to: {filepath}")

if __name__ == "__main__":
    collector = RelayInventory()
    collector.run()
