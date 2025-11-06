#!/bin/bash

# Start script for Dark Web OSINT Web Interface
# Makes launching the dashboard super easy!

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║     🕵️  Dark Web OSINT Automation Dashboard               ║"
echo "║                                                            ║"
echo "║     Starting Professional Minimalist Interface...         ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found!"
    echo "Please run this script from the web_interface directory:"
    echo "  cd web_interface"
    echo "  ./start.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Create necessary directories
mkdir -p ../logs
mkdir -p ../output

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Flask server on http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the Flask app
python app.py
