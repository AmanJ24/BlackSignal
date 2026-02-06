from typing import Dict, List, Any
import logging

# Configure Logging
logger = logging.getLogger("ScoringEngine")

class ScoringEngine:
    """
    Calculates threat scores based on normalized evidence.
    Output is a standard 0-100 score with confidence intervals.
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        # Default weights if none provided
        self.weights = weights or {
            "ioc": 1.0,
            "infrastructure": 1.5,
            "behavioral": 2.0,
            "mitre": 2.5,
            "affiliate": 3.0
        }

    def score_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scores a normalized entity (vendor, ip, handle, etc.).
        
        Expected Input Schema:
        {
            "id": "vendor_name",
            "type": "vendor",
            "evidence": {
                "behavioral": [{"type": "high_posting_frequency", "confidence": 0.8}],
                "affiliate": [{"type": "recruitment_keywords", "confidence": 0.9}]
            }
        }
        """

        evidence = entity.get("evidence", {})
        raw_score = 0.0
        reasons = []

        # Iterate through evidence categories (ioc, behavioral, etc.)
        for category, signals in evidence.items():
            weight = self.weights.get(category, 1.0)
            
            for signal in signals:
                confidence = signal.get("confidence", 0.0)
                signal_type = signal.get("type", "unknown_signal")
                
                # Formula: Confidence * Weight
                # A high confidence signal in a high weight category adds more points.
                points = confidence * weight * 10 
                raw_score += points
                
                reasons.append({
                    "category": category,
                    "signal": signal_type,
                    "confidence": confidence,
                    "points_contributed": round(points, 2)
                })

        # Normalize Score to 0-100 Cap
        final_score = min(100, round(raw_score, 2))
        
        # Calculate Severity Level
        if final_score >= 80: severity = "CRITICAL"
        elif final_score >= 60: severity = "HIGH"
        elif final_score >= 40: severity = "MEDIUM"
        else: severity = "LOW"

        return {
            "entity_id": entity.get("id"),
            "entity_type": entity.get("type"),
            "threat_score": final_score,
            "severity": severity,
            "overall_confidence": self._calculate_overall_confidence(reasons),
            "evidence_count": len(reasons),
            "reasons": reasons
        }

    def _calculate_overall_confidence(self, reasons: List[Dict]) -> float:
        """Average confidence of all contributing signals."""
        if not reasons:
            return 0.0
        total_conf = sum(r["confidence"] for r in reasons)
        return round(total_conf / len(reasons), 2)
