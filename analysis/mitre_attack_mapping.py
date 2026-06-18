import os
import sys
import json
import logging
import glob
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import settings as config
except ImportError:
    import config

logger = logging.getLogger("MITREMapper")

class MITREMapper:
    # Simplified mapping for demonstration. Real implementation needs a larger DB.
    TTPS = {
        "T1587": ["develop", "exploit", "malware", "tool"], # Develop Capabilities
        "T1566": ["phishing", "email", "lure"],             # Phishing
        "T1486": ["encrypt", "ransom", "lock"]              # Data Encrypted for Impact
    }

    def run(self):
        # Reads RAW scraper data
        files = glob.glob(os.path.join(config.BASE_DIR, "data", "raw", "scrape_*.json"))
        
        from core.state_tracker import StateTracker
        tracker = StateTracker(config.STATE_DB_PATH)

        for file_path in files:
            if tracker.is_processed("mitre_mapping", file_path):
                continue

            with open(file_path, 'r') as f:
                content = json.load(f)
            
            analyzed_items = []
            for item in content.get("data", []):
                text = item.get("raw_text", "").lower()
                
                found_ttps = []
                for ttp_id, keywords in self.TTPS.items():
                    if any(k in text for k in keywords):
                        found_ttps.append(ttp_id)
                
                if found_ttps:
                    evidence = [{
                        "type": "mitre_technique_match",
                        "description": f"Mapped TTPs: {found_ttps}",
                        "confidence": 0.7,
                        "source_feature": "mitre_mapping"
                    }]
                    item.setdefault("evidence", {})["mitre"] = evidence
                    analyzed_items.append(item)

            if analyzed_items:
                self._save(analyzed_items, os.path.basename(file_path))

            # Mark processed in StateTracker
            tracker.mark_processed("mitre_mapping", file_path)

    def _save(self, data, source):
        path = os.path.join(config.BASE_DIR, "data", "intelligence", f"intel_mitre_{int(time.time())}_{source}")
        output = {
            "meta": {
                "feature": "mitre_mapping",
                "source": source,
                "timestamp": int(time.time())
            },
            "data": data
        }
        with open(path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"✅ Mapped TTPs for {len(data)} items -> {path}")

if __name__ == "__main__":
    MITREMapper().run()
