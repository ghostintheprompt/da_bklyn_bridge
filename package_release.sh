#!/bin/bash
# MDRN Corp Release Packager - Da Bklyn Bridge

set -e

echo "[*] Initializing MDRN Corp Release Workflow..."

# 1. Build Frontend
echo "[*] Building React frontend..."
npm install
npm run build

# 2. Prepare Release Directory
echo "[*] Staging files for v1.0.0..."
RELEASE_DIR="da-bklyn-bridge-v1.0.0"
mkdir -p $RELEASE_DIR

# Copy Python Backend
cp -r python_tool $RELEASE_DIR/
rm -f $RELEASE_DIR/python_tool/*.db # Don't ship local logs
rm -rf $RELEASE_DIR/python_tool/__pycache__

# Copy Frontend Assets (Built)
mkdir -p $RELEASE_DIR/dist
cp -r dist/* $RELEASE_DIR/dist/

# Copy Core Docs
cp README.md $RELEASE_DIR/
cp BUILD.md $RELEASE_DIR/
cp LICENSE $RELEASE_DIR/ 2>/dev/null || echo "[!] WARNING: LICENSE file missing."

# 3. Create Archive
echo "[*] Creating release archive..."
tar -czf $RELEASE_DIR.tar.gz $RELEASE_DIR

echo "[+] Release package created: $RELEASE_DIR.tar.gz"
echo "[+] Build complete. Ready for GitHub Release v1.0.0."
