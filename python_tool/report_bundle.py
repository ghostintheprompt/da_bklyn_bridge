#!/usr/bin/env python3
"""
Build a redacted Markdown/JSON report bundle from a Da Bklyn Bridge DB.

This summarizes local evidence for review. It does not copy raw captures or
upload data.
"""

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

try:
    from pysqlcipher3 import dbapi2 as sqlite3
except ImportError:
    import sqlite3


MAC_RE = re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b")


class Redactor:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.tokens = {}

    def text(self, value):
        if value is None:
            return ""
        text = str(value)
        if not self.enabled:
            return text

        def replace(match):
            mac = match.group(0).upper()
            if mac not in self.tokens:
                digest = hashlib.sha256(mac.encode("utf-8")).hexdigest()[:10].upper()
                self.tokens[mac] = f"MAC_{digest}"
            return self.tokens[mac]

        return MAC_RE.sub(replace, text)


def file_sha256(path):
    file_path = Path(path)
    if not file_path.exists():
        return None
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path):
    config_path = Path(path)
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def open_db(db_path):
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")

    conn = sqlite3.connect(str(path))
    key = os.environ.get("SENTINEL_DB_KEY")
    if key:
        escaped_key = key.replace("'", "''")
        conn.execute(f"PRAGMA key='{escaped_key}'")
        conn.execute("SELECT count(*) FROM sqlite_master;")
    return conn


def fetch_rows(conn, query, args=()):
    cursor = conn.execute(query, args)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def table_count(conn, table):
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.Error:
        return 0


def configured_rogue_aps(conn, config):
    authorized = [bssid.upper() for bssid in config.get("watched_bssids", []) if isinstance(bssid, str)]
    if not authorized:
        return []
    placeholders = ", ".join(["?"] * len(authorized))
    query = f"""
        SELECT ssid, bssid, channel, rssi, crypto
        FROM aps
        WHERE UPPER(bssid) NOT IN ({placeholders})
        AND ssid IN (SELECT DISTINCT ssid FROM aps WHERE UPPER(bssid) IN ({placeholders}))
        ORDER BY last_seen DESC
    """
    return fetch_rows(conn, query, authorized + authorized)


def escape_cell(value, redactor):
    text = redactor.text(value).replace("\n", " ").replace("|", "\\|")
    return text or "-"


def markdown_table(headers, rows, redactor):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(escape_cell(row.get(header), redactor) for header in headers) + " |")
    return "\n".join(lines)


def build_summary(db_path, config_path, conn, config, config_hash, redactor):
    counts = {
        "aps": table_count(conn, "aps"),
        "probes": table_count(conn, "probes"),
        "deauths": table_count(conn, "deauths"),
        "alerts": table_count(conn, "alerts"),
    }
    rogue_aps = configured_rogue_aps(conn, config)
    deauth_stats = fetch_rows(
        conn,
        """
        SELECT bssid, COUNT(*) AS frame_count, MIN(timestamp) AS first_seen, MAX(timestamp) AS last_seen
        FROM deauths
        GROUP BY bssid
        ORDER BY frame_count DESC
        """,
    )
    recent_alerts = fetch_rows(
        conn,
        """
        SELECT timestamp, type, severity, msg
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT 20
        """,
    )
    recent_aps = fetch_rows(
        conn,
        """
        SELECT ssid, bssid, channel, rssi, crypto, last_seen
        FROM aps
        ORDER BY last_seen DESC
        LIMIT 20
        """,
    )
    recent_probes = fetch_rows(
        conn,
        """
        SELECT mac, ssid, rssi, timestamp
        FROM probes
        ORDER BY timestamp DESC
        LIMIT 20
        """,
    )

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Da Bklyn Bridge Report Bundle",
        "",
        f"- Generated: {generated_at}",
        f"- Database: `{Path(db_path).resolve()}`",
        f"- Config: `{Path(config_path).resolve()}`",
        f"- Config SHA256: `{config_hash or 'missing'}`",
        f"- MAC redaction: `{'enabled' if redactor.enabled else 'disabled'}`",
        "",
        "## Counts",
        "",
        markdown_table(
            ["metric", "count"],
            [{"metric": key, "count": value} for key, value in counts.items()],
            redactor,
        ),
        "",
        "## Rogue AP Review",
        "",
    ]

    if rogue_aps:
        lines.append(markdown_table(["ssid", "bssid", "channel", "rssi", "crypto"], rogue_aps, redactor))
    elif config.get("watched_bssids"):
        lines.append("No rogue AP rows were found for the configured watched BSSID set.")
    else:
        lines.append("Rogue AP review skipped because `watched_bssids` is empty in the config.")

    lines.extend(["", "## Deauth Summary", ""])
    lines.append(markdown_table(["bssid", "frame_count", "first_seen", "last_seen"], deauth_stats, redactor) if deauth_stats else "No deauth rows found.")

    lines.extend(["", "## Recent Alerts", ""])
    lines.append(markdown_table(["timestamp", "type", "severity", "msg"], recent_alerts, redactor) if recent_alerts else "No alert rows found.")

    lines.extend(["", "## Recent AP Rows", ""])
    lines.append(markdown_table(["ssid", "bssid", "channel", "rssi", "crypto", "last_seen"], recent_aps, redactor) if recent_aps else "No AP rows found.")

    lines.extend(["", "## Recent Probe Rows", ""])
    lines.append(markdown_table(["mac", "ssid", "rssi", "timestamp"], recent_probes, redactor) if recent_probes else "No probe rows found.")

    lines.extend(
        [
            "",
            "## Handling Notes",
            "",
            "- This bundle summarizes the local database only; raw pcaps and the raw DB are not copied into the bundle.",
            "- Keep MAC redaction enabled for shared examples unless scope requires exact identifiers.",
            "- Attach scope, ROE, operator notes, command log, and screenshots separately when preparing a trusted-access packet.",
        ]
    )

    manifest_summary = {
        "generated_at": generated_at,
        "counts": counts,
        "rogue_ap_rows": len(rogue_aps),
        "deauth_groups": len(deauth_stats),
        "recent_alert_rows": len(recent_alerts),
        "redacted": redactor.enabled,
    }
    return "\n".join(lines) + "\n", manifest_summary


def unique_bundle_dir(out_dir, timestamp):
    base = Path(out_dir) / f"report_{timestamp}"
    candidate = base
    index = 2
    while candidate.exists():
        candidate = Path(f"{base}_{index}")
        index += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def build_report_bundle(db_path, config_path, out_dir="report_bundle", redact=True):
    config = load_config(config_path)
    config_hash = file_sha256(config_path)
    redactor = Redactor(enabled=redact)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = unique_bundle_dir(out_dir, timestamp)

    conn = open_db(db_path)
    try:
        summary_md, manifest_summary = build_summary(db_path, config_path, conn, config, config_hash, redactor)
    finally:
        conn.close()

    summary_path = bundle_dir / "SUMMARY.md"
    manifest_path = bundle_dir / "manifest.json"
    summary_path.write_text(summary_md, encoding="utf-8")

    manifest = {
        **manifest_summary,
        "database_path": str(Path(db_path).resolve()),
        "config_path": str(Path(config_path).resolve()),
        "config_sha256": config_hash,
        "files": ["SUMMARY.md", "manifest.json"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return bundle_dir, manifest


def main():
    parser = argparse.ArgumentParser(description="Build a redacted Da Bklyn Bridge report bundle.")
    parser.add_argument("--db", default="replay_sentinel.db", help="Input SQLite/SQLCipher database")
    parser.add_argument("--config", default="config.yaml", help="Config used for capture or replay")
    parser.add_argument("--out", default="report_bundle", help="Output bundle parent directory")
    parser.add_argument("--no-redact", action="store_true", help="Include raw MAC/BSSID values in the Markdown report")
    args = parser.parse_args()

    bundle_dir, manifest = build_report_bundle(args.db, args.config, args.out, redact=not args.no_redact)
    print(f"[+] Wrote report bundle: {bundle_dir}")
    print(f"[+] Counts: {manifest['counts']}")
    print(f"[+] Redaction: {'off' if args.no_redact else 'on'}")


if __name__ == "__main__":
    main()
