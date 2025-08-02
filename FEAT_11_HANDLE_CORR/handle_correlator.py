#!/usr/bin/env python3
"""
Feature 11: Handle Correlation

This module correlates threat actor handles across multiple platforms and marketplaces
to identify known actors and track their activities across the dark web ecosystem.

Author: OSINT Pipeline Project
Created: 2025-08-01
"""

import json
import logging
import requests
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

# Add parent directory to path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/handle_correlation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import config, handle if not available
try:
    from config import get_n8n_webhook_url
    CONFIG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Config module not available: {e}. Using fallback configuration.")
    CONFIG_AVAILABLE = False

class HandleCorrelationError(Exception):
    pass

class HandleCorrelator:
    def __init__(self):
        self.known_handles = self.load_known_handles('known_handles.json')
        logger.info(f"Loaded {len(self.known_handles)} known handles.")

    def load_known_handles(self, filepath: str) -> Dict[str, Any]:
        """Load known handles from a JSON file"""
        try:
            with open(filepath, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning(f"File {filepath} not found, starting with an empty list.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {filepath}: {e}")
            return {}

    def compare_handle(self, handle: str) -> Dict[str, str]:
        """Compare handle against known handles"""
        try:
            is_known = handle in self.known_handles
            status = "known" if is_known else "unknown"
            logger.info(f"Handle '{handle}' status: {status}")
            return {"handle": handle, "status": status}
        except Exception as e:
            logger.error(f"Error comparing handle '{handle}': {e}")
            raise HandleCorrelationError(f"Error comparing handle '{handle}': {e}")

    def correlate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Correlate handles with existing data"""
        try:
            results = []
            for entry in data.get('extracted_handles', []):
                handle_info = self.compare_handle(entry['handle'])
                results.append({"handle": entry['handle'], "status": handle_info['status']})
            return {"results": results, "source": data.get('source')}
        except KeyError as e:
            logger.error(f"Key error: {e}")
            raise HandleCorrelationError(f"Key error during correlation: {e}")
        except Exception as e:
            logger.error(f"General error during correlation: {e}")
            raise HandleCorrelationError(f"General error during correlation: {e}")
