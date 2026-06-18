import os
import sys
import json
import re
import logging
import glob
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from config import settings as config
except ImportError:
    import config

logger = logging.getLogger("HashExtractor")

class HashExtractor:
    """
    Extracts potential malware hashes (MD5, SHA1, SHA256) from raw text.
    """

    PATTERNS = {
        "md5": r'\b[a-fA-F0-9]{32}\b',
        "sha1": r'\b[a-fA-F0-9]{40}\b',
        "sha256": r'\b[a-fA-F0-9]{64}\b'
    }

    def run(self):
        raw_path = os.path.join(config.BASE_DIR, "data", "raw", "*.json")
        files = glob.glob(raw_path)
        
        from core.state_tracker import StateTracker
        tracker = StateTracker(config.STATE_DB_PATH)

        for file_path in files:
            if "tor_relays" in os.path.basename(file_path):
                continue
            if tracker.is_processed("hash_extractor", file_path):
                continue
            self._process_file(file_path)

    def _process_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Flatten content to string
            text_content = json.dumps(data.get("data", []))
            
            extracted_hashes = []
            
            for hash_type, pattern in self.PATTERNS.items():
                matches = set(re.findall(pattern, text_content))
                for match in matches:
                    extracted_hashes.append({
                        "id": match,
                        "type": "hash",
                        "subtype": hash_type,
                        "confidence": 1.0, # Regex match is technically definite, context determines malice
                        "source": os.path.basename(file_path)
                    })

            if extracted_hashes:
                self._save(extracted_hashes, os.path.basename(file_path))

            # Mark processed in SQLite DB to prevent redundant execution
            from core.state_tracker import StateTracker
            StateTracker(config.STATE_DB_PATH).mark_processed("hash_extractor", file_path)
        except Exception as e:
            logger.error(f"❌ Failed to process hashes in {file_path}: {e}")

    def _save(self, hashes, source):
        output = {
            "meta": {
                "processor": "hash_extractor",
                "source": source,
                "count": len(hashes)
            },
            "data": hashes
        }
        filename = f"normalized_hashes_{int(time.time())}_{source}"
        path = os.path.join(config.BASE_DIR, "data", "normalized", filename)
        
        with open(path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"✅ Extracted {len(hashes)} hashes -> {filename}")

if __name__ == "__main__":
    HashExtractor().run()
