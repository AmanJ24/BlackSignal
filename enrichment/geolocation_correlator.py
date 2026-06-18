import time
import requests
from .utils import BaseEnricher

from config import settings as config

class GeoCorrelator(BaseEnricher):
    def __init__(self):
        super().__init__("Geo_Correlator")
        # List of countries often associated with threat actor infrastructure
        self.high_risk_countries = ["RU", "CN", "KP", "IR", "BY"] 

    def run(self):
        files = self.get_normalized_files()
        for file_path in files:
            data = self.load_data(file_path)
            enriched_items = []
            
            for item in data.get("data", []):
                if item.get("type") == "ipv4":
                    geo = self._lookup_ip_api(item["id"])
                    if geo:
                        item.setdefault("evidence", {})["infrastructure"] = geo
                        enriched_items.append(item)
            
            if enriched_items:
                self.save_enriched(enriched_items, file_path)
            else:
                from core.state_tracker import StateTracker
                StateTracker(config.STATE_DB_PATH).mark_processed(self.name, file_path)

    def _lookup_ip_api(self, ip):
        try:
            # IP-API (Free) limits to 45 requests per minute
            time.sleep(1.5) 
            resp = self.session.get(f"http://ip-api.com/json/{ip}", timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                country = data.get("countryCode")
                
                if country in self.high_risk_countries:
                    return [{
                        "type": "high_risk_geolocation",
                        "description": f"Hosted in {data.get('country')}",
                        "confidence": 0.5, # Country alone isn't proof, but a signal
                        "source_feature": "geo_correlator"
                    }]
        except Exception:
            pass
        return None

if __name__ == "__main__":
    GeoCorrelator().run()
