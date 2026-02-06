import os
import sys
import json
import glob
import time
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import settings as config
except ImportError:
    import config

class BaseEnricher:
    """
    Base class to handle reading normalized data and saving enriched results.
    """
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        logging.basicConfig(level=logging.INFO)

    def get_normalized_files(self):
        """Finds most recent normalized files."""
        return glob.glob(os.path.join(config.BASE_DIR, "data", "normalized", "*.json"))

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
                "source": source_file,
                "timestamp": timestamp,
                "count": len(data)
            },
            "data": data
        }

        with open(out_path, 'w') as f:
            json.dump(output, f, indent=4)
        
        self.logger.info(f"✅ Saved enriched data to {filename}")
