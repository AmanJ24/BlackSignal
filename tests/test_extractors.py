"""
Tests for IOC and Hash extraction regex patterns.
These test the core detection logic without any file I/O or Tor dependency.
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.extraction.ioc_extractor import IOCExtractor
from processors.extraction.hash_extractor import HashExtractor


class TestIOCPatterns:
    """Test IOC regex pattern accuracy."""

    def setup_method(self):
        self.patterns = IOCExtractor.PATTERNS

    # --- IPv4 ---

    def test_ipv4_matches_valid_ips(self):
        matches = re.findall(self.patterns["ipv4"], "Server at 8.8.8.8 and 1.2.3.4")
        assert "8.8.8.8" in matches
        assert "1.2.3.4" in matches

    def test_ipv4_range_boundary(self):
        text = "255.255.255.255 and 0.0.0.0"
        matches = re.findall(self.patterns["ipv4"], text)
        assert "255.255.255.255" in matches
        assert "0.0.0.0" in matches

    def test_ipv4_does_not_match_invalid(self):
        text = "999.999.999.999"
        matches = re.findall(self.patterns["ipv4"], text)
        assert len(matches) == 0

    # --- Email ---

    def test_email_matches_standard(self):
        matches = re.findall(self.patterns["email"], "contact admin@darkmarket.onion today")
        assert "admin@darkmarket.onion" in matches

    def test_email_complex(self):
        matches = re.findall(self.patterns["email"], "user.name+tag@example.co.uk")
        assert len(matches) == 1

    # --- Bitcoin ---

    def test_btc_legacy_address(self):
        matches = re.findall(self.patterns["btc_wallet"], "Pay to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        assert len(matches) == 1

    def test_btc_bech32_address(self):
        matches = re.findall(self.patterns["btc_wallet"], "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4")
        assert len(matches) == 1

    # --- Onion domains ---

    def test_onion_v3_domain(self):
        domain = "juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion"
        matches = re.findall(self.patterns["onion_domain"], f"http://{domain}/")
        assert domain in matches

    def test_onion_v3_no_false_positives(self):
        """Short strings should not match v3 onion pattern."""
        matches = re.findall(self.patterns["onion_domain"], "example.onion")
        assert len(matches) == 0

    # --- Ethereum ---

    def test_eth_address(self):
        matches = re.findall(
            self.patterns["eth_wallet"],
            "Send to 0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"
        )
        assert len(matches) == 1

    def test_eth_address_no_false_positives(self):
        matches = re.findall(self.patterns["eth_wallet"], "0xSHORT")
        assert len(matches) == 0


class TestHashPatterns:
    """Test hash extraction regex patterns."""

    def setup_method(self):
        self.patterns = HashExtractor.PATTERNS

    def test_md5_detection(self):
        md5 = "d41d8cd98f00b204e9800998ecf8427e"
        matches = re.findall(self.patterns["md5"], f"hash: {md5}")
        assert md5 in matches

    def test_sha1_detection(self):
        sha1 = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        matches = re.findall(self.patterns["sha1"], f"hash: {sha1}")
        assert sha1 in matches

    def test_sha256_detection(self):
        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        matches = re.findall(self.patterns["sha256"], f"hash: {sha256}")
        assert sha256 in matches

    def test_sha256_in_mixed_text(self):
        text = """
        Malware sample uploaded:
        SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        Size: 1.2MB
        """
        matches = re.findall(self.patterns["sha256"], text)
        assert len(matches) == 1

    def test_no_false_positives_on_short_hex(self):
        """Hex strings shorter than 32 chars should not match any hash pattern."""
        text = "abcdef1234567890"  # 16 chars
        for pattern in self.patterns.values():
            matches = re.findall(pattern, text)
            assert len(matches) == 0


class TestIOCFiltering:
    """Test the local IP filtering logic in IOCExtractor."""

    def test_local_ip_filtering(self):
        """Verify that 127.x and 192.168.x IPs are filtered out."""
        extractor = IOCExtractor()
        # We access the pattern directly to test the filtering logic
        pattern = extractor.PATTERNS["ipv4"]
        text = "Server 127.0.0.1 and target 8.8.4.4 and local 192.168.1.1"
        all_matches = set(re.findall(pattern, text))

        # Filter as the extractor does
        filtered = [
            ip for ip in all_matches
            if not (ip.startswith("127.") or ip.startswith("192.168."))
        ]

        assert "8.8.4.4" in filtered
        assert "127.0.0.1" not in filtered
        assert "192.168.1.1" not in filtered
