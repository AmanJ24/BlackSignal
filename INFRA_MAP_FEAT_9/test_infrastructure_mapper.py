#!/usr/bin/env python3
"""
Test script for Infrastructure Mapping Feature 9
Tests the infrastructure_mapper.py with sample data
"""

import json
from infrastructure_mapper import InfrastructureMapper, InfrastructureMappingError

def main():
    print("🚀 Testing Infrastructure Mapping Feature 9")
    print("=" * 50)
    
    # Initialize mapper (will use mock data since no API keys provided)
    mapper = InfrastructureMapper()
    
    print("\n1️⃣ Testing single IP mapping:")
    print("-" * 30)
    
    test_ips = ["8.8.8.8", "1.1.1.1", "192.168.1.1"]
    
    for ip in test_ips:
        try:
            print(f"\n🔍 Testing IP: {ip}")
            result = mapper.map_infrastructure(ip)
            
            # Display key information
            print(f"  ✅ Status: Successfully mapped")
            print(f"  📊 Data sources: {', '.join(result.get('data_sources', []))}")
            print(f"  🎯 Risk score: {result.get('analysis', {}).get('risk_score', 0)}")
            print(f"  🏗️  Infrastructure type: {result.get('analysis', {}).get('infrastructure_type', 'unknown')}")
            print(f"  🌍 Location: {result.get('analysis', {}).get('geolocation', {}).get('country', 'unknown')}")
            
            risk_factors = result.get('analysis', {}).get('risk_factors', [])
            if risk_factors:
                print(f"  ⚠️  Risk factors: {', '.join(risk_factors)}")
                
        except InfrastructureMappingError as e:
            print(f"  ❌ Error: {e}")
    
    print("\n\n2️⃣ Testing with sample data file:")
    print("-" * 30)
    
    try:
        # Process sample data
        results = mapper.process_sample_data("sample_data.json")
        
        if results:
            print(f"\n📈 Summary Report:")
            print(f"Total IPs processed: {len(results)}")
            
            # Risk analysis summary
            high_risk = [r for r in results if r.get('analysis', {}).get('risk_score', 0) > 50]
            medium_risk = [r for r in results if 25 < r.get('analysis', {}).get('risk_score', 0) <= 50]
            low_risk = [r for r in results if r.get('analysis', {}).get('risk_score', 0) <= 25]
            
            print(f"🔴 High risk IPs: {len(high_risk)}")
            print(f"🟡 Medium risk IPs: {len(medium_risk)}")
            print(f"🟢 Low risk IPs: {len(low_risk)}")
            
            # Show details for high-risk IPs
            if high_risk:
                print(f"\n🚨 High Risk IP Details:")
                for ip_data in high_risk:
                    ip = ip_data.get('ip_address', 'unknown')
                    score = ip_data.get('analysis', {}).get('risk_score', 0)
                    factors = ip_data.get('analysis', {}).get('risk_factors', [])
                    source = ip_data.get('source', 'unknown')
                    print(f"  • {ip} (Score: {score}, Source: {source})")
                    for factor in factors:
                        print(f"    - {factor}")
            
            # Save results to file
            output_file = "infrastructure_mapping_results.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {output_file}")
            
        else:
            print("❌ No results generated")
            
    except Exception as e:
        print(f"❌ Error processing sample data: {e}")
    
    print("\n\n3️⃣ Testing webhook integration:")
    print("-" * 30)
    
    # Test webhook functionality (mock)
    try:
        sample_result = mapper.map_infrastructure("8.8.8.8")
        
        # This would normally send to n8n webhook
        webhook_url = "https://sipiv63984.app.n8n.cloud/webhook-test/infra-mapping"
        
        print(f"🔗 Would send to webhook: {webhook_url}")
        print("📦 Sample payload structure:")
        print(f"  - IP: {sample_result.get('ip_address')}")
        print(f"  - Timestamp: {sample_result.get('timestamp')}")
        print(f"  - Risk Score: {sample_result.get('analysis', {}).get('risk_score')}")
        print(f"  - Data Sources: {len(sample_result.get('data_sources', []))}")
        
        print("✅ Webhook integration ready (API keys needed for real data)")
        
    except Exception as e:
        print(f"❌ Webhook test error: {e}")
    
    print("\n🎉 Infrastructure Mapping Test Complete!")
    print("=" * 50)
    print("\n📝 Next Steps:")
    print("1. Add real API keys for Shodan and AbuseIPDB")
    print("2. Configure n8n webhook endpoint")
    print("3. Integrate with other pipeline features")
    print("4. Set up automated monitoring and alerts")

if __name__ == "__main__":
    main()
