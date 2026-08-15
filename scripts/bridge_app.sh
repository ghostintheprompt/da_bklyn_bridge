#!/usr/bin/env bash
# App-like launcher for the Mac dashboard.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_TARGET="${SENTINEL_PROXY_TARGET:-http://127.0.0.1:5000}"

usage() {
  cat <<'USAGE'
Usage: scripts/bridge_app.sh [--api http://<VM_IP>:5000]

Starts the Da Bklyn Bridge dashboard as an app-like local web console.
Capture still runs inside Linux; this launcher is for the Mac/browser side.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api)
      API_TARGET="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[!] Unknown option: $1"
      usage
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

echo "[*] Da Bklyn Bridge app deck"
echo "[*] API target: $API_TARGET"
echo "[*] Capture belongs in Linux/UTM. This starts the local dashboard only."
echo "[*] Quick host preflight:"
bash scripts/alfa_doctor.sh | sed -n '1,42p'

export SENTINEL_PROXY_TARGET="$API_TARGET"
exec npm run dev -- --host 127.0.0.1
