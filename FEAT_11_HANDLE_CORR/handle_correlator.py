#!/usr/bin/env python3
"""
Feature 11: Handle Correlation (Local Version)

This module correlates threat actor handles against a local database of known actors
to identify matches and saves the results to a local JSON file.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path for config imports (optional for this script)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'handle_correlation.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HandleCorrelator:
    """Correlates threat actor handles against a known database."""

    def __init__(self, known_handles_path: str = 'known_handles.json'):
        self.known_handles_path = known_handles_path
        self.known_handles = self._load_known_handles()
        logger.info(f"Loaded {len(self.known_handles)} known threat actor handles.")

    def _load_known_handles(self) -> Dict[str, Any]:
        """Loads the known handles database from a JSON file."""
        db_path = os.path.join(os.path.dirname(__file__), self.known_handles_path)
        if not os.path.exists(db_path):
            logger.critical(f"CRITICAL: Handle database '{self.known_handles_path}' not found. This feature cannot run.")
            raise FileNotFoundError(f"'{self.known_handles_path}' is required for handle correlation.")
        try:
            with open(db_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {self.known_handles_path}: {e}")
            return {}


    def correlate_handles(self, handles: List[str]) -> List[Dict]:
        """Correlates a list of handles against the known database."""
        results = []
        for handle in set(handles):  # Use set to process unique handles only
            is_known = handle.lower() in [h.lower() for h in self.known_handles.keys()]
            if is_known:
                # Find the original case for displaying info
                original_case_handle = next((h for h in self.known_handles if h.lower() == handle.lower()), handle)
                results.append({
                    "handle": original_case_handle,
                    "status": "known",
                    "details": self.known_handles.get(original_case_handle)
                })
            else:
                results.append({
                    "handle": handle,
                    "status": "unknown",
                    "details": None
                })
        logger.info(f"Correlated {len(handles)} handles. Found {len([r for r in results if r['status'] == 'known'])} known actors.")
        return results

def save_results(data: List[Dict]):
    """Saves the correlation results to a JSON file."""
    if not data:
        logger.warning("No correlation results to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_11_handle_correlation.json')
        
        final_payload = {
            "feature_name": "Handle Correlation",
            "execution_timestamp": datetime.now().isoformat(),
            "handles_analyzed": len(data),
            "known_handles_found": len([h for h in data if h['status'] == 'known']),
            "correlation_results": data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Feature 11: Handle Correlation...")
    
    # In a real pipeline, this input would come from a file (e.g., IOC or NER output).
    # For standalone testing, we use a sample list.
    sample_handles_to_check = [
        "Gnosticplayers",
        "UnknownVendor123",
        "ShinyHunters",
        "NewUser2025",
        "shinyhunters" # Test case-insensitivity
    ]

    try:
        correlator = HandleCorrelator()
        correlation_results = correlator.correlate_handles(sample_handles_to_check)
        
        if correlation_results:
            print("\n--- Correlation Results ---")
            for result in correlation_results:
                status_icon = "✅" if result['status'] == 'known' else "❓"
                print(f"  {status_icon} Handle: {result['handle']:<20} | Status: {result['status']}")
            print("---------------------------")
            save_results(correlation_results)
        else:
            logger.info("No handles were processed.")
            
    except Exception as e:
        logger.critical(f"A critical error occurred during correlation: {e}")

    logger.info("✅ Handle correlation process completed.")
