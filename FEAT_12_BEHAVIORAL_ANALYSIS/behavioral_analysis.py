#!/usr/bin/env python3
"""
FEATURE 12: BEHAVIORAL ANALYSIS (Local Version)

Analyzes vendor behavior patterns from marketplace data, including posting frequency,
sentiment, risk keywords, and price evolution. Saves a detailed report locally.
"""

import json
import re
from datetime import datetime
from collections import Counter, defaultdict
from textblob import TextBlob
import os
import sys
import logging

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'behavioral_analysis.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BehavioralAnalyzer:
    def __init__(self):
        self.risk_keywords = {
            'high_risk': ['ransomware', 'exploit', '0day', 'botnet', 'c2', 'breach'],
            'medium_risk': ['cvv', 'carding', 'fraud', 'stolen', 'cracked', 'dumps'],
            'recruitment': ['affiliate', 'partner', 'recruit', 'join us', 'team', 'raas'],
            'trust_building': ['trust', 'reliable', 'reputation', 'feedback', 'escrow']
        }

    def _analyze_posting_patterns(self, vendor_posts):
        """Analyzes posting frequency, timing, and marketplace spread."""
        posts = sorted([datetime.fromisoformat(p['timestamp'].replace('Z', '')) for p in vendor_posts])
        time_diffs_hours = [(posts[i] - posts[i-1]).total_seconds() / 3600 for i in range(1, len(posts))]
        
        return {
            'total_posts': len(posts),
            'marketplaces': list(set(p['marketplace'] for p in vendor_posts)),
            'first_post': posts[0].isoformat() if posts else None,
            'latest_post': posts[-1].isoformat() if posts else None,
            'avg_hours_between_posts': round(sum(time_diffs_hours) / len(time_diffs_hours), 2) if time_diffs_hours else 0,
            'most_active_hour': Counter(p.hour for p in posts).most_common(1)[0][0] if posts else None,
            'most_active_day': Counter(p.weekday() for p in posts).most_common(1)[0][0] if posts else None # Monday=0
        }

    def _analyze_sentiment(self, vendor_posts):
        """Analyzes sentiment and keyword indicators from post content."""
        sentiments = [TextBlob(p['post_content']).sentiment for p in vendor_posts]
        confidence_words = ['trust', 'reliable', 'guarantee', 'experience', 'reputation']
        urgency_words = ['limited', 'fast', 'quick', 'urgent', 'now', 'today']
        
        all_content = " ".join(p['post_content'] for p in vendor_posts).lower()

        return {
            'avg_polarity': round(sum(s.polarity for s in sentiments) / len(sentiments), 3) if sentiments else 0,
            'avg_subjectivity': round(sum(s.subjectivity for s in sentiments) / len(sentiments), 3) if sentiments else 0,
            'confidence_indicators': sum(word in all_content for word in confidence_words),
            'urgency_indicators': sum(word in all_content for word in urgency_words)
        }

    def _analyze_risk_profile(self, vendor_posts):
        """Calculates a risk score based on keywords in post content."""
        profile = {
            'risk_score': 0,
            'risk_factors': set(),
            'category_scores': Counter()
        }
        all_content = " ".join(p['post_content'] for p in vendor_posts).lower()
        
        for category, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword in all_content:
                    profile['category_scores'][category] += 1
                    profile['risk_factors'].add(keyword)
        
        score = (
            profile['category_scores']['high_risk'] * 10 +
            profile['category_scores']['medium_risk'] * 5 +
            profile['category_scores']['recruitment'] * 3 -
            profile['category_scores']['trust_building'] * 2
        )
        profile['risk_score'] = max(0, score)
        profile['risk_factors'] = sorted(list(profile['risk_factors']))
        profile['risk_level'] = self._categorize_risk(profile['risk_score'])
        return profile

    def _categorize_risk(self, score):
        if score >= 20: return 'CRITICAL'
        if score >= 10: return 'HIGH'
        if score >= 5: return 'MEDIUM'
        return 'LOW'

    def generate_report(self, data: dict) -> dict:
        """Generates a comprehensive behavioral analysis report for all vendors."""
        marketplace_data = data.get('marketplace_data', [])
        if not marketplace_data:
            logger.warning("Input data contains no 'marketplace_data'. Cannot generate report.")
            return {}
            
        # Group posts by vendor
        vendor_data = defaultdict(list)
        for entry in marketplace_data:
            vendor_data[entry['vendor_handle']].append(entry)

        report = {'behavioral_profiles': {}}
        for vendor, posts in vendor_data.items():
            patterns = self._analyze_posting_patterns(posts)
            sentiment = self._analyze_sentiment(posts)
            risk = self._analyze_risk_profile(posts)
            
            # Combine all analyses to calculate an overall threat level
            threat_score = risk.get('risk_score', 0)
            if sentiment.get('avg_polarity', 0) < -0.2: threat_score += 5
            if patterns.get('avg_hours_between_posts', 999) < 24: threat_score += 3
            if len(patterns.get('marketplaces', [])) > 1: threat_score += 5
            
            report['behavioral_profiles'][vendor] = {
                'posting_patterns': patterns,
                'sentiment_analysis': sentiment,
                'risk_profile': risk,
                'overall_threat_level': self._categorize_risk(threat_score)
            }
        
        report['analysis_timestamp'] = datetime.now().isoformat()
        report['vendors_analyzed'] = len(vendor_data)
        return report

def save_results(data: dict):
    """Saves the final report to a JSON file."""
    if not data or not data.get('behavioral_profiles'):
        logger.warning("No behavioral profiles generated, nothing to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_12_behavioral_analysis.json')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

def main():
    logger.info("🚀 Starting Feature 12: Behavioral Analysis...")
    
    # In a pipeline, this would read from a previous step's output file.
    # For now, we create a dummy input file.
    INPUT_FILE = "mock_behavioral_input_data.json"
    if not os.path.exists(INPUT_FILE):
        logger.warning(f"'{INPUT_FILE}' not found. Creating a dummy file for testing.")
        dummy_data = {
            "marketplace_data": [
                {"vendor_handle": "CyberCriminal", "marketplace": "AlphaBay", "post_content": "Selling new 0day exploit for Windows.", "price": "$5000", "timestamp": "2025-08-01T10:00:00Z"},
                {"vendor_handle": "CarderKing", "marketplace": "Dread", "post_content": "Fresh CVV dumps available. Best quality, guaranteed.", "price": "$50", "timestamp": "2025-08-01T11:00:00Z"},
                {"vendor_handle": "CyberCriminal", "marketplace": "Dread", "post_content": "Join our RaaS affiliate team for high profit.", "price": "N/A", "timestamp": "2025-08-01T18:00:00Z"}
            ],
            "previous_behavioral_data": {} # For price evolution, not implemented in this version
        }
        with open(INPUT_FILE, 'w') as f:
            json.dump(dummy_data, f, indent=2)

    try:
        with open(INPUT_FILE, 'r') as f:
            input_data = json.load(f)
        
        analyzer = BehavioralAnalyzer()
        report = analyzer.generate_report(input_data)
        
        if report:
            save_results(report)
            print("\n--- Behavioral Analysis Summary ---")
            for vendor, profile in report['behavioral_profiles'].items():
                print(f"Vendor: {vendor}, Threat Level: {profile['overall_threat_level']}")
            print("---------------------------------")
        
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}")

    logger.info("✅ Behavioral analysis completed.")

if __name__ == "__main__":
    main()
