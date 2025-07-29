# Project Logs Directory

This directory contains log files from various OSINT automation features.

## Log Files Structure:
- `feature_1_tor_relay.log` - Tor relay enumeration logs
- `feature_2_onion_crawl.log` - Onion domain discovery logs  
- `feature_3_marketplace.log` - Marketplace scraping logs
- `feature_4_api_enrich.log` - API enrichment logs
- `feature_5_stix_taxii.log` - STIX/TAXII feed parsing logs

## Guidelines:
- Log files are automatically rotated when they exceed 10MB
- Logs older than 30 days are automatically archived
- All logs use UTC timestamps for consistency
- Log level: INFO and above for production, DEBUG for development

## Security Note:
These logs may contain sensitive indicators and should be handled according to your organization's data protection policies.
