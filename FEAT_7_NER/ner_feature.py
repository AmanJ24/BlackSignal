#!/usr/bin/env python3
"""
Feature 7: Named Entity Recognition (NER) - Local Version
Extracts named entities (PERSON, ORG, NORP) from text data using spaCy
and saves the results to a local JSON file.
"""

import spacy
import json
import os
import sys
from datetime import datetime
import logging

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'ner_feature.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model 'en_core_web_sm' loaded successfully.")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found.")
    logger.info("Please run: python -m spacy download en_core_web_sm")
    sys.exit(1)

def extract_entities(text: str) -> list:
    """Extracts key named entities (PERSON, ORG, NORP) from text."""
    if not text:
        return []
    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "NORP"]]

def process_text_entry(entry: dict) -> dict:
    """Processes a single text entry and returns a structured NER result."""
    text_content = entry.get("data", "")
    entities = extract_entities(text_content)
    
    # Create structured output
    result = {
        "source": entry.get("source", "unknown_source"),
        "source_timestamp": entry.get("timestamp", "unknown_timestamp"),
        "feature": "Named Entity Recognition (NER)",
        "analysis_timestamp": datetime.now().isoformat(),
        "input_text_snippet": text_content[:250] + "..." if len(text_content) > 250 else text_content,
        "entities_found": len(entities),
        "entities": {
            "PERSON": sorted(list(set([ent[0] for ent in entities if ent[1] == "PERSON"]))),
            "ORG": sorted(list(set([ent[0] for ent in entities if ent[1] == "ORG"]))),
            "NORP": sorted(list(set([ent[0] for ent in entities if ent[1] == "NORP"])))
        }
    }
    return result

def save_results(data: list):
    """Saves the NER analysis results to a JSON file in the 'output' directory."""
    if not data:
        logger.warning("No NER results to save.")
        return
        
    try:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_7_ner_analysis.json')
        
        final_payload = {
            "feature_name": "Named Entity Recognition (NER)",
            "execution_timestamp": datetime.now().isoformat(),
            "total_entries_analyzed": len(data),
            "analysis_results": data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_payload, f, indent=4, ensure_ascii=False)
            
        logger.info(f"💾 Results successfully saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to save results to file: {e}")

def load_input_data(file_path: str) -> list:
    """Loads input data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logger.info(f"✅ Loaded {len(data)} data entries from {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"❌ Input file not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing JSON from {file_path}: {e}")
        return []

if __name__ == "__main__":
    logger.info("🚀 Starting Feature 7: Named Entity Recognition...")
    
    # In a real pipeline, this input file would be the output of a previous step,
    # like the marketplace scraper.
    # For testing, we create a dummy input file.
    INPUT_FILE = "sample_ner_input_data.json"
    if not os.path.exists(INPUT_FILE):
        logger.warning(f"'{INPUT_FILE}' not found. Creating a dummy file for testing.")
        dummy_data = [
            {
                "source": "MarketplaceScrape",
                "timestamp": "2025-08-01T10:00:00Z",
                "data": "A new exploit for Microsoft Windows was released by the hacker group 'Shadow Brokers'. John Doe, a Russian analyst, confirmed its validity."
            },
            {
                "source": "OnionCrawl",
                "timestamp": "2025-08-01T11:00:00Z",
                "data": "The administrator of the forum, Jane Smith, announced a partnership with the American company 'SecureCorp'."
            }
        ]
        with open(INPUT_FILE, 'w') as f:
            json.dump(dummy_data, f, indent=2)

    # Load data from the input file
    input_data_list = load_input_data(INPUT_FILE)
    
    if input_data_list:
        all_results = []
        for i, entry in enumerate(input_data_list, 1):
            logger.info(f"--- Analyzing entry {i}/{len(input_data_list)} ---")
            result = process_text_entry(entry)
            all_results.append(result)
            print(json.dumps(result, indent=2))
        
        save_results(all_results)
    else:
        logger.error("No data loaded. Exiting.")
        
    logger.info("✅ NER analysis completed.")
