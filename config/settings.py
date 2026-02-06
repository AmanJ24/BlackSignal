import os
from dotenv import load_dotenv

# Load secrets from .secrets.env
load_dotenv(".secrets.env")

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# --- TOR SETTINGS ---
TOR_CONTROL_PORT = int(os.getenv("TOR_CONTROL_PORT", 9051))
TOR_SOCKS_PORT = int(os.getenv("TOR_SOCKS_PORT", 9050))
TOR_SOCKS_HOST = os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
TOR_PASSWORD = os.getenv("TOR_PASSWORD", "TorRelay123")

# --- API KEYS ---
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY")
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")

# --- TARGETS (Production would load these from a DB) ---
ONION_SEEDS = [
    "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/", # Ahmia
]

MARKET_TARGETS = [
    "https://duckduckgogg42ts72.onion/" # Example Safe Target
]
