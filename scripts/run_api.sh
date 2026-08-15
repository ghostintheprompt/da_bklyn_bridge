#!/usr/bin/env bash
# Start the local dashboard API with the venv when available.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${SENTINEL_API_HOST:-127.0.0.1}"
PORT="${SENTINEL_API_PORT:-5000}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="${2:-}"; shift 2 ;;
    --port) PORT="${2:-}"; shift 2 ;;
    --host-vm)
      HOST="0.0.0.0"
      shift
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/run_api.sh [--host 127.0.0.1] [--port 5000] [--host-vm]

Default is localhost only. Use --host-vm only when the VM network is trusted or
host-only and you need to view the dashboard from the Mac browser.
USAGE
      exit 0
      ;;
    *) echo "[!] Unknown option: $1"; exit 2 ;;
  esac
done

if [[ "$HOST" == "0.0.0.0" && -z "${SENTINEL_API_TOKEN:-}" ]]; then
  echo "[!] API will listen on all VM interfaces without a bearer token."
  echo "[!] Prefer host-only networking, UTM port forwarding, or set SENTINEL_API_TOKEN."
fi

PYTHON="$ROOT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi

export SENTINEL_API_HOST="$HOST"
export SENTINEL_API_PORT="$PORT"
cd "$ROOT_DIR"
exec "$PYTHON" "$ROOT_DIR/python_tool/api_bridge.py"
