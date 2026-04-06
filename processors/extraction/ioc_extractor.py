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

logger = logging.getLogger("IOCExtractor")
logging.basicConfig(level=logging.INFO)

class IOCExtractor:
    """
    Parses raw content for technical indicators (IPs, BTC, Emails, URLs).
    Outputs normalized data ready for scoring.
    """

    PATTERNS = {
        # Standard IPv4 (excluding common local ranges in logic, but matching structure here)
        "ipv4": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        
        # Email Addresses
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        
        # Bitcoin Addresses (Legacy & Bech32)
        "btc_wallet": r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b',
        
        # Onion V3 Domains
        "onion_domain": r'\b[a-z2-7]{56}\.onion\b',
        
        # Ethereum Addresses
        "eth_wallet": r'\b0x[a-fA-F0-9]{40}\b'
    }

    def run(self):
        # Find most recent raw files
        raw_path = os.path.join(config.BASE_DIR, "data", "raw", "*.json")
        files = glob.glob(raw_path)
        
        if not files:
            logger.warning("⚠️ No raw data files found to process.")
            return

        for file_path in files:
            logger.info(f"🔍 Processing: {os.path.basename(file_path)}")
            self._process_file(file_path)

    def _process_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                content = json.load(f)

            raw_items = content.get("data", [])
            extracted_iocs = []

            # Handle both list formats (scraper output) and simple lists (crawler output)
            if isinstance(raw_items, list):
                text_blob = " ".join([str(item) for item in raw_items])
            else:
                text_blob = str(raw_items)

            for ioc_type, pattern in self.PATTERNS.items():
                matches = set(re.findall(pattern, text_blob))
                for match in matches:
                    # BASIC FILTERING (Remove Local IPs)
                    if ioc_type == "ipv4" and (match.startswith("127.") or match.startswith("192.168.")):
                        continue
                    
                    extracted_iocs.append({
                        "id": match,
                        "type": ioc_type,
                        "source_file": os.path.basename(file_path),
                        "discovered_at": content.get("meta", {}).get("timestamp")
                    })

            if extracted_iocs:
                self._save_normalized(extracted_iocs, os.path.basename(file_path))

        except Exception as e:
            logger.error(f"❌ Failed to process {file_path}: {e}")

    def _save_normalized(self, iocs, source_filename):
        output = {
            "meta": {
                "processor": "ioc_extractor",
                "source": source_filename,
                "count": len(iocs)
            },
            "data": iocs
        }
        
        filename = f"normalized_iocs_{int(time.time())}_{source_filename}"
        out_path = os.path.join(config.BASE_DIR, "data", "normalized", filename)
        
        with open(out_path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"✅ Extracted {len(iocs)} IOCs -> {out_path}")

if __name__ == "__main__":
    import time
    extractor = IOCExtractor()
    extractor.run()
