#!/bin/bash

# Silabs CLI Setup Script for Linux
# This script sets up a Python virtual environment and installs dependencies

set -e  # Exit on any error

echo "🚀 Setting up Silabs CLI environment on Linux..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version (require 3.8+)
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
    echo "✅ Python $PYTHON_VERSION found"
else
    echo "❌ Python $PYTHON_VERSION is too old. Please upgrade to Python 3.8 or higher."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Please run this script from the silabs-cli directory."
    exit 1
fi

if [ ! -f "silabs.py" ]; then
    echo "❌ silabs.py not found. Please run this script from the silabs-cli directory."
    exit 1
fi

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
python -m pip install -r requirements.txt

# Verify installation
echo "✅ Verifying installation..."
python -c "import click, toml, yaml; print('All dependencies installed successfully!')"

# Create activation script for convenience
cat > activate.sh << 'EOF'
#!/bin/bash
# Activation script for Silabs CLI
echo "🔧 Activating Silabs CLI environment..."
source venv/bin/activate
echo "✅ Environment activated. You can now run:"
echo "   python silabs.py --help"
echo "   ./run.sh --help  (with automatic tool path detection)"
echo ""
echo "To use with automatic Silabs tool detection:"
echo "   1. Make sure Silabs tools are installed on your system"
echo "   2. Run: ./run.sh <command>"
echo ""
echo "💡 To deactivate, run: deactivate"
EOF

chmod +x activate.sh

# Test the CLI
echo "🧪 Testing CLI..."
python silabs.py --help | head -5

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To use the Silabs CLI:"
echo "  1. Run: source activate.sh"
echo "  2. Then: python silabs.py --help"
echo ""
echo "Or run directly:"
echo "  source venv/bin/activate && python silabs.py --help"
echo ""
echo "Happy coding! 🚀"