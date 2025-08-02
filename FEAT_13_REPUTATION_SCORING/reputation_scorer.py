import json

def calculate_reputation(vendor_data):
    """Calculates a reputation score based on vendor feedback and transaction data"""
    # Example: Base score
    score = 0
    
    # Add points for positive feedback
    score += vendor_data.get('positive_feedback', 0) * 2
    
    # Deduct points for negative feedback
    score -= vendor_data.get('negative_feedback', 0) * 5
    
    # Increase score for repeated BTC transactions
    repeated_btc = vendor_data.get('repeated_btc', 0)
    score += min(repeated_btc, 10) * 3  # Cap at 10 for simplicity
    
    # Additional logic can be implemented for more factors
    
    return score


def process_vendor_data(input_file, output_file):
    """Processes vendor data and calculates reputation score"""
    try:
        with open(input_file, 'r') as file:
            vendors = json.load(file)
        
        results = []
        for vendor in vendors:
            reputation_score = calculate_reputation(vendor)
            vendor['reputation_score'] = reputation_score
            results.append(vendor)
        
        with open(output_file, 'w') as file:
            json.dump(results, file, indent=4)
        
        print(f"🎉 Reputation scores calculated and saved to {output_file}")
        
    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found")
    except json.JSONDecodeError:
        print(f"❌ Error: Failed to decode JSON from {input_file}")


def main():
    input_file = 'vendor_data.json'
    output_file = 'vendor_reputation_scores.json'
    process_vendor_data(input_file, output_file)


if __name__ == "__main__":
    main()

