#!/bin/bash

echo "🚀 Starting Dark Web OSINT Platform Setup..."

# 1. Check for Python
if ! command -v python3 &> /dev/null
then
    echo "❌ Python3 could not be found."
    exit
fi

# 2. Create Virtual Environment
echo "📦 Creating Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install Python Dependencies
echo "⬇️  Installing Dependencies..."
pip install -r requirements.txt

# 4. Download NLP Models
echo "🧠 Downloading NLP Models (spaCy & TextBlob)..."
python3 -m spacy download en_core_web_sm
python3 -m textblob.download_corpora

# 5. Create Data Directories
echo "📂 Creating Data Directory Structure..."
mkdir -p data/raw
mkdir -p data/normalized
mkdir -p data/enriched
mkdir -p data/intelligence
mkdir -p logs

echo "✅ Setup Complete!"
echo "------------------------------------------------"
echo "👉 To run the Dashboard: python3 web/app.py"
echo "👉 To run the CLI:       python3 orchestration/run_pipeline.py"
echo "------------------------------------------------"
