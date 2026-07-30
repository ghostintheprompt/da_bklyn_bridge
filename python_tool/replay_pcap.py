#!/usr/bin/env python3
"""
Offline replay harness for Da Bklyn Bridge.

This reads packets from a pcap/pcapng and feeds them through the same packet
callback used by live capture. It does not set monitor mode, hop channels, or
transmit frames.
"""

import argparse
import os
from pathlib import Path

from scapy.all import PcapReader

from alerting import AlertManager
from capture import PacketCapturer
from remote_id import RemoteIDMonitor
from storage import Database


class StaticGPS:
    def __init__(self, lat=0.0, lon=0.0):
        self.coords = (lat, lon)

    def get_coords(self):
        return self.coords


def replay_pcap(path, db_path, config_path, limit=None):
    os.environ.setdefault("SENTINEL_ALLOW_INSECURE_DB", "1")

    db = Database(db_path)
    alert_mgr = AlertManager(db, config_path)
    remote_id = RemoteIDMonitor(db)
    gps = StaticGPS()
    capturer = PacketCapturer("offline-replay", db, alert_mgr, remote_id, gps)

    count = 0
    with PcapReader(str(path)) as packets:
        for pkt in packets:
            capturer.packet_callback(pkt)
            count += 1
            if limit and count >= limit:
                break

    return count, db


def main():
    parser = argparse.ArgumentParser(description="Replay pcap data through Da Bklyn Bridge parsers.")
    parser.add_argument("pcap", help="pcap or pcapng file to replay")
    parser.add_argument("--db", default="replay_sentinel.db", help="Output SQLite/SQLCipher database path")
    parser.add_argument("--config", default="config.yaml", help="Config file for alerting rules")
    parser.add_argument("--limit", type=int, default=None, help="Maximum packets to replay")
    args = parser.parse_args()

    pcap_path = Path(args.pcap)
    if not pcap_path.exists():
        raise SystemExit(f"pcap not found: {pcap_path}")

    count, db = replay_pcap(pcap_path, args.db, args.config, args.limit)
    print(f"[+] Replayed packets: {count}")
    print(f"[+] AP rows: {len(db.get_recent_aps(limit=100000))}")
    print(f"[+] Probe rows: {len(db.get_recent_probes(limit=100000))}")
    print(f"[+] Alert rows: {len(db.get_recent_alerts(limit=100000))}")


if __name__ == "__main__":
    main()
