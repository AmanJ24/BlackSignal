import os
import sys
import json
import logging
import glob
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import settings as config
except ImportError:
    import config

logger = logging.getLogger("ReputationAnalysis")

class ReputationAnalysis:
    def run(self):
        """
        Correlates entities (IOCs and Handles) with behavioral, MITRE,
        and affiliate evidence parsed from their source scrapers.
        """
        entity_to_sources = {}
        entity_types = {}

        # 1. Map entities to their raw source files
        normalized_path = os.path.join(config.BASE_DIR, "data", "normalized", "*.json")
        for fpath in glob.glob(normalized_path):
            try:
                with open(fpath, 'r') as f:
                    content = json.load(f)
                for item in content.get("data", []):
                    eid = item.get("id")
                    etype = item.get("type", "unknown")
                    source = item.get("source") or item.get("source_file")
                    if eid and source:
                        entity_to_sources.setdefault(eid, set()).add(source)
                        entity_types[eid] = etype
            except Exception as e:
                logger.error(f"❌ Failed to parse normalized file {fpath}: {e}")

        # 2. Gather behavioral/MITRE/affiliate evidence by source file
        source_to_evidence = {}
        intel_path = os.path.join(config.BASE_DIR, "data", "intelligence", "*.json")
        for fpath in glob.glob(intel_path):
            # Skip historical reputation records to avoid self-reinforcement loops
            if "intel_reputation" in fpath:
                continue
            try:
                with open(fpath, 'r') as f:
                    content = json.load(f)
                
                meta = content.get("meta", {})
                source = meta.get("source")
                
                # Fallback to parsing filename if source meta is absent
                if not source:
                    filename = os.path.basename(fpath)
                    parts = filename.split("_")
                    if len(parts) >= 4:
                        source = "_".join(parts[3:])
                
                if not source:
                    continue

                for item in content.get("data", []):
                    item_evidence = item.get("evidence", {})
                    if not item_evidence:
                        continue

                    source_to_evidence.setdefault(source, {})
                    for category, signals in item_evidence.items():
                        if isinstance(signals, list):
                            source_to_evidence[source].setdefault(category, []).extend(signals)
            except Exception as e:
                logger.error(f"❌ Failed to parse intelligence file {fpath}: {e}")

        # 3. Correlate entities with source evidence
        reputation_reports = []
        for eid, sources in entity_to_sources.items():
            merged_evidence = {}
            evidence_count = 0

            for src in sources:
                src_evidence = source_to_evidence.get(src, {})
                for category, signals in src_evidence.items():
                    for signal in signals:
                        # Deduplicate signal types per category for the entity
                        sig_type = signal.get("type")
                        existing = merged_evidence.setdefault(category, [])
                        if not any(x.get("type") == sig_type for x in existing):
                            existing.append(signal)
                            evidence_count += 1

            if evidence_count > 0:
                # Add reputation corroboration if found across multiple sources/signals
                if len(sources) > 1 or evidence_count > 1:
                    merged_evidence.setdefault("behavioral", []).append({
                        "type": "multi_source_corroboration",
                        "description": f"Entity correlated across {len(sources)} sources with {evidence_count} signals.",
                        "confidence": min(0.5 + (0.05 * evidence_count) + (0.1 * len(sources)), 0.95),
                        "source_feature": "reputation_analysis"
                    })

                reputation_reports.append({
                    "id": eid,
                    "type": entity_types[eid],
                    "evidence": merged_evidence
                })

        if reputation_reports:
            self._save(reputation_reports)
        else:
            logger.warning("⚠️ No reputation reports could be generated.")

    def _save(self, data):
        output = {
            "meta": {
                "analysis": "reputation_analysis",
                "timestamp": int(time.time()),
                "count": len(data)
            },
            "data": data
        }
        path = os.path.join(config.BASE_DIR, "data", "intelligence", f"intel_reputation_{int(time.time())}.json")
        with open(path, 'w') as f:
            json.dump(output, f, indent=4)
        logger.info(f"✅ Generated {len(data)} reputation reports -> {path}")

if __name__ == "__main__":
    ReputationAnalysis().run()
