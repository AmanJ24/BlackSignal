"""
Scoring Stage — Final pipeline stage that aggregates enriched data
and runs it through the ScoringEngine to produce scored intelligence.
"""

import os
import json
import glob
import time
import logging

import config.settings as config
from core.scoring_engine import ScoringEngine

logger = logging.getLogger("ScoringStage")


class ScoringStage:
    """
    Reads enriched and intelligence data, normalizes it into scoring-compatible
    entities, and produces final scored threat assessments.
    """

    def __init__(self, weights=None):
        self.engine = ScoringEngine(weights=weights)

    def run(self):
        entities = {}

        # 1. Collect evidence from enriched data
        enriched_files = glob.glob(os.path.join(config.DATA_DIR, "enriched", "*.json"))
        for fpath in enriched_files:
            self._merge_evidence(fpath, entities)

        # 2. Collect evidence from intelligence data
        intel_files = glob.glob(os.path.join(config.DATA_DIR, "intelligence", "*.json"))
        for fpath in intel_files:
            self._merge_evidence(fpath, entities)

        if not entities:
            logger.warning("⚠️  No entities found to score.")
            return

        # 3. Score all entities
        scored_results = []
        for entity_id, entity in entities.items():
            try:
                result = self.engine.score_entity(entity)
                scored_results.append(result)
            except Exception as e:
                logger.error(f"❌ Failed to score entity {entity_id}: {e}")

        # 4. Sort by threat score (highest first) and save
        scored_results.sort(key=lambda x: x["threat_score"], reverse=True)
        self._save(scored_results)

        # 5. Log summary
        critical = sum(1 for r in scored_results if r["severity"] == "CRITICAL")
        high = sum(1 for r in scored_results if r["severity"] == "HIGH")
        logger.info(
            f"🎯 Scored {len(scored_results)} entities — "
            f"🔴 {critical} CRITICAL, 🟠 {high} HIGH"
        )

    def _merge_evidence(self, file_path, entities):
        """
        Reads a data file and merges evidence into the entity accumulator.
        Handles both list-of-items and dict-with-data formats.
        """
        try:
            with open(file_path, 'r') as f:
                content = json.load(f)

            items = content.get("data", [])
            if not isinstance(items, list):
                return

            for item in items:
                if not isinstance(item, dict):
                    continue

                entity_id = item.get("id")
                if not entity_id:
                    continue

                # Initialize entity if new
                if entity_id not in entities:
                    entities[entity_id] = {
                        "id": entity_id,
                        "type": item.get("type", "unknown"),
                        "evidence": {}
                    }

                # Merge evidence categories
                item_evidence = item.get("evidence", {})
                for category, signals in item_evidence.items():
                    if isinstance(signals, list):
                        entities[entity_id]["evidence"].setdefault(category, []).extend(signals)

        except Exception as e:
            logger.error(f"❌ Failed to read {file_path}: {e}")

    def _save(self, scored_results):
        output = {
            "meta": {
                "stage": "scoring",
                "timestamp": int(time.time()),
                "total_scored": len(scored_results),
            },
            "data": scored_results
        }

        filename = f"scored_intelligence_{int(time.time())}.json"
        path = os.path.join(config.DATA_DIR, "intelligence", filename)

        with open(path, 'w') as f:
            json.dump(output, f, indent=4)

        logger.info(f"💾 Saved scored intelligence to {path}")


if __name__ == "__main__":
    ScoringStage().run()
