import os
import time
import requests
from dotenv import load_dotenv
from .utils import BaseEnricher

load_dotenv(".secrets.env")

class APIEnricher(BaseEnricher):
    def __init__(self):
        super().__init__("API_Enricher")
        self.vt_key = os.getenv("VIRUSTOTAL_API_KEY")
        self.abuse_key = os.getenv("ABUSEIPDB_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DarkWeb-OSINT-Pipeline/2.0"})

    def run(self):
        files = self.get_normalized_files()
        for file_path in files:
            data = self.load_data(file_path)
            enriched_items = []
            
            for item in data.get("data", []):
                # Enrich Hashes (VirusTotal)
                if item.get("type") == "hash" and self.vt_key:
                    result = self._check_virustotal(item["id"])
                    if result:
                        # MERGE evidence into the item
                        item.setdefault("evidence", {})["ioc"] = result
                        enriched_items.append(item)
                
                # Enrich IPs (AbuseIPDB)
                elif item.get("type") == "ipv4" and self.abuse_key:
                    result = self._check_abuseipdb(item["id"])
                    if result:
                        item.setdefault("evidence", {})["ioc"] = result
                        enriched_items.append(item)

            if enriched_items:
                self.save_enriched(enriched_items, file_path)

    def _check_virustotal(self, hash_val):
        """Queries VirusTotal v3 API"""
        url = f"https://www.virustotal.com/api/v3/files/{hash_val}"
        headers = {"x-apikey": self.vt_key}
        
        try:
            # VT Rate limit: 4 requests/min for free tier => 15s sleep
            time.sleep(15) 
            resp = self.session.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                
                if malicious > 0:
                    # Calculate confidence based on detection ratio
                    confidence = min(malicious / 10.0, 1.0) # 10 detections = 100% confidence
                    return [{
                        "type": "virustotal_detection",
                        "description": f"Detected by {malicious} engines",
                        "confidence": confidence,
                        "source_feature": "api_enrichment"
                    }]
        except Exception as e:
            self.logger.error(f"VT Error for {hash_val}: {e}")
        return None

    def _check_abuseipdb(self, ip):
        """Queries AbuseIPDB"""
        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {"Key": self.abuse_key, "Accept": "application/json"}
        params = {"ipAddress": ip, "maxAgeInDays": 90}
        
        try:
            time.sleep(1) # Mild rate limiting
            resp = self.session.get(url, headers=headers, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                score = data.get("abuseConfidenceScore", 0)
                
                if score > 0:
                    return [{
                        "type": "abuseipdb_report",
                        "description": f"Abuse Score: {score}",
                        "confidence": score / 100.0,
                        "source_feature": "api_enrichment"
                    }]
        except Exception as e:
            self.logger.error(f"AbuseIPDB Error for {ip}: {e}")
        return None

if __name__ == "__main__":
    APIEnricher().run()
