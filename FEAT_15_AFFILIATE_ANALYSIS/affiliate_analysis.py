#!/usr/bin/env python3
"""
Feature 15: Affiliate Recruitment/Payment Analysis
Detects RaaS structures by analyzing BTC reuse patterns, affiliate referrals, and promo posts.
"""

import json
import re
import sys
import os
from collections import defaultdict, Counter
from datetime import datetime
import requests

# Add parent directory to path for config import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from config import get_webhook_url
except ImportError:
    print("Warning: config.py not found. Using fallback webhook URL.")
    def get_webhook_url(feature_name):
        return f"https://sipiv63984.app.n8n.cloud/webhook-test/{feature_name}"

class AffiliateAnalyzer:
    def __init__(self):
        self.webhook_url = get_webhook_url("affiliate-analysis")
        
        # Pattern definitions for affiliate detection
        self.affiliate_keywords = [
            r'\baffiliate\b', r'\bpartner\b', r'\bteam\b', r'\bjoin\b',
            r'\brecruit\b', r'\bhire\b', r'\bcollaborate\b', r'\bgroup\b',
            r'\bnetwork\b', r'\bmember\b', r'\bdivision\b', r'\bbranch\b'
        ]
        
        self.payment_keywords = [
            r'\bcommission\b', r'\bpercentage\b', r'\bcut\b', r'\bshare\b',
            r'\bpayout\b', r'\breward\b', r'\bbonus\b', r'\bprofit\b',
            r'\bearnings\b', r'\bincome\b', r'\bsplit\b', r'\bfee\b'
        ]
        
        self.btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
        self.percentage_pattern = r'\b\d{1,3}%\b'
        
    def extract_btc_addresses(self, text):
        """Extract Bitcoin addresses from text"""
        if not text:
            return []
        
        matches = re.findall(self.btc_pattern, str(text), re.IGNORECASE)
        return list(set(matches))  # Remove duplicates
        
    def detect_affiliate_mentions(self, text):
        """Detect affiliate-related keywords in text"""
        if not text:
            return []
        
        text_lower = str(text).lower()
        mentions = []
        
        for pattern in self.affiliate_keywords:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            mentions.extend(matches)
            
        return mentions
        
    def detect_payment_mentions(self, text):
        """Detect payment-related keywords in text"""
        if not text:
            return []
        
        text_lower = str(text).lower()
        mentions = []
        
        for pattern in self.payment_keywords:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            mentions.extend(matches)
            
        # Also look for percentage mentions
        percentages = re.findall(self.percentage_pattern, str(text))
        mentions.extend(percentages)
        
        return mentions
        
    def analyze_btc_reuse(self, posts):
        """Analyze BTC address reuse patterns across posts"""
        btc_usage = defaultdict(list)
        
        for post in posts:
            post_id = post.get('id', 'unknown')
            author = post.get('author', 'unknown')
            content = f"{post.get('title', '')} {post.get('description', '')}"
            
            btc_addresses = self.extract_btc_addresses(content)
            
            for btc in btc_addresses:
                btc_usage[btc].append({
                    'post_id': post_id,
                    'author': author,
                    'content_snippet': content[:100] + '...' if len(content) > 100 else content
                })
        
        # Identify reused addresses (used by multiple authors or posts)
        reused_addresses = {}
        for btc, usage_list in btc_usage.items():
            if len(usage_list) > 1:
                authors = set(item['author'] for item in usage_list)
                reused_addresses[btc] = {
                    'usage_count': len(usage_list),
                    'unique_authors': len(authors),
                    'authors': list(authors),
                    'posts': usage_list
                }
        
        return reused_addresses
        
    def analyze_author_patterns(self, posts):
        """Analyze patterns in author behavior for recruitment indicators"""
        author_analysis = defaultdict(lambda: {
            'posts': [],
            'affiliate_mentions': 0,
            'payment_mentions': 0,
            'btc_addresses': set(),
            'total_posts': 0,
            'recruitment_score': 0
        })
        
        for post in posts:
            author = post.get('author', 'unknown')
            content = f"{post.get('title', '')} {post.get('description', '')}"
            
            # Count mentions
            affiliate_mentions = self.detect_affiliate_mentions(content)
            payment_mentions = self.detect_payment_mentions(content)
            btc_addresses = self.extract_btc_addresses(content)
            
            # Update author analysis
            author_data = author_analysis[author]
            author_data['posts'].append(post.get('id', 'unknown'))
            author_data['affiliate_mentions'] += len(affiliate_mentions)
            author_data['payment_mentions'] += len(payment_mentions)
            author_data['btc_addresses'].update(btc_addresses)
            author_data['total_posts'] += 1
            
            # Calculate recruitment score
            score = 0
            score += len(affiliate_mentions) * 10  # High weight for affiliate mentions
            score += len(payment_mentions) * 8    # High weight for payment mentions
            score += len(btc_addresses) * 5       # Medium weight for BTC addresses
            
            author_data['recruitment_score'] += score
        
        # Convert sets to lists for JSON serialization
        for author, data in author_analysis.items():
            data['btc_addresses'] = list(data['btc_addresses'])
            data['avg_recruitment_score'] = (
                data['recruitment_score'] / data['total_posts'] 
                if data['total_posts'] > 0 else 0
            )
        
        return dict(author_analysis)
        
    def detect_hierarchy_indicators(self, posts):
        """Detect indicators of hierarchical structures in RaaS operations"""
        hierarchy_indicators = []
        
        hierarchy_keywords = [
            r'\bleader\b', r'\bboss\b', r'\bmanager\b', r'\badmin\b',
            r'\bmoderator\b', r'\bsupervisor\b', r'\bcoordinator\b',
            r'\bdirector\b', r'\bchief\b', r'\bhead\b'
        ]
        
        for post in posts:
            content = f"{post.get('title', '')} {post.get('description', '')}"
            content_lower = content.lower()
            
            for pattern in hierarchy_keywords:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                if matches:
                    hierarchy_indicators.append({
                        'post_id': post.get('id', 'unknown'),
                        'author': post.get('author', 'unknown'),
                        'hierarchy_terms': matches,
                        'content_snippet': content[:150] + '...' if len(content) > 150 else content
                    })
        
        return hierarchy_indicators
        
    def analyze_posts(self, posts):
        """Main analysis function"""
        if not posts:
            print("No posts provided for analysis")
            return None
        
        print(f"Analyzing {len(posts)} posts for affiliate recruitment patterns...")
        
        # Perform various analyses
        btc_reuse = self.analyze_btc_reuse(posts)
        author_patterns = self.analyze_author_patterns(posts)
        hierarchy_indicators = self.detect_hierarchy_indicators(posts)
        
        # Generate summary statistics
        total_authors = len(author_patterns)
        high_risk_authors = len([
            author for author, data in author_patterns.items() 
            if data['avg_recruitment_score'] > 20
        ])
        
        analysis_result = {
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_type': 'affiliate_recruitment_payment',
            'input_stats': {
                'total_posts': len(posts),
                'unique_authors': total_authors,
                'posts_analyzed': len(posts)
            },
            'btc_reuse_analysis': {
                'reused_addresses_count': len(btc_reuse),
                'reused_addresses': btc_reuse
            },
            'author_analysis': {
                'total_authors': total_authors,
                'high_risk_authors': high_risk_authors,
                'author_details': author_patterns
            },
            'hierarchy_analysis': {
                'hierarchy_indicators_found': len(hierarchy_indicators),
                'indicators': hierarchy_indicators
            },
            'risk_assessment': {
                'overall_risk_level': self.calculate_overall_risk(
                    btc_reuse, author_patterns, hierarchy_indicators
                ),
                'key_findings': self.generate_key_findings(
                    btc_reuse, author_patterns, hierarchy_indicators
                )
            }
        }
        
        return analysis_result
        
    def calculate_overall_risk(self, btc_reuse, author_patterns, hierarchy_indicators):
        """Calculate overall risk level based on analysis results"""
        risk_score = 0
        
        # BTC reuse contributes to risk
        risk_score += len(btc_reuse) * 15
        
        # High-risk authors contribute to risk
        high_risk_authors = len([
            author for author, data in author_patterns.items() 
            if data['avg_recruitment_score'] > 20
        ])
        risk_score += high_risk_authors * 25
        
        # Hierarchy indicators contribute to risk
        risk_score += len(hierarchy_indicators) * 10
        
        # Determine risk level
        if risk_score >= 100:
            return "HIGH"
        elif risk_score >= 50:
            return "MEDIUM" 
        elif risk_score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
            
    def generate_key_findings(self, btc_reuse, author_patterns, hierarchy_indicators):
        """Generate key findings summary"""
        findings = []
        
        if btc_reuse:
            findings.append(f"Found {len(btc_reuse)} BTC addresses reused across multiple posts/authors")
            
        high_risk_authors = [
            author for author, data in author_patterns.items() 
            if data['avg_recruitment_score'] > 20
        ]
        if high_risk_authors:
            findings.append(f"Identified {len(high_risk_authors)} high-risk authors with recruitment indicators")
            
        if hierarchy_indicators:
            findings.append(f"Detected {len(hierarchy_indicators)} posts with hierarchical structure indicators")
            
        if not findings:
            findings.append("No significant affiliate recruitment patterns detected")
            
        return findings
        
    def send_webhook(self, data):
        """Send analysis results to n8n webhook"""
        try:
            print(f"Sending affiliate analysis data to webhook: {self.webhook_url}")
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.webhook_url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("✅ Webhook sent successfully!")
                return True
            else:
                print(f"❌ Webhook failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Webhook request timed out (expected if webhook not set up)")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Connection error (expected if webhook not set up)")
            return False
        except Exception as e:
            print(f"❌ Webhook error: {str(e)}")
            return False

def load_mock_data():
    """Load mock data for testing"""
    mock_posts = [
        {
            'id': 'post_001',
            'author': 'CryptoPartner99',
            'title': 'Looking for affiliate partners - 60% commission',
            'description': 'Join our team and earn 60% commission on all sales. We provide the best malware tools. Contact via BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa for partnership details.',
            'timestamp': '2024-01-15T10:30:00Z'
        },
        {
            'id': 'post_002', 
            'author': 'MalwareKing',
            'title': 'Team expansion - hiring skilled members',
            'description': 'Our group is expanding! Looking for dedicated members to join our network. Excellent profit sharing available. Payment address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            'timestamp': '2024-01-16T14:20:00Z'
        },
        {
            'id': 'post_003',
            'author': 'RansomAdmin',
            'title': 'Division leaders needed - management positions',
            'description': 'We need experienced coordinators to manage our affiliate program. High earnings potential with 70% cut. Apply now!',
            'timestamp': '2024-01-17T09:15:00Z'
        },
        {
            'id': 'post_004',
            'author': 'CryptoPartner99',
            'title': 'New tool release - partners get early access',
            'description': 'Latest version available for all team members. Commission structure updated. Same BTC address for payments: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            'timestamp': '2024-01-18T16:45:00Z'
        },
        {
            'id': 'post_005',
            'author': 'IndependentSeller',
            'title': 'Quality products for sale',
            'description': 'Selling various tools and services. No affiliates needed. Payment: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
            'timestamp': '2024-01-19T11:30:00Z'
        }
    ]
    
    return mock_posts

def main():
    """Main execution function"""
    print("🔍 Starting Affiliate Recruitment/Payment Analysis (Feature 15)")
    print("=" * 60)
    
    analyzer = AffiliateAnalyzer()
    
    # Load mock data for testing
    posts = load_mock_data()
    print(f"📊 Loaded {len(posts)} mock posts for analysis")
    
    # Perform analysis
    try:
        analysis_result = analyzer.analyze_posts(posts)
        
        if analysis_result:
            print("\n" + "=" * 60)
            print("📋 ANALYSIS RESULTS SUMMARY:")
            print("=" * 60)
            
            print(f"Total Posts Analyzed: {analysis_result['input_stats']['total_posts']}")
            print(f"Unique Authors: {analysis_result['input_stats']['unique_authors']}")
            print(f"BTC Addresses Reused: {analysis_result['btc_reuse_analysis']['reused_addresses_count']}")
            print(f"High-Risk Authors: {analysis_result['author_analysis']['high_risk_authors']}")
            print(f"Hierarchy Indicators: {analysis_result['hierarchy_analysis']['hierarchy_indicators_found']}")
            print(f"Overall Risk Level: {analysis_result['risk_assessment']['overall_risk_level']}")
            
            print("\n📌 Key Findings:")
            for finding in analysis_result['risk_assessment']['key_findings']:
                print(f"  • {finding}")
            
            # Send to webhook
            print("\n" + "=" * 60)
            webhook_success = analyzer.send_webhook(analysis_result)
            
            # Go up one directory from the current script, then into the 'output' folder
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
            os.makedirs(output_dir, exist_ok=True) # Create the directory if it doesn't exist
            output_file = os.path.join(output_dir, 'affiliate_analysis_results.json')

            with open(output_file, 'w') as f:
                json.dump(analysis_result, f, indent=2)

        else:
            print("❌ Analysis failed - no results generated")
            
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return 1
    
    print("\n✅ Affiliate Recruitment/Payment Analysis completed!")
    return 0

if __name__ == "__main__":
    exit(main())
