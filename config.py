import os

# --- TOR CONFIGURATION ---
TOR_CONTROL_PORT = int(os.getenv("TOR_CONTROL_PORT", 9051))
TOR_SOCKS_PORT = int(os.getenv("TOR_SOCKS_PORT", 9050))
TOR_SOCKS_HOST = os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
TOR_PASSWORD = os.getenv("TOR_PASSWORD", "TorRelay123") # Change this in production

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# --- SCORING WEIGHTS ---
SCORING_WEIGHTS = {
    "ioc": 1.0,           # Standard technical indicator
    "infrastructure": 1.5, # Server/Hosting/DNS
    "behavioral": 2.0,     # Patterns/TTPs
    "mitre": 2.5,          # Strategic alignment
    "affiliate": 3.0       # Direct financial/human intent
}
