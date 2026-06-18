import os
import sys
import json
import logging
import glob
import time
from textblob import TextBlob # pip install textblob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import settings as config
except ImportError:
    import config

logger = logging.getLogger("BehavioralAnalysis")

class BehavioralAnalysis:
    def run(self):
        # Reads RAW scraper data because we need full text context
        files = glob.glob(os.path.join(config.BASE_DIR, "data", "raw", "scrape_*.json"))
        
        from core.state_tracker import StateTracker
        tracker = StateTracker(config.STATE_DB_PATH)

        for file_path in files:
            if tracker.is_processed("behavioral_analysis", file_path):
                continue

            with open(file_path, 'r') as f:
                content = json.load(f)
            
            analyzed_items = []
            for item in content.get("data", []):
                text = item.get("raw_text", "")
                if not text: continue

                analysis = TextBlob(text)
                
                evidence = []
                
                # Sentiment Analysis
                if analysis.sentiment.polarity < -0.5:
                    evidence.append({
                        "type": "negative_sentiment",
                        "confidence": 0.6,
                        "source_feature": "behavioral_analysis"
                    })
                
                # Keyword Risk Analysis
                risk_keywords = ["ransom", "leak", "database", "ssn", "exploit"]
                found_keywords = [kw for kw in risk_keywords if kw in text.lower()]
                
                if found_keywords:
                    evidence.append({
                        "type": "high_risk_keywords",
                        "description": f"Found: {found_keywords}",
                        "confidence": 0.8,
                        "source_feature": "behavioral_analysis"
                    })
                
                if evidence:
                    item["evidence"] = {"behavioral": evidence}
                    analyzed_items.append(item)

            if analyzed_items:
                self._save(analyzed_items, os.path.basename(file_path))

            # Mark processed in StateTracker
            tracker.mark_processed("behavioral_analysis", file_path)

    def _save(self, data, source):
        # Save to Intelligence folder
        path = os.path.join(config.BASE_DIR, "data", "intelligence", f"intel_behavior_{int(time.time())}_{source}")
        output = {
            "meta": {
                "feature": "behavioral_analysis",
                "source": source,
                "timestamp": int(time.time())
            },
            "data": data
        }
        with open(path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"✅ Analyzed behavior for {len(data)} items -> {path}")

if __name__ == "__main__":
    BehavioralAnalysis().run()
