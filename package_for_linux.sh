#!/bin/bash

# Package script for exporting Silabs CLI to Linux
# This script creates a tarball with all necessary files

echo "📦 Packaging Silabs CLI for Linux export..."

# Create export directory
EXPORT_DIR="silabs-cli-linux-export"
rm -rf "$EXPORT_DIR"
mkdir "$EXPORT_DIR"

# Copy essential files
mkdir -p "$EXPORT_DIR/silabs"
cp -r silabs/* "$EXPORT_DIR/silabs/"
cp silabs.py "$EXPORT_DIR/"
cp requirements.txt "$EXPORT_DIR/"
cp setup_linux.sh "$EXPORT_DIR/"
cp run.sh "$EXPORT_DIR/"
cp README.md "$EXPORT_DIR/"
cp RUN_SH_GUIDE.md "$EXPORT_DIR/"
cp SILABS_CLI_PLAN.md "$EXPORT_DIR/"

# Make scripts executable
chmod +x "$EXPORT_DIR/setup_linux.sh"
chmod +x "$EXPORT_DIR/run.sh"

# Create tarball
TARBALL="silabs-cli-linux-$(date +%Y%m%d).tar.gz"
tar -czf "$TARBALL" "$EXPORT_DIR"

# Clean up
rm -rf "$EXPORT_DIR"

echo "✅ Package created: $TARBALL"
echo ""
echo "To use on Linux:"
echo "  1. tar -xzf $TARBALL"
echo "  2. cd silabs-cli-linux-export"
echo "  3. ./setup_linux.sh"
echo ""
echo "Happy coding! 🚀"