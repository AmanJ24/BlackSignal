from flask import Flask, jsonify
from stem.control import Controller
import requests
import json
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_n8n_webhook_url, get_tor_password, TOR_CONTROL_PORT

app = Flask(__name__)

@app.route("/relays", methods=["GET"])
def get_relays():
    print("Starting relay fetch...")
    output = []
    
    try:
        print("Connecting to Tor controller...")
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            print("Authenticating...")
            controller.authenticate(password=get_tor_password())
            print("Getting network statuses...")
            relays = list(controller.get_network_statuses())
            print(f"Found {len(relays)} relays")
            
            for relay in relays[:10]:
                relay_data = {
                    "fingerprint": relay.fingerprint,
                    "address": relay.address,
                    "nickname": relay.nickname,
                    "flags": list(relay.flags),
                }
                output.append(relay_data)
                print(f"Processed relay: {relay.nickname}")

        print(f"Prepared {len(output)} relays for webhook")
        
        # ✅ Push to n8n webhook AFTER output is ready
        webhook_url = get_n8n_webhook_url('tor-relays')
        
        try:
            print(f"Sending to webhook: {webhook_url}")
            headers = {'Content-Type': 'application/json'}
            res = requests.post(webhook_url, json=output, headers=headers, timeout=30)
            print(f"Webhook response - Status: {res.status_code}, Text: {res.text}")
            
            if res.status_code == 200:
                return jsonify({
                    "status": "success", 
                    "message": "Data sent to n8n successfully",
                    "count": len(output),
                    "webhook_response": res.status_code
                })
            else:
                return jsonify({
                    "status": "webhook_error", 
                    "message": f"Webhook returned status {res.status_code}",
                    "count": len(output),
                    "response": res.text
                }), 400
                
        except requests.exceptions.RequestException as e:
            print(f"Error sending to n8n: {str(e)}")
            return jsonify({
                "status": "webhook_failed", 
                "message": f"Failed to send to webhook: {str(e)}",
                "count": len(output),
                "data": output  # Return the data anyway
            }), 500
    
    except Exception as e:
        print(f"Error connecting to Tor controller: {str(e)}")
        return jsonify({
            "error": "Failed to connect to Tor controller", 
            "message": str(e),
            "details": "Make sure Tor is running with ControlPort 9051 enabled"
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

