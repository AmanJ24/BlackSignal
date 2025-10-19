from stem.control import Controller
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_tor_password, TOR_CONTROL_PORT

with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
    controller.authenticate(password=get_tor_password())
    relays = controller.get_network_statuses()
    output = []

    for relay in relays:
        output.append({
            "fingerprint": relay.fingerprint,
            "address": relay.address,
            "nickname": relay.nickname,
            "flags": relay.flags,
        })

    import json
    print(json.dumps(output, indent=2))  # Only first 10 relays for now

