import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from core.tor.tor_manager import TorManager
import config.settings as config

logger = logging.getLogger("RelayInventory")
logging.basicConfig(level=logging.INFO)

class RelayInventory:
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
            
            # Explicit check to satisfy type checker and runtime safety
            if self.tm._controller is None:
                raise RuntimeError("Tor Controller failed to initialize.")

            logger.info("📡 Fetching Tor Network Consensus...")
            
            # Now safe to call
            relays = None
            for attempt in range(12):
                try:
                    relays = self.tm._controller.get_network_statuses()
                    break
                except Exception as e:
                    if "unavailable" in str(e).lower():
                        logger.info(f"⏳ Waiting for Tor descriptors (attempt {attempt+1}/12)...")
                        time.sleep(5)
                    else:
                        raise e
            if relays is None:
                raise RuntimeError("Failed to fetch descriptors: Tor is not fully bootstrapped.")
            
            inventory = []
            for relay in relays:
                inventory.append({
                    "fingerprint": relay.fingerprint,
                    "nickname": relay.nickname,
                    "address": relay.address
                })
            
            logger.info(f"✅ Collected {len(inventory)} active relays.")
            self._save_results(inventory)

        except Exception as e:
            logger.critical(f"❌ Relay inventory failed: {e}")
            raise

    def _save_results(self, data):
        timestamp = datetime.utcnow().isoformat()
        output = {"meta": {"feature": "relay_inventory", "timestamp": timestamp}, "data": data}

        raw_dir = os.path.join(config.DATA_DIR, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        filepath = os.path.join(raw_dir, f"tor_relays_{int(time.time())}.json")
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=4)
        
        logger.info(f"💾 Saved relay inventory to: {filepath}")

if __name__ == "__main__":
    RelayInventory().run()
