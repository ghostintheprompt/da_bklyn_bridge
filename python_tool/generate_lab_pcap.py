#!/usr/bin/env python3
"""
Generate a deterministic, synthetic 802.11 lab pcap for offline validation.

The packets are constructed locally with Scapy. This script does not open a
wireless interface, change monitor mode, hop channels, or transmit frames.
"""

import argparse
from pathlib import Path
from textwrap import dedent

from scapy.all import (
    Dot11,
    Dot11Beacon,
    Dot11Deauth,
    Dot11Elt,
    Dot11ProbeReq,
    EAPOL,
    LLC,
    RadioTap,
    SNAP,
    wrpcap,
)
from scapy.layers.dot11 import Dot11EltRSN


BROADCAST = "ff:ff:ff:ff:ff:ff"
DEFAULT_CLIENT = "02:11:22:33:44:55"


def beacon_packet(ssid, bssid, channel=6, vendor_payload=None):
    pkt = (
        RadioTap()
        / Dot11(type=0, subtype=8, addr1=BROADCAST, addr2=bssid, addr3=bssid)
        / Dot11Beacon(cap="ESS+privacy")
        / Dot11Elt(ID="SSID", info=ssid.encode("utf-8"))
        / Dot11Elt(ID="DSset", info=bytes([channel]))
        / Dot11EltRSN()
    )
    if vendor_payload:
        pkt = pkt / Dot11Elt(ID=221, info=vendor_payload)
    return pkt


def probe_request_packet(client_mac, ssid):
    return (
        RadioTap()
        / Dot11(type=0, subtype=4, addr1=BROADCAST, addr2=client_mac, addr3=BROADCAST)
        / Dot11ProbeReq()
        / Dot11Elt(ID="SSID", info=ssid.encode("utf-8"))
    )


def eapol_packet(bssid, client_mac):
    return (
        RadioTap()
        / Dot11(type=2, subtype=0, addr1=client_mac, addr2=bssid, addr3=bssid)
        / LLC(dsap=0xAA, ssap=0xAA, ctrl=3)
        / SNAP(OUI=0, code=0x888E)
        / EAPOL(version=2, type=3, len=0)
    )


def deauth_packet(bssid, client_mac, reason=7):
    return (
        RadioTap()
        / Dot11(type=0, subtype=12, addr1=client_mac, addr2=bssid, addr3=bssid)
        / Dot11Deauth(reason=reason)
    )


def high_entropy_vendor_payload():
    return bytes(range(255))


def build_lab_packets(
    ssid="TrustedNet",
    authorized_bssid="AA:BB:CC:DD:EE:01",
    rogue_bssid="AA:BB:CC:DD:EE:99",
    client_mac=DEFAULT_CLIENT,
    probe_ssid="CoffeeShop",
):
    return [
        beacon_packet(ssid, authorized_bssid, channel=6),
        beacon_packet(ssid, rogue_bssid, channel=6),
        beacon_packet("TelemetryNet", "AA:BB:CC:DD:EE:77", channel=11, vendor_payload=high_entropy_vendor_payload()),
        probe_request_packet(client_mac, probe_ssid),
        eapol_packet(authorized_bssid, client_mac),
        deauth_packet(rogue_bssid, client_mac),
        deauth_packet(rogue_bssid, client_mac),
    ]


def generate_lab_pcap(out_path, **kwargs):
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    packets = build_lab_packets(**kwargs)
    wrpcap(str(out), packets)
    return len(packets)


def write_lab_config(config_path, ssid="TrustedNet", authorized_bssid="AA:BB:CC:DD:EE:01"):
    config = Path(config_path)
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        dedent(
            f"""
            watched_ssids:
              - "{ssid}"
            watched_bssids:
              - "{authorized_bssid}"
            blocklist_macs: []
            deauth_threshold: 1
            interface: offline-replay
            dwell_time: 2
            discord_webhook_url: ""

            operation_mode: passive
            trusted_access_ack: false
            authorized_lab_bssids: []

            active_mitigation:
              enabled: false
              allowed_bssids: []
              allow_broadcast_client: false
              frame_count: 1
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="Generate a deterministic offline lab pcap.")
    parser.add_argument("--out", default="lab_validation.pcap", help="Output pcap path")
    parser.add_argument("--write-config", help="Optional matching passive config path")
    parser.add_argument("--ssid", default="TrustedNet", help="Watched lab SSID")
    parser.add_argument("--authorized-bssid", default="AA:BB:CC:DD:EE:01", help="Owned authorized AP BSSID")
    parser.add_argument("--rogue-bssid", default="AA:BB:CC:DD:EE:99", help="Synthetic unauthorized AP BSSID")
    parser.add_argument("--client-mac", default=DEFAULT_CLIENT, help="Synthetic client MAC")
    parser.add_argument("--probe-ssid", default="CoffeeShop", help="Synthetic probed SSID")
    args = parser.parse_args()

    packet_count = generate_lab_pcap(
        args.out,
        ssid=args.ssid,
        authorized_bssid=args.authorized_bssid,
        rogue_bssid=args.rogue_bssid,
        client_mac=args.client_mac,
        probe_ssid=args.probe_ssid,
    )

    if args.write_config:
        write_lab_config(args.write_config, ssid=args.ssid, authorized_bssid=args.authorized_bssid)
        print(f"[+] Wrote matching passive config: {args.write_config}")

    print(f"[+] Wrote synthetic lab pcap: {args.out}")
    print(f"[+] Packets: {packet_count}")
    print("[+] Offline only: no interface opened and no RF frames transmitted.")


if __name__ == "__main__":
    main()
