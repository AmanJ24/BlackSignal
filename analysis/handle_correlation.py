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

logger = logging.getLogger("HandleCorrelation")

class HandleCorrelation:
    def __init__(self):
        # In a real app, this loads from a DB. For now, a simple JSON file or dict.
        self.known_actors_file = os.path.join(config.BASE_DIR, "analysis", "known_handles.json")
        self.known_actors = self._load_known_handles()

    def _load_known_handles(self):
        if os.path.exists(self.known_actors_file):
            with open(self.known_actors_file, 'r') as f:
                return json.load(f)
        return {} # Empty if no DB

    def run(self):
        # Process Normalized Entities (Output of NER)
        files = glob.glob(os.path.join(config.BASE_DIR, "data", "normalized", "normalized_entities_*.json"))
        
        from core.state_tracker import StateTracker
        tracker = StateTracker(config.STATE_DB_PATH)

        for file_path in files:
            if tracker.is_processed("handle_correlation", file_path):
                continue

            with open(file_path, 'r') as f:
                content = json.load(f)
            
            analyzed_handles = []
            for entity in content.get("data", []):
                if entity.get("subtype") == "PERSON":
                    handle = entity.get("id")
                    match = self.known_actors.get(handle)
                    
                    if match:
                        # Add Intelligence Evidence
                        entity.setdefault("evidence", {})["behavioral"] = [{
                            "type": "known_threat_actor",
                            "description": f"Matches known actor: {match.get('group', 'Unknown')}",
                            "confidence": 0.9,
                            "source_feature": "handle_correlation"
                        }]
                        analyzed_handles.append(entity)

            if analyzed_handles:
                self._save(analyzed_handles, os.path.basename(file_path))

            # Mark processed in StateTracker
            tracker.mark_processed("handle_correlation", file_path)

    def _save(self, data, source):
        output = {
            "meta": {
                "analysis": "handle_correlation",
                "source": source,
                "timestamp": int(time.time())
            },
            "data": data
        }
        path = os.path.join(config.BASE_DIR, "data", "intelligence", f"intel_handles_{int(time.time())}_{source}")
        with open(path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"✅ Correlated {len(data)} handles -> {path}")

if __name__ == "__main__":
    HandleCorrelation().run()
