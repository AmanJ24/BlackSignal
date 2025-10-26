#!/usr/bin/env python3
"""
Feature 13: Reputation Scoring (Local Version)

Calculates reputation scores for vendors based on feedback, transaction data,
and history. Reads vendor data from a local file and saves the scored results
to the 'output' directory.
"""

import json
import os
import sys
import logging
from datetime import datetime

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'reputation_scorer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def calculate_reputation(vendor_data: dict) -> dict:
    """
    Calculates a robust reputation score and level based on vendor data.
    Returns a dictionary with the score and explanatory details.
    """
    score = 50  # Start from a neutral baseline
    reasons = []

    positive = vendor_data.get('positive_feedback', 0)
    negative = vendor_data.get('negative_feedback', 0)
    total_feedback = positive + negative

    score -= negative * 5
    if negative > 0:
        reasons.append(f"{-negative * 5} points for {negative} negative feedback")
        
    score += positive * 2
    if positive > 0:
        reasons.append(f"+{positive * 2} points for {positive} positive feedback")

    if total_feedback > 5:  # Only apply ratio bonus/penalty if there's significant feedback
        feedback_ratio = positive / total_feedback
        if feedback_ratio >= 0.98:
            score += 10
            reasons.append("+10 points for excellent feedback ratio (>98%)")
        elif feedback_ratio < 0.85:
            score -= 15
            reasons.append("-15 points for poor feedback ratio (<85%)")

    first_seen_str = vendor_data.get('first_seen')
    if first_seen_str:
        try:
            first_seen_date = datetime.fromisoformat(first_seen_str.replace('Z', ''))
            age_months = (datetime.now() - first_seen_date).days // 30
            age_bonus = min(age_months, 12)  # Cap bonus at 12 months
            if age_bonus > 0:
                score += age_bonus
                reasons.append(f"+{age_bonus} points for vendor age ({age_months} months)")
        except (ValueError, TypeError):
            pass  # Ignore if date format is wrong
            
    final_score = max(0, min(100, int(score)))

    # Determine risk level based on score
    if final_score >= 85:
        level = "Highly Trusted"
    elif final_score >= 65:
        level = "Trusted"
    elif final_score >= 40:
        level = "Neutral"
    elif final_score >= 20:
        level = "Risky"
    else:
        level = "Untrustworthy"

    return {"score": final_score, "level": level, "calculation_factors": reasons}

def process_vendors(input_data: list) -> list:
    """Processes a list of vendor data and calculates reputation for each."""
    results = []
    if not isinstance(input_data, list):
        logger.error("Input data is not a list of vendors.")
        return []

    for vendor in input_data:
        vendor_handle = vendor.get("vendor_handle", "UnknownVendor")
        logger.info(f"Calculating reputation for vendor: {vendor_handle}")
        reputation_details = calculate_reputation(vendor)
        
        # Add the results back to the original vendor dictionary
        vendor['reputation'] = reputation_details
        results.append(vendor)
        
    return results

def save_results(data: list):
    """Saves the reputation scores to a JSON file."""
    if not data:
        logger.warning("No reputation scores to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_13_reputation_scores.json')
        
        final_payload = {
            "feature_name": "Reputation Scoring",
            "execution_timestamp": datetime.now().isoformat(),
            "vendors_processed": len(data),
            "vendor_reputations": data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

def main():
    """Main execution function for the reputation scorer."""
    logger.info("🚀 Starting Feature 13: Reputation Scoring...")
    
    # In a real pipeline, this file would be the output of a previous feature.
    # We create a dummy version for standalone testing.
    INPUT_FILE = "vendor_data.json"
    if not os.path.exists(INPUT_FILE):
        logger.warning(f"'{INPUT_FILE}' not found. Creating a dummy file for testing.")
        dummy_data = [
            {"vendor_handle": "TrustedSeller", "positive_feedback": 250, "negative_feedback": 3, "first_seen": "2023-01-01T12:00:00Z"},
            {"vendor_handle": "NewVendor", "positive_feedback": 5, "negative_feedback": 0, "first_seen": datetime.now().isoformat()},
            {"vendor_handle": "RiskyVendor", "positive_feedback": 50, "negative_feedback": 15, "first_seen": "2024-05-01T12:00:00Z"}
        ]
        with open(INPUT_FILE, 'w') as f:
            json.dump(dummy_data, f, indent=2)
    
    try:
        with open(INPUT_FILE, 'r') as f:
            vendor_data = json.load(f)
        
        scored_vendors = process_vendors(vendor_data)
        
        if scored_vendors:
            save_results(scored_vendors)
            print("\n--- Reputation Scoring Summary ---")
            for vendor in scored_vendors:
                rep = vendor['reputation']
                print(f"  - Vendor: {vendor['vendor_handle']:<15} | Score: {rep['score']:<3} | Level: {rep['level']}")
            print("---------------------------------")
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}")

    logger.info("✅ Reputation scoring complete.")

if __name__ == "__main__":
    main()
