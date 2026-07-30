import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generate_lab_pcap import generate_lab_pcap, write_lab_config
from replay_pcap import replay_pcap
from report_bundle import build_report_bundle


class OfflineArtifactTests(unittest.TestCase):
    def setUp(self):
        os.environ["SENTINEL_ALLOW_INSECURE_DB"] = "1"
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.pcap_path = self.base / "lab_validation.pcap"
        self.config_path = self.base / "lab_config.yaml"
        self.db_path = self.base / "replay_sentinel.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_generated_lab_pcap_replays_into_expected_alerts(self):
        packet_count = generate_lab_pcap(self.pcap_path)
        write_lab_config(self.config_path)

        replayed, db = replay_pcap(self.pcap_path, self.db_path, self.config_path)
        alerts = db.get_recent_alerts(limit=100)
        aps = db.get_recent_aps(limit=100)
        probes = db.get_recent_probes(limit=100)
        db.conn.close()

        alert_types = {alert[1] for alert in alerts}
        self.assertEqual(packet_count, 7)
        self.assertEqual(replayed, 7)
        self.assertGreaterEqual(len(aps), 3)
        self.assertEqual(len(probes), 1)
        self.assertEqual(sum(1 for alert in alerts if alert[1] == "ROGUE_AP_DETECTED"), 1)
        self.assertIn("ROGUE_AP_DETECTED", alert_types)
        self.assertIn("DEAUTH_ATTACK", alert_types)
        self.assertIn("WPA_HANDSHAKE", alert_types)
        self.assertIn("COVERT_CHANNEL_SUSPECTED", alert_types)

    def test_report_bundle_writes_redacted_summary_and_manifest(self):
        generate_lab_pcap(self.pcap_path)
        write_lab_config(self.config_path)
        _, db = replay_pcap(self.pcap_path, self.db_path, self.config_path)
        db.conn.close()

        bundle_dir, manifest = build_report_bundle(self.db_path, self.config_path, self.base / "reports")
        summary = (bundle_dir / "SUMMARY.md").read_text(encoding="utf-8")

        self.assertTrue((bundle_dir / "manifest.json").exists())
        self.assertEqual(manifest["counts"]["aps"], 3)
        self.assertGreaterEqual(manifest["counts"]["alerts"], 4)
        self.assertEqual(manifest["rogue_ap_rows"], 1)
        self.assertTrue(manifest["redacted"])
        self.assertIn("ROGUE_AP_DETECTED", summary)
        self.assertIn("MAC_", summary)
        self.assertNotIn("AA:BB:CC:DD:EE:99", summary)


if __name__ == "__main__":
    unittest.main()
