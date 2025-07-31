import spacy
import json
from datetime import datetime

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    """Extract named entities from text using spaCy NLP"""
    # Process whole documents with spaCy
    doc = nlp(text)
    # Find named entities, phrases, and concepts
    named_entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "NORP"]]
    return named_entities

def process_text(text):
    """Process input text and extract entities with formatted output"""
    entities = extract_entities(text)
    
    # Create structured output for n8n webhook integration
    result = {
        "timestamp": datetime.now().isoformat(),
        "feature": "Named Entity Recognition (NER)",
        "input_text": text[:200] + "..." if len(text) > 200 else text,
        "entities_found": len(entities),
        "entities": {
            "PERSON": [ent[0] for ent in entities if ent[1] == "PERSON"],
            "ORG": [ent[0] for ent in entities if ent[1] == "ORG"],
            "NORP": [ent[0] for ent in entities if ent[1] == "NORP"]
        },
        "raw_entities": entities
    }
    
    # Print results for testing
    print("\n=== NER FEATURE 7 RESULTS ===")
    print(f"Text analyzed: {result['input_text']}")
    print(f"Total entities found: {result['entities_found']}")
    print("\nExtracted Entities:")
    for entity_type, entities_list in result['entities'].items():
        if entities_list:
            print(f"  {entity_type}: {', '.join(entities_list)}")
    print("\nRaw entities with labels:")
    for entity in entities:
        print(f"  - '{entity[0]}' ({entity[1]})")
    
    return result

def load_sample_data(json_file_path="sample_dark_web_data.json"):
    """Load sample dark web data from JSON file"""
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        print(f"✅ Loaded {len(data)} data entries from {json_file_path}")
        return data
    except FileNotFoundError:
        print(f"❌ Error: {json_file_path} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return []

# Test with dark web marketplace sample data
if __name__ == "__main__":
    # Load data from JSON file
    sample_data_list = load_sample_data()
    
    if not sample_data_list:
        print("No data loaded. Exiting.")
        exit(1)
    
    # Iterate over each extracted data sample
    for i, entry in enumerate(sample_data_list, 1):
        print(f"\n{'='*60}")
        print(f"TESTING SAMPLE {i} from {entry['source']} ({entry.get('timestamp', 'No timestamp')})")
        print(f"{'='*60}")
        result = process_text(entry['data'])
        
        # Add source information to result
        result['source'] = entry['source']
        result['source_timestamp'] = entry.get('timestamp', 'Unknown')
        
        # This result would be sent to n8n webhook in production
        print("\n[Ready for n8n webhook integration]")
        print(json.dumps(result, indent=2))
