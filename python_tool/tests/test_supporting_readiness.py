import os
import sys
import tempfile
import unittest
from pathlib import Path

from scapy.all import Dot11, Dot11Beacon, Dot11Elt, RadioTap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from remote_id import RemoteIDMonitor
from storage import Database
from vendors import resolve_vendor


class SupportingReadinessTests(unittest.TestCase):
    def setUp(self):
        os.environ["SENTINEL_ALLOW_INSECURE_DB"] = "1"
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_resolve_vendor_can_load_external_oui_csv(self):
        oui_csv = self.base / "oui.csv"
        oui_csv.write_text(
            "Assignment,Organization Name\nACBBCC,Example Lab Hardware\n",
            encoding="utf-8",
        )

        self.assertEqual(resolve_vendor("AC:BB:CC:00:11:22", oui_csv), "Example Lab Hardware")

    def test_remote_id_marker_logs_structured_alert(self):
        db = Database(str(self.base / "sentinel.db"))
        monitor = RemoteIDMonitor(db)
        pkt = (
            RadioTap()
            / Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2="AA:BB:CC:DD:EE:10", addr3="AA:BB:CC:DD:EE:10")
            / Dot11Beacon()
            / Dot11Elt(ID="SSID", info=b"DroneRID")
            / Dot11Elt(ID=221, info=b"\xFA\x0B\xBCOpenDroneID:lab")
        )

        monitor.process_packet(pkt)
        alerts = db.get_recent_alerts(limit=10)
        db.conn.close()

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0][1], "REMOTE_ID_DRONE")
        self.assertIn("OpenDroneID", alerts[0][2])
        self.assertIn("FA:0B:BC", alerts[0][2])


if __name__ == "__main__":
    unittest.main()
