#!/bin/bash

echo "🚀 Setting up Expense Settlement App for macOS..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher first."
    echo "   You can download it from: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Make launcher script executable
echo "🔐 Making launcher script executable..."
chmod +x run_app.sh

echo ""
echo "✅ Setup complete! You can now run the app using:"
echo "   ./run_app.sh"
echo ""
echo "   Or manually with:"
echo "   source venv/bin/activate"
echo "   streamlit run app.py"
echo "" 