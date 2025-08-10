# Affiliate Recruitment/Payment Analysis

This feature detects RaaS structures by analyzing BTC reuse patterns, affiliate referrals, and promo posts.

## What it does
- Analyze content for BTC reuse, handle repetition, and referral patterns.
- Calculate scores based on author mentions of "affiliate", "partner", etc.
- Detects structures and hierarchies within RaaS operations.

## Input
- Darknet market scraping results (JSON)

## Output
- Analysis of potential affiliation structures
- BTC reuse patterns and scores

## Usage Example
```bash
cd PROJECT_DARK_WEB/FEAT_15_AFFILIATE_ANALYSIS
python3 affiliate_analysis.py
```

## Dependencies
- Python libraries: `json`, `re`
- Custom pattern matching logic
