# Feature 12: Behavioral Analysis

## Overview

This feature analyzes vendor behavior patterns from marketplace data to identify threats, track patterns, and score risk levels. It processes data from previous features in the pipeline to build comprehensive behavioral profiles.

## What It Does

### Core Analysis Functions:
- **Posting Pattern Analysis**: Frequency, timing, and marketplace presence
- **Sentiment Analysis**: Emotional tone and confidence indicators using TextBlob
- **Risk Profiling**: Keyword-based threat scoring with multiple risk categories
- **Price Evolution**: Tracks pricing trends and changes over time
- **Threat Level Assessment**: Overall threat scoring based on multiple factors

### Risk Categories:
- **High Risk**: Ransomware, exploits, 0-day, government/military content
- **Medium Risk**: CVV dumps, carding, fraud, stolen data
- **Recruitment**: Affiliate programs, RaaS recruitment
- **Trust Building**: Reputation indicators, escrow usage

## Input Data Format

The script expects mock data in JSON format representing outputs from previous features:

```json
{
  "marketplace_data": [...],
  "previous_behavioral_data": {...},
  "geolocation_data": {...},
  "handle_correlation": {...}
}
```

## Output

Generates comprehensive behavioral profiles including:
- Risk scores (0-100+)
- Threat levels (LOW/MEDIUM/HIGH/CRITICAL)
- Sentiment analysis scores
- Posting pattern metrics
- Price trend analysis

## Usage

```bash
# Activate virtual environment
source ../venv/bin/activate

# Run analysis on mock data
python3 behavioral_analysis.py
```

## Dependencies

- `requests>=2.31.0` - HTTP requests for webhook integration
- `textblob>=0.17.1` - Natural language processing and sentiment analysis
- `python-dotenv>=1.0.0` - Environment variable management

## Configuration

- **Webhook URL**: Configured via `config.py` using n8n account settings
- **Risk Keywords**: Defined in `BehavioralAnalyzer.__init__()`
- **Timeout Settings**: 15-second timeout for webhook requests

## Integration

- **Input**: Mock data representing combined pipeline outputs
- **Output**: Sends results to n8n webhook endpoint: `behavioral-analysis`
- **Error Handling**: Comprehensive exception handling for network issues

## Example Results

```
🔸 VENDOR: ZeroDay_Hunter
   Overall Threat Level: CRITICAL
   Risk Score: 38
   Risk Level: CRITICAL
   Total Posts: 1
   Marketplaces: 1
   Avg Sentiment: -0.11
   Risk Factors: 0day, military, government, exploit
```

## Notes

- Script will function even if n8n webhook is not set up yet
- Comprehensive error messages help identify configuration issues
- Mock data includes realistic vendor behaviors for testing
- Results are JSON-serializable for webhook transmission
