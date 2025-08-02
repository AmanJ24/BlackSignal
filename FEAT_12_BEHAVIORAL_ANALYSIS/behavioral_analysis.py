#!/usr/bin/env python3
"""
FEATURE 12: BEHAVIORAL ANALYSIS
Analyzes vendor behavior patterns from marketplace data including:
- Posting frequency and patterns
- Sentiment analysis of posts
- Price evolution tracking
- Risk scoring based on behavior
- Writing style analysis
"""

import json
import re
import requests
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from textblob import TextBlob
import os
import sys

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_n8n_webhook_url

class BehavioralAnalyzer:
    def __init__(self):
        self.risk_keywords = {
            'high_risk': ['ransomware', 'exploit', '0day', 'government', 'military', 'hack', 'breach'],
            'medium_risk': ['cvv', 'dumps', 'carding', 'fraud', 'stolen', 'cracked'],
            'recruitment': ['affiliate', 'partner', 'recruit', 'join', 'team', 'RaaS'],
            'trust_building': ['trust', 'reliable', 'reputation', 'feedback', 'escrow', 'guarantee']
        }
        
    def load_data(self, file_path):
        """Load mock data from JSON file"""
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def analyze_posting_patterns(self, marketplace_data):
        """Analyze posting frequency and timing patterns"""
        patterns = {}
        
        for entry in marketplace_data:
            vendor = entry['vendor_handle']
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', ''))
            
            if vendor not in patterns:
                patterns[vendor] = {
                    'posts': [],
                    'marketplaces': set(),
                    'total_posts': 0,
                    'avg_time_between_posts': 0,
                    'active_hours': [],
                    'active_days': []
                }
            
            patterns[vendor]['posts'].append(timestamp)
            patterns[vendor]['marketplaces'].add(entry['marketplace'])
            patterns[vendor]['total_posts'] += 1
            patterns[vendor]['active_hours'].append(timestamp.hour)
            patterns[vendor]['active_days'].append(timestamp.weekday())
        
        # Calculate average time between posts
        for vendor, data in patterns.items():
            if len(data['posts']) > 1:
                data['posts'].sort()
                time_diffs = []
                for i in range(1, len(data['posts'])):
                    diff = (data['posts'][i] - data['posts'][i-1]).total_seconds() / 3600  # hours
                    time_diffs.append(diff)
                data['avg_time_between_posts'] = sum(time_diffs) / len(time_diffs) if time_diffs else 0
            
            # Convert datetime objects to ISO strings for JSON serialization
            data['posts'] = [post.isoformat() for post in data['posts']]
            data['marketplaces'] = list(data['marketplaces'])
            data['most_active_hour'] = Counter(data['active_hours']).most_common(1)[0][0] if data['active_hours'] else None
            data['most_active_day'] = Counter(data['active_days']).most_common(1)[0][0] if data['active_days'] else None
        
        return patterns
    
    def analyze_sentiment(self, marketplace_data):
        """Analyze sentiment of vendor posts"""
        sentiment_analysis = {}
        
        for entry in marketplace_data:
            vendor = entry['vendor_handle']
            content = entry['post_content']
            
            if vendor not in sentiment_analysis:
                sentiment_analysis[vendor] = {
                    'sentiments': [],
                    'avg_polarity': 0,
                    'avg_subjectivity': 0,
                    'confidence_indicators': 0,
                    'urgency_indicators': 0
                }
            
            # TextBlob sentiment analysis
            blob = TextBlob(content)
            sentiment_analysis[vendor]['sentiments'].append({
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            })
            
            # Count confidence and urgency indicators
            confidence_words = ['trust', 'reliable', 'guarantee', 'years', 'experience', 'reputation']
            urgency_words = ['limited', 'fast', 'quick', 'urgent', 'now', 'today', 'fresh']
            
            content_lower = content.lower()
            sentiment_analysis[vendor]['confidence_indicators'] += sum(1 for word in confidence_words if word in content_lower)
            sentiment_analysis[vendor]['urgency_indicators'] += sum(1 for word in urgency_words if word in content_lower)
        
        # Calculate averages
        for vendor, data in sentiment_analysis.items():
            if data['sentiments']:
                data['avg_polarity'] = sum(s['polarity'] for s in data['sentiments']) / len(data['sentiments'])
                data['avg_subjectivity'] = sum(s['subjectivity'] for s in data['sentiments']) / len(data['sentiments'])
        
        return sentiment_analysis
    
    def analyze_risk_profile(self, marketplace_data):
        """Calculate risk scores based on content and behavior"""
        risk_profiles = {}
        
        for entry in marketplace_data:
            vendor = entry['vendor_handle']
            content = entry['post_content'].lower()
            
            if vendor not in risk_profiles:
                risk_profiles[vendor] = {
                    'risk_score': 0,
                    'risk_factors': [],
                    'category_scores': {
                        'high_risk': 0,
                        'medium_risk': 0,
                        'recruitment': 0,
                        'trust_building': 0
                    }
                }
            
            # Check for risk keywords
            for category, keywords in self.risk_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in content)
                risk_profiles[vendor]['category_scores'][category] += matches
                
                if matches > 0:
                    risk_profiles[vendor]['risk_factors'].extend([k for k in keywords if k in content])
        
        # Calculate overall risk score
        for vendor, profile in risk_profiles.items():
            score = 0
            score += profile['category_scores']['high_risk'] * 10  # High risk keywords worth 10 points
            score += profile['category_scores']['medium_risk'] * 5  # Medium risk keywords worth 5 points
            score += profile['category_scores']['recruitment'] * 3   # Recruitment keywords worth 3 points
            score -= profile['category_scores']['trust_building'] * 2  # Trust building reduces risk
            
            profile['risk_score'] = max(0, score)  # Ensure non-negative
            profile['risk_level'] = self.categorize_risk(profile['risk_score'])
        
        return risk_profiles
    
    def categorize_risk(self, score):
        """Categorize risk level based on score"""
        if score >= 20:
            return 'CRITICAL'
        elif score >= 10:
            return 'HIGH'
        elif score >= 5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def analyze_price_evolution(self, marketplace_data, previous_data):
        """Analyze price changes and trends"""
        price_analysis = {}
        
        # Extract numeric prices from current data
        for entry in marketplace_data:
            vendor = entry['vendor_handle']
            price_str = entry['price']
            
            if vendor not in price_analysis:
                price_analysis[vendor] = {
                    'current_prices': [],
                    'historical_prices': [],
                    'price_trend': 'stable',
                    'avg_price': 0
                }
            
            # Extract numeric price
            price_match = re.search(r'\$?(\d+(?:\.\d+)?)', price_str)
            if price_match:
                price = float(price_match.group(1))
                price_analysis[vendor]['current_prices'].append(price)
        
        # Add historical data if available
        if previous_data and 'previous_behavioral_data' in previous_data:
            for vendor, historical in previous_data['previous_behavioral_data'].items():
                if vendor in price_analysis and 'price_evolution' in historical:
                    price_analysis[vendor]['historical_prices'] = historical['price_evolution']
        
        # Calculate trends
        for vendor, data in price_analysis.items():
            all_prices = data['historical_prices'] + data['current_prices']
            if len(all_prices) >= 2:
                if all_prices[-1] > all_prices[0]:
                    data['price_trend'] = 'increasing'
                elif all_prices[-1] < all_prices[0]:
                    data['price_trend'] = 'decreasing'
                else:
                    data['price_trend'] = 'stable'
                
                data['avg_price'] = sum(all_prices) / len(all_prices)
        
        return price_analysis
    
    def generate_behavioral_report(self, data):
        """Generate comprehensive behavioral analysis report"""
        marketplace_data = data['marketplace_data']
        
        # Perform all analyses
        patterns = self.analyze_posting_patterns(marketplace_data)
        sentiment = self.analyze_sentiment(marketplace_data)
        risk_profiles = self.analyze_risk_profile(marketplace_data)
        price_evolution = self.analyze_price_evolution(marketplace_data, data)
        
        # Compile comprehensive report
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'vendors_analyzed': len(patterns),
            'behavioral_profiles': {}
        }
        
        for vendor in patterns.keys():
            report['behavioral_profiles'][vendor] = {
                'posting_patterns': patterns.get(vendor, {}),
                'sentiment_analysis': sentiment.get(vendor, {}),
                'risk_profile': risk_profiles.get(vendor, {}),
                'price_analysis': price_evolution.get(vendor, {}),
                'overall_threat_level': self.calculate_threat_level(
                    risk_profiles.get(vendor, {}),
                    sentiment.get(vendor, {}),
                    patterns.get(vendor, {})
                )
            }
        
        return report
    
    def calculate_threat_level(self, risk_profile, sentiment, patterns):
        """Calculate overall threat level based on multiple factors"""
        threat_score = 0
        
        # Risk score contribution
        if risk_profile:
            threat_score += risk_profile.get('risk_score', 0)
        
        # Sentiment contribution (negative sentiment increases threat)
        if sentiment and sentiment.get('avg_polarity', 0) < -0.2:
            threat_score += 5
        
        # Posting frequency contribution (very frequent posting increases threat)
        if patterns and patterns.get('avg_time_between_posts', 0) < 24:  # Less than 24 hours
            threat_score += 3
        
        # Multiple marketplace presence
        if patterns and len(patterns.get('marketplaces', [])) > 2:
            threat_score += 2
        
        # Categorize threat level
        if threat_score >= 25:
            return 'CRITICAL'
        elif threat_score >= 15:
            return 'HIGH'
        elif threat_score >= 8:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def send_to_webhook(self, report):
        """Send analysis report to n8n webhook with comprehensive error handling"""
        try:
            webhook_url = get_n8n_webhook_url('behavioral-analysis')
            print(f"📡 Attempting to send data to: {webhook_url}")
            
            payload = {
                'feature': 'behavioral_analysis',
                'data': report,
                'metadata': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'feature_version': '1.0',
                    'data_source': 'mock_input_data.json'
                }
            }
            
            # Configure request with proper timeout and headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'OSINT-Pipeline-Feature-12/1.0'
            }
            
            response = requests.post(
                webhook_url, 
                json=payload, 
                headers=headers,
                timeout=15,  # Reduced timeout for faster feedback
                verify=True  # SSL verification
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully sent behavioral analysis to webhook")
                print(f"   Response: {response.text[:100]}..." if len(response.text) > 100 else f"   Response: {response.text}")
                return True
            elif response.status_code == 404:
                print(f"⚠️  Webhook endpoint not found (404). Please set up n8n webhook first.")
                print(f"   Expected endpoint: {webhook_url}")
                return False
            elif response.status_code == 502 or response.status_code == 503:
                print(f"⚠️  n8n service temporarily unavailable ({response.status_code})")
                return False
            else:
                print(f"❌ Webhook request failed with status: {response.status_code}")
                print(f"   Response: {response.text[:200]}..." if len(response.text) > 200 else f"   Response: {response.text}")
                return False
                
        except requests.exceptions.ConnectTimeout:
            print(f"⏰ Connection timeout - n8n webhook not responding within 15 seconds")
            print(f"   This is expected if n8n webhook is not set up yet")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 Connection error - cannot reach n8n webhook")
            print(f"   This is expected if n8n webhook is not set up yet")
            print(f"   Details: {str(e)[:100]}...")
            return False
        except requests.exceptions.ReadTimeout:
            print(f"⏰ Read timeout - n8n webhook response took too long")
            return False
        except requests.exceptions.RequestException as e:
            print(f"🌐 Network request error: {str(e)[:100]}...")
            return False
        except json.JSONEncodeError as e:
            print(f"📄 JSON serialization error: {e}")
            print(f"   Check for non-serializable objects in report data")
            return False
        except Exception as e:
            print(f"❌ Unexpected error sending to webhook: {type(e).__name__}: {str(e)[:100]}...")
            return False
    
    def run_analysis(self, data_file='mock_input_data.json'):
        """Main analysis function"""
        print("🔍 Starting Behavioral Analysis (Feature 12)...")
        
        # Load data
        data = self.load_data(data_file)
        if not data:
            print("❌ Failed to load data")
            return
        
        # Generate report
        report = self.generate_behavioral_report(data)
        
        # Display results
        print(f"\n📊 BEHAVIORAL ANALYSIS REPORT - {report['analysis_timestamp']}")
        print("=" * 80)
        
        for vendor, profile in report['behavioral_profiles'].items():
            print(f"\n🔸 VENDOR: {vendor}")
            print(f"   Overall Threat Level: {profile['overall_threat_level']}")
            print(f"   Risk Score: {profile['risk_profile'].get('risk_score', 0)}")
            print(f"   Risk Level: {profile['risk_profile'].get('risk_level', 'UNKNOWN')}")
            print(f"   Total Posts: {profile['posting_patterns'].get('total_posts', 0)}")
            print(f"   Marketplaces: {len(profile['posting_patterns'].get('marketplaces', []))}")
            print(f"   Avg Sentiment: {profile['sentiment_analysis'].get('avg_polarity', 0):.2f}")
            
            if profile['risk_profile'].get('risk_factors'):
                print(f"   Risk Factors: {', '.join(set(profile['risk_profile']['risk_factors']))}")
        
        # Send to webhook
        print("\n📡 Sending results to n8n webhook...")
        self.send_to_webhook(report)
        
        print("\n✅ Behavioral analysis completed!")
        return report

if __name__ == "__main__":
    analyzer = BehavioralAnalyzer()
    analyzer.run_analysis()

