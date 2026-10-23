import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import wireless_ops as wo


class ScopeTests(unittest.TestCase):
    def test_load_scope_from_file_ignores_comments(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
            fh.write("# engagement scope\nAA:BB:CC:DD:EE:FF\n11:22:33:44:55:66  # client AP\n")
            path = fh.name
        scope = wo.load_scope(scope_file=path)
        self.assertEqual(scope, {"AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"})

    def test_require_scope_refuses_out_of_scope(self):
        scope = {"AA:BB:CC:DD:EE:FF"}
        self.assertEqual(wo.require_scope("aa:bb:cc:dd:ee:ff", scope), "AA:BB:CC:DD:EE:FF")
        with self.assertRaises(SystemExit):
            wo.require_scope("00:00:00:00:00:01", scope)


class CommandBuilderTests(unittest.TestCase):
    def test_airodump_cmd(self):
        cmd = wo.airodump_cmd("wlan0", "aa:bb:cc:dd:ee:ff", 6, "/tmp/cap")
        self.assertEqual(cmd, ["airodump-ng", "-c", "6", "--bssid", "AA:BB:CC:DD:EE:FF",
                               "-w", "/tmp/cap", "--output-format", "pcap", "wlan0"])

    def test_deauth_cmd_broadcast_has_no_client_flag(self):
        self.assertNotIn("-c", wo.deauth_cmd("wlan0", "aa:bb:cc:dd:ee:ff", 3))

    def test_deauth_cmd_targeted_client(self):
        cmd = wo.deauth_cmd("wlan0", "aa:bb:cc:dd:ee:ff", 3, "11:22:33:44:55:66")
        self.assertIn("-c", cmd)
        self.assertIn("11:22:33:44:55:66", cmd)

    def test_convert_and_crack_hint(self):
        self.assertEqual(wo.convert_cmd("c.cap", "h.22000"), ["hcxpcapngtool", "-o", "h.22000", "c.cap"])
        self.assertEqual(wo.crack_hint("h.22000")[:3], ["hashcat", "-m", "22000"])


class MoreOpsTests(unittest.TestCase):
    def test_essid_scope_refuses_unauthorized(self):
        scope = {"CorpNet"}
        self.assertEqual(wo.require_essid_scope("CorpNet", scope), "CorpNet")
        with self.assertRaises(SystemExit):
            wo.require_essid_scope("NotAuthorized", scope)

    def test_reaver_pixie_cmd(self):
        cmd = wo.reaver_pixie_cmd("wlan0", "aa:bb:cc:dd:ee:ff", 6)
        self.assertEqual(cmd[:2], ["reaver", "-i"])
        self.assertIn("-K", cmd)
        self.assertIn("AA:BB:CC:DD:EE:FF", cmd)

    def test_eaphammer_creds_cmd(self):
        self.assertEqual(
            wo.eaphammer_creds_cmd("wlan0", "CorpNet"),
            ["eaphammer", "-i", "wlan0", "--essid", "CorpNet", "--creds"],
        )

    def test_ble_scan_cmd_is_time_bounded(self):
        cmd = wo.ble_scan_cmd(20)
        self.assertEqual(cmd[:2], ["timeout", "20"])
        self.assertIn("lescan", cmd)

    def test_wash_cmd(self):
        self.assertEqual(wo.wash_cmd("wlan0"), ["wash", "-i", "wlan0"])


if __name__ == "__main__":
    unittest.main()
