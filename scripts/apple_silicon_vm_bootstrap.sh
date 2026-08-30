#!/usr/bin/env bash
# Lightweight Linux VM bootstrap for Apple-silicon hosts.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WITH_RTL8812AU=0
WITH_AIRCRACK=0
WITH_ML=0
WITH_EVIDENCE=0

usage() {
  cat <<'USAGE'
Usage: scripts/apple_silicon_vm_bootstrap.sh [options]

Run this inside the ARM Linux VM, not on macOS.

Options:
  --rtl8812au       Install Realtek RTL8812AU/88xxAU DKMS support for AWUS036ACH-class adapters.
  --with-aircrack   Install aircrack-ng tools for monitor fallback and authorized lab work.
  --with-ml         Install optional pandas/scikit-learn anomaly training requirements.
  --with-evidence   Install optional SQLCipher Python binding for encrypted evidence DBs.
  -h, --help        Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rtl8812au) WITH_RTL8812AU=1; shift ;;
    --with-aircrack) WITH_AIRCRACK=1; shift ;;
    --with-ml) WITH_ML=1; shift ;;
    --with-evidence) WITH_EVIDENCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[!] Unknown option: $1"; usage; exit 2 ;;
  esac
done

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "[!] This bootstrap runs inside the ARM Linux VM. On macOS, install UTM and pass the Alfa USB device into the VM."
  exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "[!] This script expects Debian/Kali/Ubuntu-style apt packages."
  exit 1
fi

echo "[*] Installing lean system packages..."
BASE_PACKAGES=(
  python3-venv
  python3-pip
  iw
  iproute2
  usbutils
  wireless-tools
  tcpdump
)

if [[ "$WITH_AIRCRACK" -eq 1 ]]; then
  BASE_PACKAGES+=(aircrack-ng)
fi

sudo apt-get update
sudo apt-get install -y "${BASE_PACKAGES[@]}"

if [[ "$WITH_RTL8812AU" -eq 1 ]]; then
  echo "[*] Installing Realtek 88xxAU DKMS support..."
  sudo apt-get install -y dkms "linux-headers-$(uname -r)" || true
  sudo apt-get install -y realtek-rtl88xxau-dkms || {
    echo "[!] DKMS package install failed. On Kali ARM, confirm apt sources are current."
  }
fi

echo "[*] Creating local Python venv..."
cd "$ROOT_DIR"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r python_tool/requirements.txt

if [[ "$WITH_ML" -eq 1 ]]; then
  python -m pip install -r python_tool/requirements-ml.txt
fi

if [[ "$WITH_EVIDENCE" -eq 1 ]]; then
  python -m pip install -r python_tool/requirements-evidence.txt
fi

echo "[+] Bootstrap complete."
echo "[*] Running readiness doctor..."
bash scripts/alfa_doctor.sh
