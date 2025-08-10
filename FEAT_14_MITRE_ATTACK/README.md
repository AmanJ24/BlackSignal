# MITRE ATT&CK TTP Mapping

This feature maps observed behaviors and findings to MITRE ATT&CK techniques using keyword matching and pattern recognition.

## What it does
- Links behavior and findings to MITRE ATT&CK techniques
- Uses keyword matching logic against threat descriptions
- Maps activities to specific TTP (Tactics, Techniques, and Procedures)
- Provides structured output for threat attribution

## Input
- Threat description text (JSON)
- Observed behaviors and indicators

## Output
- Mapped MITRE ATT&CK techniques with confidence scores
- TTP classification and attribution data

## Usage Example
```bash
cd PROJECT_DARK_WEB/FEAT_14_MITRE_ATTACK
python3 mitre_mapper.py
```

## Dependencies
- Python libraries: `json`, `re`, `requests`
- MITRE ATT&CK dataset (locally stored)
- Pattern matching algorithms
