#!/usr/bin/env python3
"""
Feature 15: Affiliate Recruitment/Payment Analysis (Local Version)

Detects Ransomware-as-a-Service (RaaS) structures by analyzing BTC reuse,
affiliate referral keywords, and hierarchical terms in posts. Saves the
analysis to a local JSON file.
"""

import json
import re
import sys
import os
from collections import defaultdict, Counter
from datetime import datetime
import logging

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'affiliate_analysis.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AffiliateAnalyzer:
    """Analyzes posts for signs of affiliate programs and RaaS structures."""

    def __init__(self):
        self.affiliate_keywords = [
            'affiliate', 'partner', 'team', 'join', 'recruit', 'hire',
            'collaborate', 'group', 'network', 'member', 'division', 'branch', 'raas'
        ]
        self.payment_keywords = [
            'commission', 'percentage', 'cut', 'share', 'payout', 'reward',
            'bonus', 'profit', 'earnings', 'income', 'split', 'fee'
        ]
        self.hierarchy_keywords = [
            'leader', 'boss', 'manager', 'admin', 'moderator',
            'supervisor', 'coordinator', 'director', 'chief', 'head'
        ]
        self.btc_pattern = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')

    def analyze_posts(self, posts: list) -> dict:
        """Main analysis function to generate a comprehensive report from posts."""
        if not posts:
            logger.warning("No posts provided for analysis.")
            return {}

        logger.info(f"Analyzing {len(posts)} posts for affiliate recruitment patterns...")
        
        author_patterns = self._analyze_author_patterns(posts)
        btc_reuse = self._analyze_btc_reuse(posts)
        hierarchy_indicators = self._detect_hierarchy_indicators(posts)
        
        high_risk_authors = [
            author for author, data in author_patterns.items() 
            if data['avg_recruitment_score'] > 20
        ]
        
        report = {
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'total_posts_analyzed': len(posts),
            'unique_authors_found': len(author_patterns),
            'btc_reuse_analysis': {
                'reused_addresses_count': len(btc_reuse),
                'reused_addresses': btc_reuse
            },
            'author_analysis': {
                'total_authors': len(author_patterns),
                'high_risk_authors_count': len(high_risk_authors),
                'author_details': author_patterns
            },
            'hierarchy_analysis': {
                'indicators_found': len(hierarchy_indicators),
                'indicators': hierarchy_indicators
            },
            'risk_assessment': {}
        }
        
        overall_risk, key_findings = self._generate_risk_assessment(btc_reuse, author_patterns, hierarchy_indicators)
        report['risk_assessment']['overall_risk_level'] = overall_risk
        report['risk_assessment']['key_findings'] = key_findings
        
        return report

    def _analyze_author_patterns(self, posts: list) -> dict:
        """Analyzes patterns in author behavior for recruitment indicators."""
        author_analysis = defaultdict(lambda: {
            'post_ids': [], 'affiliate_mentions': 0, 'payment_mentions': 0,
            'btc_addresses': set(), 'total_posts': 0, 'recruitment_score': 0
        })

        for post in posts:
            author = post.get('author', 'Unknown')
            content = f"{post.get('title', '')} {post.get('description', '')}".lower()
            
            aff_mentions = sum(1 for kw in self.affiliate_keywords if kw in content)
            pay_mentions = sum(1 for kw in self.payment_keywords if kw in content)
            btc_addrs = self.btc_pattern.findall(content)

            author_data = author_analysis[author]
            author_data['post_ids'].append(post.get('id', 'unknown'))
            author_data['affiliate_mentions'] += aff_mentions
            author_data['payment_mentions'] += pay_mentions
            author_data['btc_addresses'].update(btc_addrs)
            author_data['total_posts'] += 1
            author_data['recruitment_score'] += (aff_mentions * 10) + (pay_mentions * 8) + (len(btc_addrs) * 5)
        
        # Finalize data for serialization
        for author, data in author_analysis.items():
            data['btc_addresses'] = sorted(list(data['btc_addresses']))
            data['avg_recruitment_score'] = round(data['recruitment_score'] / data['total_posts'], 2) if data['total_posts'] > 0 else 0
        
        return dict(author_analysis)

    def _analyze_btc_reuse(self, posts: list) -> dict:
        """Analyzes BTC address reuse patterns across posts."""
        btc_usage = defaultdict(list)
        for post in posts:
            content = f"{post.get('title', '')} {post.get('description', '')}"
            for btc in self.btc_pattern.findall(content):
                btc_usage[btc].append({'post_id': post.get('id'), 'author': post.get('author')})

        reused = {
            btc: {'usage_count': len(uses), 'authors': sorted(list(set(u['author'] for u in uses)))}
            for btc, uses in btc_usage.items() if len(uses) > 1
        }
        return reused

    def _detect_hierarchy_indicators(self, posts: list) -> list:
        """Detects indicators of hierarchical structures in posts."""
        indicators = []
        for post in posts:
            content = f"{post.get('title', '')} {post.get('description', '')}".lower()
            matches = [kw for kw in self.hierarchy_keywords if kw in content]
            if matches:
                indicators.append({
                    'post_id': post.get('id'), 'author': post.get('author'),
                    'hierarchy_terms': matches,
                    'content_snippet': content[:150] + ('...' if len(content) > 150 else '')
                })
        return indicators

    def _generate_risk_assessment(self, btc_reuse, author_patterns, hierarchy_indicators):
        """Calculates an overall risk level and generates key findings."""
        risk_score = 0
        findings = []

        if btc_reuse:
            risk_score += len(btc_reuse) * 15
            findings.append(f"Found {len(btc_reuse)} BTC addresses reused across multiple posts/authors, suggesting a centralized payment system.")
        
        high_risk_authors = [author for author, data in author_patterns.items() if data['avg_recruitment_score'] > 20]
        if high_risk_authors:
            risk_score += len(high_risk_authors) * 25
            findings.append(f"Identified {len(high_risk_authors)} high-risk authors with strong recruitment indicators: {', '.join(high_risk_authors)}.")
        
        if hierarchy_indicators:
            risk_score += len(hierarchy_indicators) * 10
            findings.append(f"Detected {len(hierarchy_indicators)} posts with terms suggesting a hierarchical structure (e.g., manager, admin).")

        if not findings:
            findings.append("No significant affiliate recruitment patterns were detected.")

        if risk_score >= 100: level = "CRITICAL"
        elif risk_score >= 50: level = "HIGH"
        elif risk_score >= 20: level = "MEDIUM"
        else: level = "LOW"
            
        return level, findings

def save_results(data: dict):
    """Saves the analysis report to a JSON file."""
    if not data or not data.get('behavioral_profiles'):
        logger.warning("No analysis was generated, nothing to save.")
        return
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_15_affiliate_analysis.json')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

def main():
    """Main execution function for the affiliate analyzer."""
    logger.info("🚀 Starting Feature 15: Affiliate Recruitment/Payment Analysis...")
    
    # In a pipeline, this would read from a previous step's output file.
    INPUT_FILE = "sample_posts.json"
    if not os.path.exists(INPUT_FILE):
        logger.warning(f"'{INPUT_FILE}' not found. Creating a dummy file for testing.")
        dummy_posts = [
            {'id': 'post_001', 'author': 'RaaS_Admin', 'title': 'Join our affiliate team!', 'description': 'Earn 70% commission on all ransomware payments. We are a big group looking to expand. Contact us. Payouts via BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', 'timestamp': '2024-01-15T10:30:00Z'},
            {'id': 'post_002', 'author': 'MalwareKing', 'title': 'Hiring skilled partners', 'description': 'Looking for members to join our network. Good profit share. Same BTC address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', 'timestamp': '2024-01-16T14:20:00Z'},
            {'id': 'post_003', 'author': 'NormalVendor', 'title': 'Selling data', 'description': 'Simple sale, no partners.', 'timestamp': '2024-01-19T11:30:00Z'}
        ]
        with open(INPUT_FILE, 'w') as f:
            json.dump(dummy_posts, f, indent=2)
    
    try:
        with open(INPUT_FILE, 'r') as f:
            posts_data = json.load(f)
        
        analyzer = AffiliateAnalyzer()
        report = analyzer.analyze_posts(posts_data)
        
        if report:
            save_results(report)
            print("\n--- Affiliate Analysis Summary ---")
            summary = report.get('risk_assessment', {})
            print(f"Overall Risk Level: {summary.get('overall_risk_level')}")
            for finding in summary.get('key_findings', []):
                print(f"  - {finding}")
            print("----------------------------------")

    except Exception as e:
        logger.critical(f"A critical error occurred: {e}")

    logger.info("✅ Affiliate analysis completed.")

if __name__ == "__main__":
    main()
