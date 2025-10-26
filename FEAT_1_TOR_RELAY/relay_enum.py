#!/usr/bin/env python3
"""
Feature 1: Tor Relay Enumeration
Connects to the local Tor Control Port to fetch and list active Tor relays,
then saves the output to a JSON file.
"""

import sys
import os
import json
from datetime import datetime
from stem.control import Controller

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import get_tor_password, TOR_CONTROL_PORT
except ImportError:
    # Fallback if config.py is not found
    def get_tor_password():
        return "your_tor_password"
    TOR_CONTROL_PORT = 9051

def fetch_tor_relays():
    """
    Connects to the Tor controller, fetches network statuses, and returns relay data.
    """
    print("🚀 Starting Feature 1: Tor Relay Enumeration...")
    output_data = []
    
    try:
        print(f"🔌 Connecting to Tor controller on port {TOR_CONTROL_PORT}...")
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            print("🔐 Authenticating with Tor controller...")
            controller.authenticate(password=get_tor_password())
            
            print("🌐 Getting network statuses...")
            relays = list(controller.get_network_statuses())
            print(f"✅ Found {len(relays)} relays.")
            
            # Process all relays
            for relay in relays:
                relay_data = {
                    "fingerprint": relay.fingerprint,
                    "nickname": relay.nickname,
                    "address": relay.address,
                    "flags": list(relay.flags),
                    "bandwidth": relay.bandwidth,
                    "version": relay.version,
                }
                output_data.append(relay_data)
            
            print(f"👍 Processed {len(output_data)} relays.")
            return output_data

    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Tor controller: {e}")
        print("    Please ensure Tor is running and the ControlPort is configured correctly.")
        return None

def save_results(data: list):
    """
    Saves the extracted relay data to a JSON file in the 'output' directory.
    """
    if not data:
        print("No data to save.")
        return
        
    try:
        # Define the output path relative to the project root
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'feature_1_tor_relays.json')
        
        # Create the final payload with metadata
        final_payload = {
            "feature_name": "Tor Relay Enumeration",
            "execution_timestamp": datetime.now().isoformat(),
            "relay_count": len(data),
            "relays": data
        }

        with open(output_file, 'w') as f:
            json.dump(final_payload, f, indent=4)
        
        print(f"💾 Results successfully saved to: {output_file}")

    except Exception as e:
        print(f"❌ ERROR: Failed to save results to file: {e}")

if __name__ == "__main__":
    relay_data = fetch_tor_relays()
    if relay_data is not None:
        save_results(relay_data)
        print("✅ Tor Relay Enumeration finished successfully.")
    else:
        print("❌ Tor Relay Enumeration failed.")

