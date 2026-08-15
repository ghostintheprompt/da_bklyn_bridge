#!/usr/bin/env bash
# Start passive capture with the local venv when available.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT_DIR/python_tool/config.yaml"
DB_PATH="$ROOT_DIR/sentinel.db"
IFACE=""
LAB_INSECURE=0
NO_PROMPT=0
NO_ELEVATE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--interface) IFACE="${2:-}"; shift 2 ;;
    -c|--config) CONFIG="${2:-}"; shift 2 ;;
    --db) DB_PATH="${2:-}"; shift 2 ;;
    --lab-insecure) LAB_INSECURE=1; shift ;;
    --no-prompt) NO_PROMPT=1; shift ;;
    --no-elevate) NO_ELEVATE=1; shift ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/run_passive.sh [--interface wlan0] [--lab-insecure] [--no-prompt]

Starts passive 802.11 capture. Use only on RF environments and devices you own
or are explicitly authorized to monitor.
USAGE
      exit 0
      ;;
    *) echo "[!] Unknown option: $1"; exit 2 ;;
  esac
done

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "[!] Capture must run inside Linux with the Alfa passed through. macOS can run the dashboard only."
  exit 1
fi

if [[ "$NO_PROMPT" -ne 1 && "${BRIDGE_SKIP_SCOPE_PROMPT:-}" != "1" ]]; then
  echo "[scope] Passive capture can still collect nearby device identifiers."
  read -r -p "Continue only if you own or are authorized for this RF environment? [y/N] " answer
  case "$answer" in
    y|Y|yes|YES) ;;
    *) echo "Aborted."; exit 1 ;;
  esac
fi

if [[ "${EUID:-$(id -u)}" -ne 0 && "$NO_ELEVATE" -ne 1 ]]; then
  SUDO_CMD=(sudo -E "$0" --no-elevate --no-prompt --config "$CONFIG" --db "$DB_PATH")
  if [[ -n "$IFACE" ]]; then
    SUDO_CMD+=(--interface "$IFACE")
  fi
  if [[ "$LAB_INSECURE" -eq 1 ]]; then
    SUDO_CMD+=(--lab-insecure)
  fi
  exec "${SUDO_CMD[@]}"
fi

if [[ "$LAB_INSECURE" -eq 1 ]]; then
  export SENTINEL_ALLOW_INSECURE_DB=1
fi

if [[ -z "${SENTINEL_DB_KEY:-}" && "${SENTINEL_ALLOW_INSECURE_DB:-}" != "1" ]]; then
  echo "[!] SENTINEL_DB_KEY is not set. SQLCipher installs will require it; use --lab-insecure only for local validation."
fi

PYTHON="$ROOT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi

CMD=("$PYTHON" "$ROOT_DIR/python_tool/main.py" "--config" "$CONFIG" "--db" "$DB_PATH")
if [[ -n "$IFACE" ]]; then
  CMD+=("--interface" "$IFACE")
fi

exec "${CMD[@]}"
