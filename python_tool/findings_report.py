#!/usr/bin/env python3
"""
Turn da_bklyn_bridge detections into a findings-report section.

Reads the evidence DB's alerts and emits a Markdown findings section in the
engagement report format (severity, framework mapping, finding, business impact,
remediation, evidence), ready to drop into the playbook's Section 6.

Honest by construction: it reports only what the sensor actually detected. It
maps each real alert type to a finding template; unknown types are reported
generically rather than dropped or dressed up. It invents nothing.
"""

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import Database

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

# Real da_bklyn alert types -> finding templates.
FINDINGS = {
    "ROGUE_AP_DETECTED": dict(
        title="Rogue / Unauthorized Access Point",
        severity="high",
        mapping="MITRE ATT&CK T1557 (Adversary-in-the-Middle), T1200 (Hardware Additions)",
        impact="A rogue AP broadcasting a trusted SSID can harvest credentials and man-in-the-middle client traffic.",
        remediation="Deploy a WIPS with rogue containment, enforce 802.1X/EAP-TLS, and alert on a known SSID appearing on an unexpected BSSID.",
    ),
    "DEAUTH_ATTACK": dict(
        title="Wireless Deauthentication (Availability) Attack",
        severity="medium",
        mapping="MITRE ATT&CK T1498 (Network Denial of Service)",
        impact="Forged deauthentication frames knock clients off the network and force reassociation, enabling handshake capture and denial of service.",
        remediation="Enable 802.11w (Protected Management Frames) so deauth frames are authenticated; monitor for deauth floods.",
    ),
    "WPA_HANDSHAKE": dict(
        title="WPA Handshake Exposure (Offline Crackability)",
        severity="high",
        mapping="MITRE ATT&CK T1040 (Network Sniffing); weak-credential risk",
        impact="A captured 4-way handshake allows unlimited offline password guessing. The network's security reduces to passphrase entropy.",
        remediation="Enforce a long, high-entropy passphrase, migrate to WPA3-SAE, and enable PMF.",
    ),
    "COVERT_CHANNEL_SUSPECTED": dict(
        title="Possible Covert Channel in Management Frames",
        severity="medium",
        mapping="MITRE ATT&CK T1048 (Exfiltration Over Alternative Protocol), T1001 (Data Obfuscation)",
        impact="High-entropy payloads in vendor-specific tags may carry covert exfiltration beneath normal monitoring.",
        remediation="Baseline expected vendor tags, alert on high-entropy or anomalous information elements, and investigate the source device.",
    ),
    "SCANNER_DETECTED": dict(
        title="Active Wireless Reconnaissance Detected",
        severity="low",
        mapping="MITRE ATT&CK T1595 (Active Scanning)",
        impact="A device probing for many networks indicates wardriving or pre-attack reconnaissance.",
        remediation="Correlate with authorized devices; track persistent probers as an early-warning signal.",
    ),
    "REMOTE_ID_DRONE": dict(
        title="Unauthorized UAS / Drone Presence (OpenDroneID)",
        severity="low",
        mapping="Physical / airspace security; ASTM F3411 Remote ID",
        impact="A drone broadcasting Remote ID in the vicinity may indicate surveillance or a physical-security concern.",
        remediation="Log the UAS and operator ID, correlate with the site physical-security policy, and escalate per policy.",
    ),
    "ANOMALY_DETECTED": dict(
        title="Behavioral Anomaly (Model-Flagged)",
        severity="low",
        mapping="NIST AI RMF MEASURE; behavioral detection",
        impact="A device or pattern deviated from the learned baseline and warrants review.",
        remediation="Triage the flagged entity, confirm benign versus malicious, and tune the baseline.",
    ),
    "GUARDRAIL_VIOLATION": dict(
        title="Policy / Guardrail Violation",
        severity="medium",
        mapping="Policy enforcement",
        impact="An action crossed a configured safety guardrail.",
        remediation="Review the triggering action and the guardrail configuration.",
    ),
}

# Baseline/operational types that are not findings.
NON_FINDING = {
    "WATCHED_SSID_AP", "WATCHED_SSID_PROBE", "MONITOR_MODE_DROPPED", "DRIVER_REMEDIATED",
    "ARMED", "ARM_REFUSED", "DEAUTH", "DEAUTH_FAILED", "OUT_OF_SCOPE", "ACTIVE_MITIGATION",
}


def build_findings(alerts):
    """alerts: rows (id, type, msg, severity, timestamp). Returns grouped findings."""
    grouped = defaultdict(list)
    for a in alerts:
        atype = a[1]
        if atype in NON_FINDING:
            continue
        grouped[atype].append({"msg": a[2], "severity": a[3], "ts": a[4]})
    findings = []
    for atype, rows in grouped.items():
        tmpl = FINDINGS.get(atype, dict(
            title=atype.replace("_", " ").title(),
            severity=(rows[0]["severity"] or "info"),
            mapping="(unmapped detection)",
            impact="Detected by the sensor; review and classify.",
            remediation="Investigate and classify this detection.",
        ))
        findings.append({"type": atype, "count": len(rows), "evidence": rows, **tmpl})
    findings.sort(key=lambda f: (SEV_ORDER.get(f["severity"], 9), -f["count"]))
    return findings


def render_markdown(findings, client="<Client>", engagement="Wireless Assessment", source_db=""):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    counts = defaultdict(int)
    for f in findings:
        counts[f["severity"]] += 1

    out = []
    out.append(f"## Wireless Findings — {client}")
    out.append(f"*{engagement} · {now} · generated from da_bklyn_bridge detections*\n")
    out.append("### Summary")
    if findings:
        summary = ", ".join(f"{counts[s]} {s}" for s in ("critical", "high", "medium", "low", "info") if counts[s])
        out.append(f"{len(findings)} distinct findings: {summary}.\n")
    else:
        out.append("No reportable findings in this capture window.\n")

    for i, f in enumerate(findings, 1):
        fid = f"WLAN-{i:03d}"
        out.append(f"### {fid} — {f['title']}")
        out.append(f"**Severity:** {f['severity'].upper()}  ")
        out.append(f"**Mapping:** {f['mapping']}  ")
        out.append(f"**Observations:** {f['count']}\n")
        out.append(f"**Finding.** {f['impact']}\n")
        out.append("**Evidence (from the sensor):**")
        for ev in f["evidence"][:5]:
            out.append(f"- `{ev['ts']}` {ev['msg']}")
        if f["count"] > 5:
            out.append(f"- ... and {f['count'] - 5} more")
        out.append(f"\n**Remediation.** {f['remediation']}\n")
    if source_db:
        out.append(f"\n*Source evidence DB: `{source_db}`. This section reports only what the sensor observed.*")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description="Export da_bklyn_bridge detections as a findings-report section")
    p.add_argument("--db", required=True, help="evidence database path")
    p.add_argument("--out", help="output .md (default: stdout)")
    p.add_argument("--client", default="<Client>")
    p.add_argument("--engagement", default="Wireless Assessment")
    args = p.parse_args()

    os.environ.setdefault("SENTINEL_ALLOW_INSECURE_DB", "1")
    db = Database(args.db)
    alerts = db.get_recent_alerts(limit=100000)
    md = render_markdown(build_findings(alerts), args.client, args.engagement, args.db)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"[+] wrote findings section: {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
