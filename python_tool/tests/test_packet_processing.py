import os
import tempfile
import unittest
from pathlib import Path

from scapy.all import Dot11, Dot11Beacon, Dot11Deauth, Dot11Elt, Dot11ProbeReq, RadioTap

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from alerting import AlertManager
from capture import PacketCapturer
from storage import Database


class PacketProcessingTests(unittest.TestCase):
    def setUp(self):
        os.environ["SENTINEL_ALLOW_INSECURE_DB"] = "1"
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "sentinel_test.db"
        self.config_path = Path(self.tmp.name) / "config.yaml"
        self.config_path.write_text(
            "\n".join(
                [
                    "watched_ssids:",
                    '  - "TrustedNet"',
                    "watched_bssids:",
                    '  - "AA:BB:CC:DD:EE:01"',
                    "blocklist_macs: []",
                    "deauth_threshold: 1",
                    "operation_mode: passive",
                    "trusted_access_ack: false",
                    "active_mitigation:",
                    "  enabled: false",
                    "  allowed_bssids: []",
                    "  allow_broadcast_client: false",
                ]
            )
        )
        self.db = Database(str(self.db_path))
        self.alert_mgr = AlertManager(self.db, str(self.config_path))
        self.capturer = PacketCapturer("offline-test", self.db, self.alert_mgr)

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def test_probe_request_is_logged(self):
        pkt = (
            RadioTap()
            / Dot11(type=0, subtype=4, addr1="ff:ff:ff:ff:ff:ff", addr2="02:11:22:33:44:55", addr3="ff:ff:ff:ff:ff:ff")
            / Dot11ProbeReq()
            / Dot11Elt(ID="SSID", info=b"CoffeeShop")
        )

        self.capturer.packet_callback(pkt)
        probes = self.db.get_recent_probes(limit=10)

        self.assertEqual(len(probes), 1)
        self.assertEqual(probes[0][1], "02:11:22:33:44:55")
        self.assertEqual(probes[0][2], "CoffeeShop")

    def test_watched_beacon_is_logged_without_rogue_alert_for_authorized_bssid(self):
        pkt = (
            RadioTap()
            / Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2="AA:BB:CC:DD:EE:01", addr3="AA:BB:CC:DD:EE:01")
            / Dot11Beacon()
            / Dot11Elt(ID="SSID", info=b"TrustedNet")
            / Dot11Elt(ID="DSset", info=bytes([6]))
        )

        self.capturer.packet_callback(pkt)
        aps = self.db.get_recent_aps(limit=10)
        alerts = self.db.get_recent_alerts(limit=10)

        self.assertEqual(len(aps), 1)
        self.assertEqual(aps[0][0], "AA:BB:CC:DD:EE:01")
        self.assertFalse(any(alert[1] == "ROGUE_AP_DETECTED" for alert in alerts))

    def test_rogue_watched_ssid_generates_alert_but_does_not_arm_mitigation(self):
        pkt = (
            RadioTap()
            / Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2="AA:BB:CC:DD:EE:99", addr3="AA:BB:CC:DD:EE:99")
            / Dot11Beacon()
            / Dot11Elt(ID="SSID", info=b"TrustedNet")
            / Dot11Elt(ID="DSset", info=bytes([6]))
        )

        self.capturer.packet_callback(pkt)
        alerts = self.db.get_recent_alerts(limit=10)

        self.assertTrue(any(alert[1] == "ROGUE_AP_DETECTED" for alert in alerts))
        self.assertFalse(self.capturer.mitigator.bridge_mode_enabled)

    def test_deauth_threshold_generates_alert(self):
        for _ in range(2):
            pkt = (
                RadioTap()
                / Dot11(
                    type=0,
                    subtype=12,
                    addr1="11:22:33:44:55:66",
                    addr2="AA:BB:CC:DD:EE:99",
                    addr3="AA:BB:CC:DD:EE:99",
                )
                / Dot11Deauth(reason=7)
            )
            self.capturer.packet_callback(pkt)

        alerts = self.db.get_recent_alerts(limit=10)
        self.assertTrue(any(alert[1] == "DEAUTH_ATTACK" for alert in alerts))

    def test_rogue_ap_query_handles_authorized_bssid_parameters(self):
        self.db.log_ap("AA:BB:CC:DD:EE:01", "TrustedNet", 6, -45, "WPA2")
        self.db.log_ap("AA:BB:CC:DD:EE:99", "TrustedNet", 6, -50, "WPA2")

        rogues = self.db.get_rogue_aps(["AA:BB:CC:DD:EE:01"])

        self.assertEqual(len(rogues), 1)
        self.assertEqual(rogues[0][1], "AA:BB:CC:DD:EE:99")


if __name__ == "__main__":
    unittest.main()
