#!/usr/bin/env bash
# Da Bklyn Bridge Alfa readiness check.
# This script does not transmit frames. The optional monitor probe changes local
# interface mode and restores it when possible.

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE_IFACE=""
HOST_OS="$(uname -s)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --probe-monitor)
      PROBE_IFACE="${2:-}"
      shift 2
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/alfa_doctor.sh [--probe-monitor wlan0]

Checks whether a Linux VM can see the Alfa/USB wireless adapter, whether core
tools are installed, and whether Python can import the local capture stack.

By default this is read-only. --probe-monitor temporarily toggles the selected
interface into monitor mode and restores managed mode when possible.
USAGE
      exit 0
      ;;
    *)
      echo "[!] Unknown option: $1"
      exit 2
      ;;
  esac
done

section() { printf '\n== %s ==\n' "$1"; }
ok() { printf '[OK] %s\n' "$1"; }
warn() { printf '[WARN] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

section "Host"
printf 'Date: %s\n' "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
printf 'Kernel: %s\n' "$(uname -a)"
printf 'Project: %s\n' "$ROOT_DIR"
df -h "$ROOT_DIR" | sed -n '1,2p'

if [[ "$HOST_OS" == "Darwin" ]]; then
  warn "This is macOS. Alfa monitor-mode capture should run inside a Linux ARM VM with USB passthrough."
  warn "Build/view the dashboard on macOS if you want, but run capture inside the VM."
fi

section "Required Tools"
if [[ "$HOST_OS" == "Darwin" ]]; then
  for tool in python3 system_profiler ioreg; do
    if have "$tool"; then ok "$tool found"; else warn "$tool missing"; fi
  done
  for tool in iw ip lsusb airmon-ng aireplay-ng; do
    if have "$tool"; then ok "$tool found"; else warn "$tool checked inside the Linux capture VM"; fi
  done
  if have tcpdump; then ok "tcpdump found"; else warn "tcpdump optional/missing"; fi
else
  for tool in python3 iw ip lsusb; do
    if have "$tool"; then ok "$tool found"; else fail "$tool missing"; fi
  done
  for tool in airmon-ng aireplay-ng tcpdump; do
    if have "$tool"; then ok "$tool found"; else warn "$tool optional/missing"; fi
  done
fi

section "USB Wireless Adapter"
if have lsusb; then
  USB_LINES="$(lsusb | grep -Ei 'alfa|realtek|mediatek|ralink|atheros|qualcomm|802\.11|wireless|wlan' || true)"
  if [[ -n "$USB_LINES" ]]; then
    printf '%s\n' "$USB_LINES"
  else
    warn "No obvious USB Wi-Fi adapter found. In UTM, attach the Alfa from the VM USB menu."
  fi
elif [[ "$HOST_OS" == "Darwin" ]] && have system_profiler; then
  USB_LINES="$(system_profiler SPUSBDataType 2>/dev/null | grep -Ei 'alfa|realtek|mediatek|ralink|atheros|qualcomm|802\.11|wireless|wlan|8812|7612|9271' || true)"
  if [[ -z "$USB_LINES" ]] && have ioreg; then
    USB_LINES="$(ioreg -r -c IOUSBHostDevice -l -w 0 2>/dev/null \
      | awk '
        /USB Product Name|USB Vendor Name|kUSBProductString|kUSBVendorString|idVendor|idProduct/ { candidate = candidate $0 "\n" }
        /alfa|Alfa|Realtek|MediaTek|Ralink|Atheros|Qualcomm|802\.11|wireless|wlan|8812|7612|9271/ { found = 1 }
        /^$/ && candidate {
          if (found) printf "%s", candidate
          candidate = ""
          found = 0
        }
        END {
          if (candidate && found) printf "%s", candidate
        }
      ' \
      | awk '
        {
          gsub(/^[[:space:]|]+/, "", $0)
          if (!seen[$0]++) print
        }
      ' || true)"
  fi
  if [[ -n "$USB_LINES" ]]; then
    printf '%s\n' "$USB_LINES"
    warn "macOS sees a likely adapter. For capture, attach it to the Linux VM through UTM USB passthrough."
  else
    warn "macOS does not show an obvious Alfa-class USB Wi-Fi adapter."
    warn "If this is an Alfa router/AP, use it as your owned lab target. If this is a USB adapter, check cable, hub, and UTM passthrough."
  fi
else
  warn "Install usbutils to inspect USB passthrough."
fi

section "Wireless Interfaces"
if have iw; then
  IW_OUT="$(iw dev 2>/dev/null || true)"
  if [[ -n "$IW_OUT" ]]; then
    printf '%s\n' "$IW_OUT"
  else
    warn "iw is installed, but no wireless interface is exposed to Linux."
  fi
elif [[ "$HOST_OS" == "Darwin" ]]; then
  warn "Wireless capture interfaces appear inside the Linux VM after USB passthrough."
else
  warn "iw is missing. Install it before capture."
fi

section "Driver Hints"
if have lsmod; then
  lsmod | grep -Ei '88xx|8812|mt76|ath9k|rtl|cfg80211|mac80211' || warn "No common wireless driver modules visible."
elif [[ "$HOST_OS" == "Darwin" ]]; then
  warn "Linux driver modules are checked inside the capture VM."
fi

section "Python Stack"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
if [[ -x "$PYTHON_BIN" ]]; then
  ok "using project venv: $PYTHON_BIN"
elif [[ "$HOST_OS" == "Darwin" ]]; then
  PYTHON_BIN=""
  warn "project .venv not found; skipping capture Python imports on macOS host"
  warn "Run scripts/m1_vm_bootstrap.sh inside the Linux VM to build the capture stack."
elif have python3; then
  PYTHON_BIN="python3"
  warn "project .venv not found; checking system python only"
fi

if [[ -n "${PYTHON_BIN:-}" ]]; then
  (
    cd "$ROOT_DIR" || exit 1
    "$PYTHON_BIN" - <<'PY'
import importlib.util
mods = ["scapy", "rich", "yaml", "flask", "flask_cors"]
for mod in mods:
    print(f"[{'OK' if importlib.util.find_spec(mod) else 'FAIL'}] python import {mod}")
for mod in ["pandas", "sklearn", "pysqlcipher3"]:
    print(f"[{'OK' if importlib.util.find_spec(mod) else 'WARN'}] optional python import {mod}")
PY
  )
else
  if [[ "$HOST_OS" != "Darwin" ]]; then
    fail "python3 missing"
  fi
fi

if [[ -n "$PROBE_IFACE" ]]; then
  section "Monitor Probe"
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    fail "Monitor probe requires root. Re-run with sudo."
    exit 1
  fi
  if ! have ip || ! have iw; then
    fail "Monitor probe requires ip and iw."
    exit 1
  fi
  BEFORE_MODE="$(iw dev "$PROBE_IFACE" info 2>/dev/null | awk '/type/ {print $2; exit}')"
  ip link set "$PROBE_IFACE" down || exit 1
  if iw dev "$PROBE_IFACE" set type monitor; then
    ip link set "$PROBE_IFACE" up || true
    AFTER_MODE="$(iw dev "$PROBE_IFACE" info 2>/dev/null | awk '/type/ {print $2; exit}')"
    ok "$PROBE_IFACE monitor transition result: ${AFTER_MODE:-unknown}"
  else
    ip link set "$PROBE_IFACE" up || true
    fail "$PROBE_IFACE did not enter monitor mode."
  fi
  if [[ "${BEFORE_MODE:-}" == "managed" ]]; then
    ip link set "$PROBE_IFACE" down || true
    iw dev "$PROBE_IFACE" set type managed || true
    ip link set "$PROBE_IFACE" up || true
    ok "$PROBE_IFACE restored to managed mode."
  fi
fi

section "Next"
printf '1. If USB is missing: attach the Alfa to the VM in UTM.\n'
printf '2. If iw has no interface: install the chipset driver or try a MediaTek/Atheros Alfa.\n'
printf '3. If monitor mode works: run scripts/run_passive.sh --interface wlan0 for passive capture.\n'
printf '4. Add --lab-insecure only inside your owned lab when you are intentionally testing active controls.\n'
