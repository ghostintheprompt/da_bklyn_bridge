import os
import sys
import time
import subprocess
import argparse
from capture import PacketCapturer
from storage import Database
from alerting import AlertManager
from remote_id import RemoteIDMonitor
from gps_module import GPSLogger
from display_cli import SentinelDashboard
from update_checker import check_for_updates

def setup_monitor_mode(interface):
    print(f"[*] Attempting to set {interface} to monitor mode...")
    try:
        # Modern 'iw' approach
        subprocess.run(["ip", "link", "set", interface, "down"], check=True)
        subprocess.run(["iw", interface, "set", "monitor", "none"], check=True)
        subprocess.run(["ip", "link", "set", interface, "up"], check=True)
        print(f"[+] {interface} is now in monitor mode.")
        return True
    except subprocess.CalledProcessError:
        print(f"[!] 'iw' failed. Trying 'airmon-ng'...")
        try:
            subprocess.run(["airmon-ng", "start", interface], check=True)
            print(f"[+] airmon-ng started on {interface}")
            return True
        except Exception as e:
            print(f"[!] Failed to set monitor mode: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Da Bklyn Bridge - Alfa AWUS036ACH Monitor")
    parser.add_argument("-i", "--interface", required=True, help="Wireless interface (e.g., wlan0)")
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    if os.getuid() != 0:
        print("[!] This tool must be run as root for packet capture.")
        sys.exit(1)

    # Check for updates silently
    check_for_updates()

    # Initial Setup
    if not setup_monitor_mode(args.interface):
        print("[!] Could not initialize monitor mode. Exiting.")
        sys.exit(1)

    db = Database("sentinel.db")
    alert_mgr = AlertManager(db, config_path=args.config)
    remote_id = RemoteIDMonitor(db)
    gps_logger = GPSLogger()
    capturer = PacketCapturer(args.interface, db, alert_mgr, remote_id, gps_logger)
    dashboard = SentinelDashboard(db, capturer)

    print("[*] Da Bklyn Bridge initialized. Starting capture...")
    try:
        capturer.start()
        dashboard.run()
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    finally:
        capturer.stop()
        print("[*] Cleanup complete.")

if __name__ == "__main__":
    main()
