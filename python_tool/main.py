import os
import sys
import time
import shutil
import subprocess
import argparse
from pathlib import Path
from capture import PacketCapturer
from storage import Database
from alerting import AlertManager
from remote_id import RemoteIDMonitor
from gps_module import GPSLogger
from display_cli import SentinelDashboard
from update_checker import check_for_updates
from kernel_monitor import KernelMonitor

DEFAULT_CONFIG = str(Path(__file__).resolve().with_name("config.yaml"))


def run_command(args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def list_wireless_interfaces():
    if not shutil.which("iw"):
        return []

    result = run_command(["iw", "dev"])
    interfaces = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("Interface "):
            interfaces.append(line.split()[1])
    return interfaces


def interface_mode(interface):
    if not shutil.which("iw"):
        return "unknown"

    result = run_command(["iw", "dev"])
    current = None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Interface "):
            current = stripped.split()[1]
        elif current == interface and stripped.startswith("type "):
            return stripped.split()[1]
    return "unknown"


def interface_exists(interface):
    if not interface:
        return False
    if shutil.which("ip"):
        return run_command(["ip", "link", "show", "dev", interface]).returncode == 0
    return interface in list_wireless_interfaces()


def detect_default_interface(config_path):
    configured = None
    try:
        import yaml
        with open(config_path, "r", encoding="utf-8") as handle:
            configured = (yaml.safe_load(handle) or {}).get("interface")
    except (OSError, ImportError, AttributeError):
        configured = None

    if configured and configured != "wlan0" and interface_exists(configured):
        return configured

    wireless = list_wireless_interfaces()
    if wireless:
        if configured in wireless:
            return configured
        for name in wireless:
            if interface_mode(name) == "monitor":
                return name
        return wireless[0]

    return configured if configured and interface_exists(configured) else None


def monitor_interfaces():
    return [name for name in list_wireless_interfaces() if interface_mode(name) == "monitor"]


def setup_monitor_mode(interface, skip_setup=False):
    if skip_setup:
        print(f"[*] Using {interface} as provided; monitor-mode setup skipped.")
        return interface

    print(f"[*] Attempting to set {interface} to monitor mode...")

    if interface_mode(interface) == "monitor":
        print(f"[+] {interface} is already in monitor mode.")
        return interface

    if shutil.which("ip") and shutil.which("iw"):
        methods = [
            ["iw", "dev", interface, "set", "type", "monitor"],
            ["iw", "dev", interface, "set", "monitor", "control"],
        ]
        for method in methods:
            subprocess.run(["ip", "link", "set", interface, "down"], check=False)
            result = run_command(method)
            subprocess.run(["ip", "link", "set", interface, "up"], check=False)
            if result.returncode == 0:
                print(f"[+] {interface} is now in monitor mode.")
                return interface

    if shutil.which("airmon-ng"):
        print("[!] Direct iw setup failed. Trying airmon-ng fallback...")
        before = set(list_wireless_interfaces())
        result = run_command(["airmon-ng", "start", interface])
        after = set(list_wireless_interfaces())
        candidates = [f"{interface}mon"] + sorted(after - before) + monitor_interfaces() + [interface]
        for candidate in candidates:
            if interface_exists(candidate) and interface_mode(candidate) == "monitor":
                print(f"[+] airmon-ng started monitor interface {candidate}.")
                return candidate
        if result.returncode == 0:
            print(f"[+] airmon-ng completed. Continuing with {interface}.")
            return interface

    print("[!] Failed to set monitor mode.")
    print("[!] Run scripts/alfa_doctor.sh inside the Linux VM for driver and USB passthrough checks.")
    return None

def _load_scope_file(path):
    """Load authorized target BSSIDs from an engagement scope file.
    One BSSID per line; blank lines and '#' comments are ignored."""
    bssids = []
    try:
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.split("#", 1)[0].strip()
                if line:
                    bssids.append(line.upper())
    except OSError as e:
        print(f"[!] Could not read scope file {path}: {e}")
        sys.exit(1)
    return bssids


def main():
    parser = argparse.ArgumentParser(description="Da Bklyn Bridge - Alfa-class passive monitor")
    parser.add_argument("-i", "--interface", help="Wireless interface (for example wlan0). Autodetected when omitted.")
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG, help="Path to config file")
    parser.add_argument("--db", default="sentinel.db", help="SQLite/SQLCipher database path")
    parser.add_argument("--skip-monitor-setup", action="store_true", help="Use the interface as-is when monitor mode is already configured")
    parser.add_argument("--arm", action="store_true", help="Arm active mitigation (targeted deauth). Requires a declared engagement scope; fires only at in-scope BSSIDs.")
    parser.add_argument("--scope", help="Engagement scope file: one authorized target BSSID per line (# comments ok). Loads active_mitigation.scope_bssids from your signed ROE.")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("[!] This tool must be run as root for packet capture.")
        sys.exit(1)

    interface = args.interface or detect_default_interface(args.config)
    if not interface:
        print("[!] No wireless interface found.")
        print("[!] In the Apple-silicon ARM VM, confirm the Alfa USB device is passed through, then run scripts/alfa_doctor.sh.")
        sys.exit(1)

    # Check for updates only when explicitly enabled. Trusted/lab runs should not
    # create unexpected outbound traffic by default.
    check_for_updates()

    # Initial Setup
    monitor_interface = setup_monitor_mode(interface, skip_setup=args.skip_monitor_setup)
    if not monitor_interface:
        print("[!] Could not initialize monitor mode. Exiting.")
        sys.exit(1)

    db = Database(args.db)
    alert_mgr = AlertManager(db, config_path=args.config)
    if args.scope:
        scope_bssids = _load_scope_file(args.scope)
        alert_mgr.config.setdefault("active_mitigation", {})["scope_bssids"] = scope_bssids
        print(f"[*] Engagement scope loaded: {len(scope_bssids)} authorized BSSID(s) from {args.scope}")
    remote_id = RemoteIDMonitor(db)
    gps_logger = GPSLogger()
    
    # Phase 4 Integrations
    kernel_monitor = KernelMonitor(monitor_interface, alert_mgr)
    capturer = PacketCapturer(monitor_interface, db, alert_mgr, remote_id, gps_logger)
    
    if args.arm:
        if not capturer.mitigator.enable():
            print("[!] Bridge Mode refused by safety gate. Continuing in passive monitor mode.")

    dashboard = SentinelDashboard(db, capturer)

    print("[*] Da Bklyn Bridge initialized. Starting capture...")
    try:
        kernel_monitor.start()
        capturer.start()
        dashboard.run()
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    finally:
        kernel_monitor.stop()
        capturer.stop()
        print("[*] Cleanup complete.")

if __name__ == "__main__":
    main()
