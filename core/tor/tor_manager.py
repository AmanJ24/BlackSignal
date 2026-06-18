import time
import hashlib
import logging
import requests
import socks
from stem.control import Controller
from stem import SocketError, Signal
from stem.connection import AuthenticationFailure

logger = logging.getLogger("TorManager")

class TorManager:
    def __init__(self, control_port, socks_proxy_host, socks_proxy_port, control_password):
        self.control_port = control_port
        self.socks_host = socks_proxy_host
        self.socks_port = socks_proxy_port
        self.socks_addr = f"{socks_proxy_host}:{socks_proxy_port}"
        self.control_password = control_password
        self._controller = None

    def connect(self):
        try:
            self._controller = Controller.from_port(port=self.control_port)
            self._controller.authenticate(password=self.control_password)
            logger.info("✅ Connected and authenticated to Tor Controller.")
        except (SocketError, AuthenticationFailure) as e:
            logger.critical(f"❌ Failed to connect to Tor Control Port: {e}")
            raise RuntimeError("Tor Controller unreachable.")

    def ensure_alive(self):
        # 1. Connect if missing
        if self._controller is None:
            self.connect()
            
        # 2. Safety check: If connect() failed, raise error
        if self._controller is None:
            raise RuntimeError("Tor Controller is None after connection attempt.")

        # 3. Check liveness (Now safe because we know it's not None)
        try:
            if not self._controller.is_alive():
                self.connect()
        except Exception:
            raise RuntimeError("Tor controller not alive.")

    def session(self, purpose):
        isolation_token = hashlib.sha256(purpose.encode()).hexdigest()[:16]
        session = requests.Session()
        proxies = {
            "http": f"socks5h://{isolation_token}:x@{self.socks_addr}",
            "https": f"socks5h://{isolation_token}:x@{self.socks_addr}"
        }
        session.proxies.update(proxies)
        return session

    def new_circuit(self):
        """Request a new Tor circuit (NEWNYM). Throttled to max once per 10s by Tor."""
        self.ensure_alive()
        try:
            self._controller.signal(Signal.NEWNYM)
            logger.info("🔄 Requested new Tor circuit (NEWNYM).")
            time.sleep(1)  # Allow circuit establishment
        except Exception as e:
            logger.error(f"⚠️  Circuit renewal failed: {e}")

    def disconnect(self):
        """Cleanly close the Tor controller connection."""
        if self._controller is not None:
            try:
                self._controller.close()
                logger.info("🔌 Tor controller disconnected.")
            except Exception:
                pass
            self._controller = None

    # Context manager support for clean resource management
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
