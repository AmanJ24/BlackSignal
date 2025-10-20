import requests
import json
import socket
import time
from typing import Dict, Any, List
from datetime import datetime

# Custom exception for infrastructure mapping errors
class InfrastructureMappingError(Exception):
    pass

class InfrastructureMapper:
    SHODAN_API_URL = "https://api.shodan.io/shodan/host/"
    ABUSEIPDB_API_URL = "https://api.abuseipdb.com/api/v2/check"
    BGPVIEW_API_URL = "https://api.bgpview.io/ip/"
    
    def __init__(self, shodan_api_key: str = None, abuseipdb_api_key: str = None, use_mock_data: bool = False):
        self.shodan_api_key = shodan_api_key
        self.abuseipdb_api_key = abuseipdb_api_key
        self.use_mock_data = use_mock_data
        
        # Check if API keys are provided
        if not shodan_api_key or shodan_api_key == "your_shodan_api_key":
            print("⚠️  No valid Shodan API key provided, using mock data")
            self.use_mock_data = True
            
        if not abuseipdb_api_key or abuseipdb_api_key == "your_abuseipdb_api_key":
            print("⚠️  No valid AbuseIPDB API key provided, using mock data")
            self.use_mock_data = True

    def map_infrastructure(self, ip_address: str) -> Dict[str, Any]:
        """Map infrastructure for a given IP address"""
        result = {
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat(),
            'data_sources': []
        }
        
        try:
            # Basic IP validation
            if not self._is_valid_ip(ip_address):
                raise InfrastructureMappingError(f"Invalid IP address: {ip_address}")
            
            # Shodan API call
            shodan_data = self.query_shodan(ip_address)
            if shodan_data:
                result['shodan'] = shodan_data
                result['data_sources'].append('shodan')

            # AbuseIPDB API call
            abuseipdb_data = self.query_abuseipdb(ip_address)
            if abuseipdb_data:
                result['abuseipdb'] = abuseipdb_data
                result['data_sources'].append('abuseipdb')

            # BGPView API call (free, no API key needed)
            bgpview_data = self.query_bgpview(ip_address)
            if bgpview_data:
                result['bgpview'] = bgpview_data
                result['data_sources'].append('bgpview')
                
            # Infrastructure analysis
            result['analysis'] = self._analyze_infrastructure(result)

        except Exception as e:
            if self.use_mock_data:
                print(f"🔄 API error, using mock data: {e}")
                return self._get_mock_data(ip_address)
            else:
                raise InfrastructureMappingError(f"Error mapping infrastructure: {e}")

        return result

    def query_shodan(self, ip_address: str) -> Dict[str, Any]:
        if self.use_mock_data:
            return {"banner": f"Mock Shodan data for {ip_address}"}

        response = requests.get(f"{self.SHODAN_API_URL}{ip_address}",
                                headers={"API-Key": self.shodan_api_key})
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def query_abuseipdb(self, ip_address: str) -> Dict[str, Any]:
        if self.use_mock_data:
            return {"data": f"Mock AbuseIPDB data for {ip_address}"}

        response = requests.get(
            f"{self.ABUSEIPDB_API_URL}",
            headers={"Key": self.abuseipdb_api_key,
                     "Accept": "application/json"},
            params={"ipAddress": ip_address, "maxAgeInDays": 90})
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def query_bgpview(self, ip_address: str) -> Dict[str, Any]:
        response = requests.get(f"{self.BGPVIEW_API_URL}{ip_address}")
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def _get_mock_data(self, ip_address: str) -> Dict[str, Any]:
        """Generate mock data for testing when APIs are not available"""
        mock_data = {
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat(),
            "data_sources": ["mock_shodan", "mock_abuseipdb", "mock_bgpview"],
            "shodan": {
                "os": "Linux",
                "ports": [22, 80, 443],
                "vulns": [],
                "org": "Mock Organization",
                "isp": "Mock ISP",
                "country_code": "US",
                "city": "Mock City"
            },
            "abuseipdb": {
                "data": {
                    "ipAddress": ip_address,
                    "isPublic": True,
                    "ipVersion": 4,
                    "isWhitelisted": False,
                    "abuseConfidencePercentage": 0,
                    "countryCode": "US",
                    "usageType": "Data Center/Web Hosting/Transit",
                    "isp": "Mock ISP",
                    "domain": "mock-domain.com",
                    "totalReports": 0,
                    "numDistinctUsers": 0
                }
            },
            "bgpview": {
                "data": {
                    "ip": ip_address,
                    "ptr_record": f"mock-ptr-{ip_address.replace('.', '-')}.com",
                    "rir_allocation": {
                        "rir_name": "ARIN",
                        "country_code": "US",
                        "date_allocated": "2000-01-01 00:00:00",
                        "allocation_status": "allocated"
                    },
                    "prefixes": [
                        {
                            "prefix": f"{ip_address}/24",
                            "ip": ip_address,
                            "cidr": 24,
                            "asn": {
                                "asn": 15169,
                                "name": "GOOGLE",
                                "description": "Google LLC",
                                "country_code": "US"
                            }
                        }
                    ]
                }
            }
        }
        
        # Add analysis
        mock_data["analysis"] = self._analyze_infrastructure(mock_data)
        return mock_data
    
    def _is_valid_ip(self, ip_address: str) -> bool:
        """Validate IP address format"""
        try:
            socket.inet_aton(ip_address)
            return True
        except socket.error:
            return False
    
    def _analyze_infrastructure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze infrastructure data to identify potential threats"""
        analysis = {
            "risk_score": 0,
            "risk_factors": [],
            "infrastructure_type": "unknown",
            "hosting_provider": "unknown",
            "geolocation": {},
            "recommendations": []
        }
        
        # Analyze based on available data sources
        if "abuseipdb" in data and data["abuseipdb"]:
            abuse_data = data["abuseipdb"].get("data", {})
            confidence = abuse_data.get("abuseConfidencePercentage", 0)
            
            if confidence > 75:
                analysis["risk_score"] += 50
                analysis["risk_factors"].append("High abuse confidence score")
            elif confidence > 25:
                analysis["risk_score"] += 25
                analysis["risk_factors"].append("Moderate abuse confidence score")
            
            # Extract geolocation
            analysis["geolocation"] = {
                "country": abuse_data.get("countryCode", "unknown"),
                "isp": abuse_data.get("isp", "unknown"),
                "usage_type": abuse_data.get("usageType", "unknown")
            }
            
            # Check for hosting/VPN indicators
            usage_type = abuse_data.get("usageType", "").lower()
            if "hosting" in usage_type or "data center" in usage_type:
                analysis["infrastructure_type"] = "hosting/datacenter"
                analysis["risk_score"] += 10
                analysis["risk_factors"].append("Hosting/Data center IP")
        
        if "shodan" in data and data["shodan"]:
            shodan_data = data["shodan"]
            
            # Check for common malicious ports
            ports = shodan_data.get("ports", [])
            suspicious_ports = [1080, 4444, 8080, 9050]  # SOCKS, common backdoors, Tor
            
            for port in ports:
                if port in suspicious_ports:
                    analysis["risk_score"] += 15
                    analysis["risk_factors"].append(f"Suspicious port {port} open")
            
            # Check for vulnerabilities
            vulns = shodan_data.get("vulns", [])
            if vulns:
                analysis["risk_score"] += len(vulns) * 10
                analysis["risk_factors"].append(f"{len(vulns)} known vulnerabilities")
        
        # Generate recommendations
        if analysis["risk_score"] > 50:
            analysis["recommendations"].append("High risk IP - consider blocking")
            analysis["recommendations"].append("Monitor for suspicious activity")
        elif analysis["risk_score"] > 25:
            analysis["recommendations"].append("Moderate risk - monitor closely")
        else:
            analysis["recommendations"].append("Low risk IP")
        
        return analysis
    
    def process_sample_data(self, sample_file: str) -> List[Dict[str, Any]]:
        """Process sample data file and map infrastructure for all IPs"""
        results = []
        
        try:
            with open(sample_file, 'r') as f:
                data = json.load(f)
            
            print(f"📊 Processing sample data from {sample_file}")
            
            for ioc_batch in data.get("extracted_iocs", []):
                source = ioc_batch.get("source", "unknown")
                ip_addresses = ioc_batch.get("ip_addresses", [])
                
                print(f"\n🔍 Processing {len(ip_addresses)} IPs from {source}")
                
                for ip in ip_addresses:
                    try:
                        print(f"  📍 Mapping infrastructure for {ip}...")
                        result = self.map_infrastructure(ip)
                        result["source"] = source
                        results.append(result)
                        
                        # Add a small delay to avoid overwhelming APIs
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"  ❌ Error processing {ip}: {e}")
                        continue
            
            print(f"\n✅ Successfully processed {len(results)} IP addresses")
            return results
            
        except Exception as e:
            raise InfrastructureMappingError(f"Error processing sample data: {e}")

def send_to_webhook(data: List[Dict[str, Any]]):
    """Sends the infrastructure analysis results to the n8n webhook."""
    webhook_url = get_n8n_webhook_url("infra-mapping") # Assuming you have this in config
    if not webhook_url:
        print("Webhook URL for 'infra-mapping' not configured. Skipping.")
        return False
    try:
        payload = {
            "timestamp": datetime.now().isoformat(),
            "feature": "Infrastructure Mapping",
            "results_count": len(data),
            "results": data
        }
        response = requests.post(webhook_url, json=payload, timeout=20)
        response.raise_for_status()
        print(f"✅ Successfully sent {len(data)} infrastructure reports to webhook.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send data to webhook: {e}")
        return False



# Main Function
if __name__ == "__main__":
    # --- This part would be dynamically loaded in a real pipeline ---
    # For testing, we use a sample list of IPs.
    sample_ips = ["8.8.8.8", "1.1.1.1", "91.198.174.192"] # Google, Cloudflare, Wikipedia

    # Load API keys from config/environment
    shodan_key = get_api_key("shodan")
    abuseipdb_key = get_api_key("abuseipdb")
    
    # Initialize the mapper. It will automatically use mock data if keys are missing.
    mapper = InfrastructureMapper(shodan_api_key=shodan_key, abuseipdb_api_key=abuseipdb_key)
    
    all_results = []
    print(f"🚀 Starting infrastructure mapping for {len(sample_ips)} IPs...")
    
    for ip in sample_ips:
        try:
            print(f"\n--- Mapping IP: {ip} ---")
            result = mapper.map_infrastructure(ip)
            all_results.append(result)
            print(json.dumps(result, indent=2))
            
            # Respect rate limits, even in testing
            time.sleep(1) 
            
        except InfrastructureMappingError as e:
            print(f"❗️ Could not map IP {ip}: {e}")

    # Send the collected results to the webhook
    if all_results:
        send_to_webhook(all_results)

        try:
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'infrastructure_mapping_results.json')
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"💾 Results also saved locally to {output_file}")
        except Exception as e:
            print(f"Could not save results locally: {e}")

    else:
        print("No results to send to webhook.")

    print("\n✅ Infrastructure mapping complete.")
