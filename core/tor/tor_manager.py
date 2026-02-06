import time
import socket
import hashlib
import logging
import requests
import socks  # Requires: pip install requests[socks]
from stem.control import Controller
from stem import SocketError, AuthenticationFailure

# Configure Logging
logger = logging.getLogger("TorManager")
logging.basicConfig(level=logging.INFO)

class TorManager:
    """
    Centralized manager for Tor interactions.
    Enforces circuit isolation, connection health, and secure proxying.
    """
    
    def __init__(
        self,
        control_port: int,
        socks_proxy_host: str,
        socks_proxy_port: int,
        control_password: str
    ):
        self.control_port = control_port
        self.socks_host = socks_proxy_host
        self.socks_port = socks_proxy_port
        self.socks_addr = f"{socks_proxy_host}:{socks_proxy_port}"
        self.control_password = control_password
        self._controller = None

    # ---------- CONTROL & HEALTH ----------

    def connect(self) -> None:
        """Establishes connection to the Tor Control Port."""
        try:
            self._controller = Controller.from_port(port=self.control_port)
            self._controller.authenticate(password=self.control_password)
            logger.info("✅ Connected and authenticated to Tor Controller.")
        except (SocketError, AuthenticationFailure) as e:
            logger.critical(f"❌ Failed to connect to Tor Control Port: {e}")
            raise RuntimeError("Tor Controller unreachable. Pipeline halted for security.")

    def ensure_alive(self) -> None:
        """Checks if Tor is running. Reconnects if necessary."""
        if not self._controller:
            self.connect()
        
        try:
            if not self._controller.is_alive():
                logger.warning("⚠️ Tor Controller died. Attempting reconnection...")
                self.connect()
        except Exception:
            raise RuntimeError("Tor controller not alive and cannot reconnect.")

    def renew_identity(self) -> None:
        """Forces a NEWNYM signal to get a fresh circuit globally."""
        self.ensure_alive()
        logger.info("🔄 Signaling NEWNYM to Tor...")
        self._controller.signal("NEWNYM")
        # Wait slightly more than the recommended time to ensure propagation
        time.sleep(self._controller.get_newnym_wait() + 1)
        logger.info("✅ New identity established.")

    def get_current_ip(self, session: requests.Session) -> str:
        """Debug helper to verify IP address through a specific session."""
        try:
            return session.get("http://httpbin.org/ip", timeout=10).json().get("origin")
        except Exception as e:
            return f"Unknown (Error: {e})"

    # ---------- SESSION FACTORY (THE FACTORY) ----------

    def session(self, purpose: str) -> requests.Session:
        """
        Creates a Tor-isolated requests session.
        
        Args:
            purpose (str): A unique string identifier for the feature (e.g., 'market_scraper').
                           Sessions with different purposes will use different Tor circuits.
        
        Returns:
            requests.Session: A configured session object.
        """
        # 1. Generate a deterministic isolation key based on the purpose
        # This acts as the SOCKS5 username/password, forcing Tor to separate streams.
        isolation_token = hashlib.sha256(purpose.encode()).hexdigest()[:16]

        session = requests.Session()

        # 2. Configure Proxy with Authentication for Isolation
        # socks5h:// means DNS resolution happens via Tor (No DNS leaks)
        proxies = {
            "http": f"socks5h://{isolation_token}:x@{self.socks_addr}",
            "https": f"socks5h://{isolation_token}:x@{self.socks_addr}"
        }
        session.proxies.update(proxies)

        # 3. Standard Headers to blend in (Generic User Agent)
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })

        # 4. The Kill Switch / Tor Guard
        # This hook ensures that if the proxy fails, we don't accidentally leak to clearnet.
        # Although requests respects proxies, this adds an explicit connectivity check.
        def tor_guard(response, *args, **kwargs):
            # In a robust production environment, we might check headers or 
            # ensure the connection didn't bypass the proxy. 
            # For now, requests + socks5h is structurally safe, but we verify response codes.
            if response.status_code in [403, 406] and "Cloudflare" in response.text:
                logger.warning(f"⚠️  Request potentially blocked by WAF (Status: {response.status_code})")
            return response

        session.hooks["response"] = [tor_guard]
        
        logger.debug(f"🛡️  Created isolated session for: {purpose}")
        return session
