import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["SENTINEL_ALLOW_INSECURE_DB"] = "1"

import findings_report as fr
from storage import Database


class FindingsReportTests(unittest.TestCase):
    def _db_with_alerts(self, tmp):
        db = Database(str(Path(tmp) / "s.db"))
        db.log_alert("ROGUE_AP_DETECTED", "Rogue AP 'CorpWifi' on AA:BB:CC:00:00:01", "high")
        db.log_alert("DEAUTH_ATTACK", "Deauth flood on AA:BB:CC:00:00:02", "medium")
        db.log_alert("WPA_HANDSHAKE", "EAPOL handshake captured for AA:BB:CC:00:00:02", "info")
        db.log_alert("WATCHED_SSID_AP", "Authorized AP baseline", "info")  # NOT a finding
        db.log_alert("ARMED", "Active mitigation armed", "warning")        # NOT a finding
        alerts = db.get_recent_alerts(limit=1000)
        db.conn.close()
        return alerts

    def test_maps_real_alerts_and_excludes_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            alerts = self._db_with_alerts(tmp)
        findings = fr.build_findings(alerts)
        types = {f["type"] for f in findings}
        self.assertIn("ROGUE_AP_DETECTED", types)
        self.assertIn("DEAUTH_ATTACK", types)
        self.assertIn("WPA_HANDSHAKE", types)
        self.assertNotIn("WATCHED_SSID_AP", types)   # baseline excluded
        self.assertNotIn("ARMED", types)             # tester action excluded

    def test_render_is_pro_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            alerts = self._db_with_alerts(tmp)
        md = fr.render_markdown(fr.build_findings(alerts), client="Acme Corp")
        self.assertIn("Acme Corp", md)
        self.assertIn("Rogue / Unauthorized Access Point", md)
        self.assertIn("MITRE ATT&CK", md)
        self.assertIn("Severity:", md)
        self.assertIn("Remediation.", md)
        self.assertIn("Evidence (from the sensor):", md)
        # high severity should sort above medium
        self.assertLess(md.index("Rogue / Unauthorized"), md.index("Deauthentication"))


if __name__ == "__main__":
    unittest.main()
