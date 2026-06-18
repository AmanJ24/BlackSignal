import time
import requests
from .utils import BaseEnricher

from config import settings as config

class InfrastructureMapper(BaseEnricher):
    def __init__(self):
        super().__init__("Infra_Mapper")
        self.shodan_key = config.SHODAN_API_KEY

    def run(self):
        files = self.get_normalized_files()
        for file_path in files:
            data = self.load_data(file_path)
            enriched_items = []
            
            for item in data.get("data", []):
                if item.get("type") == "ipv4":
                    evidence = []
                    
                    # 1. ASN/BGP Lookup (Free)
                    bgp = self._lookup_bgpview(item["id"])
                    if bgp: evidence.extend(bgp)
                    
                    # 2. Shodan Lookup (Requires Key)
                    if self.shodan_key:
                        shodan = self._lookup_shodan(item["id"])
                        if shodan: evidence.extend(shodan)
                    
                    if evidence:
                        item.setdefault("evidence", {})["infrastructure"] = evidence
                        enriched_items.append(item)
            
            if enriched_items:
                self.save_enriched(enriched_items, file_path)
            else:
                from core.state_tracker import StateTracker
                StateTracker(config.STATE_DB_PATH).mark_processed(self.name, file_path)

    def _lookup_bgpview(self, ip):
        try:
            time.sleep(1)
            resp = self.session.get(f"https://api.bgpview.io/ip/{ip}", timeout=5)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                asn = data.get("asn", {}).get("asn")
                desc = data.get("asn", {}).get("description", "").lower()
                
                signals = []
                # Check for hosting/VPN keywords
                suspicious_terms = ["hosting", "datacenter", "vpn", "cloud"]
                if any(x in desc for x in suspicious_terms):
                    signals.append({
                        "type": "hosting_provider_asn",
                        "description": f"ASN {asn}: {desc}",
                        "confidence": 0.6,
                        "source_feature": "infra_mapper"
                    })
                return signals
        except Exception:
            pass
        return None

    def _lookup_shodan(self, ip):
        try:
            time.sleep(1)
            resp = self.session.get(
                f"https://api.shodan.io/shodan/host/{ip}?key={self.shodan_key}", 
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                ports = data.get("ports", [])
                
                signals = []
                # Check for risky ports
                risky_ports = [22, 3389, 445, 23]
                found_risky = set(ports).intersection(risky_ports)
                
                if found_risky:
                    signals.append({
                        "type": "risky_open_ports",
                        "description": f"Open ports: {list(found_risky)}",
                        "confidence": 0.7,
                        "source_feature": "infra_mapper"
                    })
                return signals
        except Exception:
            pass
        return None

if __name__ == "__main__":
    InfrastructureMapper().run()
