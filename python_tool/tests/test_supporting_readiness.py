import os
import sys
import tempfile
import unittest
from pathlib import Path

from scapy.all import Dot11, Dot11Beacon, Dot11Elt, RadioTap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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


if __name__ == "__main__":
    unittest.main()
