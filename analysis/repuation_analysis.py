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

logger = logging.getLogger("ReputationAnalysis")
logging.basicConfig(level=logging.INFO)

class ReputationAnalysis:
    def run(self):
        # It reads from Intelligence files (output of other analysis scripts)
        # to find entities that have accumulated negative evidence.
        files = glob.glob(os.path.join(config.BASE_DIR, "data", "intelligence", "*.json"))
        
        entities = {}

        for file_path in files:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for item in data.get("data", []):
                # We assume items might have an 'id' or we generate one from title/handle
                # For simplicity, we skip items without clear ID for now
                if "title" not in item: continue
                
                entity_id = item["title"][:50] # Placeholder ID logic
                if entity_id not in entities:
                    entities[entity_id] = {"id": entity_id, "evidence_count": 0}
                
                # Count evidence from other modules
                if "evidence" in item:
                    entities[entity_id]["evidence_count"] += len(item["evidence"])

        # Create Reputation Reports for High-Evidence Entities
        reputation_reports = []
        for eid, stats in entities.items():
            if stats["evidence_count"] > 1:
                reputation_reports.append({
                    "id": eid,
                    "type": "vendor_reputation",
                    "evidence": {
                        "behavioral": [{
                            "type": "multi_source_corroboration",
                            "confidence": 0.8,
                            "source_feature": "reputation_analysis"
                        }]
                    }
                })

        if reputation_reports:
            self._save(reputation_reports)

    def _save(self, data):
        path = os.path.join(config.BASE_DIR, "data", "intelligence", f"intel_reputation_{int(time.time())}.json")
        with open(path, 'w') as f:
            json.dump({"data": data}, f, indent=4)
        logger.info(f"✅ Generated {len(data)} reputation reports -> {path}")

if __name__ == "__main__":
    ReputationAnalysis().run()
