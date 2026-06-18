import os
import sys
import json
import logging
import glob
import time
import spacy

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from config import settings as config
except ImportError:
    import config

logger = logging.getLogger("NERExtractor")

class NERExtractor:
    def __init__(self):
        logger.info("🧠 Loading spaCy model (en_core_web_sm)...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )

    def run(self):
        raw_path = os.path.join(config.BASE_DIR, "data", "raw", "*.json")
        from core.state_tracker import StateTracker
        tracker = StateTracker(config.STATE_DB_PATH)

        for file_path in glob.glob(raw_path):
            if "tor_relays" in os.path.basename(file_path):
                continue
            if tracker.is_processed("ner_extractor", file_path):
                continue
            self._process_file(file_path)

    def _process_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # NER works best on actual sentences, not JSON structures.
            # We try to extract "raw_text" fields if they exist (common in our scrapers)
            text_chunks = []
            raw_data = data.get("data", [])
            
            if isinstance(raw_data, list):
                for item in raw_data:
                    if isinstance(item, dict) and "raw_text" in item:
                        text_chunks.append(item["raw_text"])
                    elif isinstance(item, str):
                        text_chunks.append(item)
            
            extracted_entities = []
            
            for text in text_chunks:
                # Limit text length to prevent memory overflows on large blobs
                doc = self.nlp(text[:50000])
                
                for ent in doc.ents:
                    if ent.label_ in ["PERSON", "ORG", "GPE"]:
                        extracted_entities.append({
                            "id": ent.text,
                            "type": "entity",
                            "subtype": ent.label_, # PERSON, ORG, etc.
                            "source": os.path.basename(file_path)
                        })

            # Deduplicate by ID
            unique_entities = {v['id']: v for v in extracted_entities}.values()

            if unique_entities:
                self._save(list(unique_entities), os.path.basename(file_path))

            # Mark processed in SQLite DB to prevent redundant execution
            from core.state_tracker import StateTracker
            StateTracker(config.STATE_DB_PATH).mark_processed("ner_extractor", file_path)
        except Exception as e:
            logger.error(f"❌ Failed to process NER in {file_path}: {e}")

    def _save(self, entities, source):
        output = {
            "meta": {
                "processor": "ner_extractor",
                "source": source,
                "count": len(entities)
            },
            "data": entities
        }
        filename = f"normalized_entities_{int(time.time())}_{source}"
        path = os.path.join(config.BASE_DIR, "data", "normalized", filename)
        
        with open(path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"✅ Extracted {len(entities)} entities -> {filename}")

if __name__ == "__main__":
    NERExtractor().run()
