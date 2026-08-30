#!/bin/bash
# MDRN Corp Release Packager - Da Bklyn Bridge

set -e

echo "[*] Initializing MDRN Corp Release Workflow..."

# 1. Build Frontend
echo "[*] Building React frontend..."
npm install
npm run build

# 2. Prepare Release Directory
VERSION="${1:-1.0.0}"
RELEASE_DIR="da-bklyn-bridge-v${VERSION}"
echo "[*] Staging files for v${VERSION}..."
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# Copy Python Backend
rsync -a \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='*.db' \
  --exclude='*.sqlite' \
  --exclude='*.sqlite3' \
  --exclude='*.pcap' \
  --exclude='*.pcapng' \
  --exclude='*.log' \
  --exclude='models/' \
  --exclude='report_bundle/' \
  python_tool "$RELEASE_DIR/"

# Copy Frontend Assets (Built)
mkdir -p "$RELEASE_DIR/dist"
cp -r dist/* "$RELEASE_DIR/dist/"

# Copy Core Docs
cp README.md "$RELEASE_DIR/"
cp START_HERE.md "$RELEASE_DIR/"
cp BUILD.md "$RELEASE_DIR/"
cp APPLE_SILICON_SETUP_GUIDE.md "$RELEASE_DIR/"
cp LICENSE "$RELEASE_DIR/" 2>/dev/null || echo "[!] WARNING: LICENSE file missing."
cp -r docs "$RELEASE_DIR/" 2>/dev/null || true
cp -r scripts "$RELEASE_DIR/" 2>/dev/null || true
find "$RELEASE_DIR" -type f | sort > "$RELEASE_DIR/release_manifest.txt"

# 3. Create Archive
echo "[*] Creating release archive..."
tar -czf "$RELEASE_DIR.tar.gz" "$RELEASE_DIR"

echo "[+] Release package created: $RELEASE_DIR.tar.gz"
echo "[+] Build complete. Ready for GitHub Release v${VERSION}."
