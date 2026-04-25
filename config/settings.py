import os
from pathlib import Path
from dotenv import load_dotenv

# Load secrets from .env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# --- PATHS ---
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs" 

# Alias for Backward Compatibility
OUTPUT_DIR = DATA_DIR

# Ensure data directories exist at startup
for _subdir in ["raw", "normalized", "enriched", "intelligence"]:
    (DATA_DIR / _subdir).mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

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
    "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/" # Example Safe Target
]
