import sys
import os
import json
import tempfile
import glob
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.reputation_analysis import ReputationAnalysis
import config.settings as config

class TestReputationAnalysis:
    def setup_method(self):
        # Create a mock base dir to redirect data directory read/writes
        self.test_dir = tempfile.mkdtemp()
        self.orig_base_dir = config.BASE_DIR
        config.BASE_DIR = self.test_dir

        # Re-initialize directories
        self.raw_dir = os.path.join(self.test_dir, "data", "raw")
        self.normalized_dir = os.path.join(self.test_dir, "data", "normalized")
        self.enriched_dir = os.path.join(self.test_dir, "data", "enriched")
        self.intelligence_dir = os.path.join(self.test_dir, "data", "intelligence")

        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.normalized_dir, exist_ok=True)
        os.makedirs(self.enriched_dir, exist_ok=True)
        os.makedirs(self.intelligence_dir, exist_ok=True)

    def teardown_method(self):
        # Clean up mock directories
        shutil.rmtree(self.test_dir)
        config.BASE_DIR = self.orig_base_dir

    def test_reputation_correlation(self):
        # 1. Create a mock normalized IOC/entity file
        # Entity "hacker_bob" is extracted from "scrape_post1.json"
        normalized_data = {
            "meta": {"processor": "ner_extractor", "source": "scrape_post1.json", "count": 1},
            "data": [
                {
                    "id": "hacker_bob",
                    "type": "entity",
                    "subtype": "PERSON",
                    "source": "scrape_post1.json"
                }
            ]
        }
        with open(os.path.join(self.normalized_dir, "normalized_entities_1.json"), "w") as f:
            json.dump(normalized_data, f)

        # 2. Create a mock behavioral intelligence file for "scrape_post1.json"
        behavioral_data = {
            "meta": {"feature": "behavioral_analysis", "source": "scrape_post1.json", "timestamp": 12345},
            "data": [
                {
                    "raw_text": "Buy my malware! contact hacker_bob",
                    "evidence": {
                        "behavioral": [
                            {
                                "type": "high_risk_keywords",
                                "description": "Found: ['malware']",
                                "confidence": 0.8,
                                "source_feature": "behavioral_analysis"
                            }
                        ]
                    }
                }
            ]
        }
        with open(os.path.join(self.intelligence_dir, "intel_behavior_1_scrape_post1.json"), "w") as f:
            json.dump(behavioral_data, f)

        # 3. Create a mock mitre mapping file for "scrape_post1.json"
        mitre_data = {
            "meta": {"feature": "mitre_mapping", "source": "scrape_post1.json", "timestamp": 12345},
            "data": [
                {
                    "raw_text": "Buy my malware! contact hacker_bob",
                    "evidence": {
                        "mitre": [
                            {
                                "type": "mitre_technique_match",
                                "description": "Mapped TTPs: ['T1587']",
                                "confidence": 0.7,
                                "source_feature": "mitre_mapping"
                            }
                        ]
                    }
                }
            ]
        }
        with open(os.path.join(self.intelligence_dir, "intel_mitre_1_scrape_post1.json"), "w") as f:
            json.dump(mitre_data, f)

        # 4. Run reputation analysis
        reputation = ReputationAnalysis()
        reputation.run()

        # 5. Assert that reputation file is generated and contains correlated data
        rep_files = glob.glob(os.path.join(self.intelligence_dir, "intel_reputation_*.json"))
        assert len(rep_files) == 1

        with open(rep_files[0], "r") as f:
            result = json.load(f)

        assert result["meta"]["count"] == 1
        entity_report = result["data"][0]

        # Verify correct correlation by entity ID
        assert entity_report["id"] == "hacker_bob"
        assert entity_report["type"] == "entity"

        # Verify evidence categories have been merged
        evidence = entity_report["evidence"]
        assert "behavioral" in evidence
        assert "mitre" in evidence

        # Verify signals are mapped correctly
        behavioral_types = [x["type"] for x in evidence["behavioral"]]
        assert "high_risk_keywords" in behavioral_types
        assert "multi_source_corroboration" in behavioral_types  # Triggered because of multiple signals

        mitre_types = [x["type"] for x in evidence["mitre"]]
        assert "mitre_technique_match" in mitre_types
