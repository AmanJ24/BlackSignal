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

logger = logging.getLogger("AffiliateAnalysis")
logging.basicConfig(level=logging.INFO)

class AffiliateAnalysis:
    RECRUITMENT_TERMS = ["partner", "affiliate", "percentage", "share", "profit", "recruit"]

    def run(self):
        files = glob.glob(os.path.join(config.BASE_DIR, "data", "raw", "scrape_*.json"))
        
        for file_path in files:
            with open(file_path, 'r') as f:
                content = json.load(f)
            
            analyzed_items = []
            for item in content.get("data", []):
                text = item.get("raw_text", "").lower()
                
                matches = [t for t in self.RECRUITMENT_TERMS if t in text]
                
                # If multiple recruitment terms appear, confidence increases
                if len(matches) >= 2:
                    evidence = [{
                        "type": "raas_recruitment_indicator",
                        "description": f"Recruitment terms found: {matches}",
                        "confidence": 0.6 + (0.1 * len(matches)), # Cap at 1.0 logic handled by scoring
                        "source_feature": "affiliate_analysis"
                    }]
                    item.setdefault("evidence", {})["affiliate"] = evidence
                    analyzed_items.append(item)

            if analyzed_items:
                self._save(analyzed_items, os.path.basename(file_path))

    def _save(self, data, source):
        path = os.path.join(config.BASE_DIR, "data", "intelligence", f"intel_affiliate_{int(time.time())}_{source}")
        with open(path, 'w') as f:
            json.dump({"data": data}, f, indent=4)
        logger.info(f"✅ Found {len(data)} affiliate indicators -> {path}")

if __name__ == "__main__":
    AffiliateAnalysis().run()
