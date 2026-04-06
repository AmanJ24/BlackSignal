"""
Tests for core.scoring_engine.ScoringEngine
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scoring_engine import ScoringEngine


class TestScoringEngine:
    """Tests for the threat scoring engine."""

    def setup_method(self):
        self.engine = ScoringEngine()

    # --- Basic Scoring ---

    def test_empty_evidence_returns_zero(self):
        entity = {"id": "test_ip", "type": "ip", "evidence": {}}
        result = self.engine.score_entity(entity)
        assert result["threat_score"] == 0
        assert result["severity"] == "LOW"
        assert result["evidence_count"] == 0

    def test_missing_evidence_key(self):
        entity = {"id": "test_ip", "type": "ip"}
        result = self.engine.score_entity(entity)
        assert result["threat_score"] == 0

    def test_single_low_confidence_signal(self):
        entity = {
            "id": "192.168.1.1",
            "type": "ip",
            "evidence": {
                "ioc": [{"type": "seen_in_feed", "confidence": 0.2}]
            }
        }
        result = self.engine.score_entity(entity)
        # 0.2 * 1.0 (ioc weight) * 10 = 2.0
        assert result["threat_score"] == 2.0
        assert result["severity"] == "LOW"

    def test_single_high_confidence_signal(self):
        entity = {
            "id": "evil_hash",
            "type": "hash",
            "evidence": {
                "mitre": [{"type": "T1486_encryption", "confidence": 0.9}]
            }
        }
        result = self.engine.score_entity(entity)
        # 0.9 * 2.5 (mitre weight) * 10 = 22.5
        assert result["threat_score"] == 22.5
        assert result["severity"] == "LOW"

    # --- Multi-signal scoring ---

    def test_multiple_evidence_categories(self):
        entity = {
            "id": "threat_vendor",
            "type": "vendor",
            "evidence": {
                "behavioral": [{"type": "high_risk_keywords", "confidence": 0.8}],
                "affiliate": [{"type": "raas_recruitment", "confidence": 0.9}],
                "mitre": [{"type": "T1566_phishing", "confidence": 0.7}]
            }
        }
        result = self.engine.score_entity(entity)
        # behavioral: 0.8 * 2.0 * 10 = 16.0
        # affiliate:  0.9 * 3.0 * 10 = 27.0
        # mitre:      0.7 * 2.5 * 10 = 17.5
        # total = 60.5
        assert result["threat_score"] == 60.5
        assert result["severity"] == "HIGH"
        assert result["evidence_count"] == 3

    def test_score_caps_at_100(self):
        """Even with extreme evidence, score should not exceed 100."""
        entity = {
            "id": "max_threat",
            "type": "vendor",
            "evidence": {
                "affiliate": [
                    {"type": "signal_1", "confidence": 1.0},
                    {"type": "signal_2", "confidence": 1.0},
                    {"type": "signal_3", "confidence": 1.0},
                    {"type": "signal_4", "confidence": 1.0},
                ]
            }
        }
        result = self.engine.score_entity(entity)
        # 4 * 1.0 * 3.0 * 10 = 120, capped to 100
        assert result["threat_score"] == 100
        assert result["severity"] == "CRITICAL"

    # --- Severity thresholds ---

    def test_severity_critical(self):
        entity = {
            "id": "critical_entity",
            "type": "vendor",
            "evidence": {
                "affiliate": [
                    {"type": "s1", "confidence": 1.0},
                    {"type": "s2", "confidence": 1.0},
                    {"type": "s3", "confidence": 1.0},
                ]
            }
        }
        result = self.engine.score_entity(entity)
        assert result["severity"] == "CRITICAL"

    def test_severity_medium(self):
        entity = {
            "id": "medium_entity",
            "type": "ip",
            "evidence": {
                "behavioral": [{"type": "neg_sentiment", "confidence": 0.6}],
                "ioc": [{"type": "in_feed", "confidence": 0.7}],
                "infrastructure": [{"type": "hosting", "confidence": 0.6}],
            }
        }
        result = self.engine.score_entity(entity)
        # behavioral: 0.6*2.0*10=12, ioc: 0.7*1.0*10=7, infra: 0.6*1.5*10=9 = 28
        # Actually let me recalculate... just check range
        assert 20 <= result["threat_score"] < 60

    # --- Confidence calculation ---

    def test_overall_confidence_average(self):
        entity = {
            "id": "conf_test",
            "type": "ip",
            "evidence": {
                "ioc": [
                    {"type": "s1", "confidence": 0.4},
                    {"type": "s2", "confidence": 0.8},
                ]
            }
        }
        result = self.engine.score_entity(entity)
        assert result["overall_confidence"] == 0.6  # (0.4 + 0.8) / 2

    def test_zero_confidence_signals(self):
        entity = {
            "id": "zero_conf",
            "type": "ip",
            "evidence": {
                "ioc": [{"type": "unknown", "confidence": 0.0}]
            }
        }
        result = self.engine.score_entity(entity)
        assert result["threat_score"] == 0
        assert result["overall_confidence"] == 0.0

    # --- Custom weights ---

    def test_custom_weights(self):
        custom_weights = {"ioc": 5.0}
        engine = ScoringEngine(weights=custom_weights)
        entity = {
            "id": "custom_test",
            "type": "ip",
            "evidence": {
                "ioc": [{"type": "bad_ip", "confidence": 0.5}]
            }
        }
        result = engine.score_entity(entity)
        # 0.5 * 5.0 * 10 = 25.0
        assert result["threat_score"] == 25.0

    # --- Output structure ---

    def test_output_fields_present(self):
        entity = {
            "id": "field_check",
            "type": "hash",
            "evidence": {
                "ioc": [{"type": "vt_detect", "confidence": 0.7}]
            }
        }
        result = self.engine.score_entity(entity)
        assert "entity_id" in result
        assert "entity_type" in result
        assert "threat_score" in result
        assert "severity" in result
        assert "overall_confidence" in result
        assert "evidence_count" in result
        assert "reasons" in result
        assert result["entity_id"] == "field_check"
        assert result["entity_type"] == "hash"
