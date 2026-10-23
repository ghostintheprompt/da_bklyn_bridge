import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from scapy.all import Dot11, Dot11Beacon, Dot11Elt, RadioTap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import remote_id
from remote_id import RemoteIDMonitor, decode_vendor_ie
from storage import Database


def basic_id_msg():
    m = bytearray(25)
    m[0] = (0 << 4) | 2            # type 0 BasicID, protocol version 2
    m[1] = (1 << 4) | 2            # id_type 1 (serial), ua_type 2 (multirotor)
    m[2:22] = b"1596F3B2C4D5E6F7".ljust(20, b"\x00")
    return bytes(m)


def location_msg():
    m = bytearray(25)
    m[0] = (1 << 4) | 2            # type 1 Location
    m[1] = (2 << 4) | 0            # status 2 (airborne), flags 0 (no E/W, speed mult 0)
    m[2] = 90                      # track 90 deg
    m[3] = 20                      # speed raw: 20 * 0.25 = 5.0 m/s
    m[4] = 0                       # vertical speed 0
    m[5:9] = struct.pack("<i", 407589000)    # lat 40.7589
    m[9:13] = struct.pack("<i", -739851000)  # lon -73.9851
    m[13:15] = struct.pack("<H", 2000)       # pressure alt (unused)
    m[15:17] = struct.pack("<H", 2240)       # geo alt: 2240*0.5-1000 = 120.0
    m[17:19] = struct.pack("<H", 2100)       # height: 2100*0.5-1000 = 50.0
    return bytes(m)


def operator_id_msg():
    m = bytearray(25)
    m[0] = (5 << 4) | 2            # type 5 OperatorID
    m[1] = 0                       # CAA operator id type
    m[2:22] = b"FA-OP-12345".ljust(20, b"\x00")
    return bytes(m)


def odid_message_pack(*messages):
    pack = bytes([0xF2, 25, len(messages)])    # type 0xF pack, ver 2; single size 25; count
    for m in messages:
        pack += m
    return pack


def odid_vendor_ie(payload):
    return remote_id.ODID_OUI + bytes([remote_id.ODID_VENDOR_TYPE]) + payload


def beacon_with_vendor_ie(info):
    return (
        RadioTap()
        / Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2="AA:BB:CC:00:11:22", addr3="AA:BB:CC:00:11:22")
        / Dot11Beacon()
        / Dot11Elt(ID="SSID", info=b"anything")
        / Dot11Elt(ID=221, info=info)
    )


class RemoteIDDecoderTests(unittest.TestCase):
    def test_decodes_real_message_pack_fields(self):
        pack = odid_message_pack(basic_id_msg(), location_msg(), operator_id_msg())
        decoded = decode_vendor_ie(odid_vendor_ie(pack))

        by_msg = {d["msg"]: d for d in decoded}
        self.assertEqual(by_msg["BasicID"]["uas_id"], "1596F3B2C4D5E6F7")
        self.assertEqual(by_msg["BasicID"]["id_type"], "Serial (CTA-2063-A)")

        loc = by_msg["Location"]
        self.assertAlmostEqual(loc["lat"], 40.7589, places=4)
        self.assertAlmostEqual(loc["lon"], -73.9851, places=4)
        self.assertAlmostEqual(loc["geo_alt_m"], 120.0, places=1)
        self.assertAlmostEqual(loc["height_agl_m"], 50.0, places=1)
        self.assertAlmostEqual(loc["speed_mps"], 5.0, places=2)
        self.assertEqual(loc["track_deg"], 90)
        self.assertEqual(loc["status"], "Airborne")

        self.assertEqual(by_msg["OperatorID"]["operator_id"], "FA-OP-12345")

    def test_process_packet_logs_decoded_alert(self):
        os.environ["SENTINEL_ALLOW_INSECURE_DB"] = "1"
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(str(Path(tmp) / "s.db"))
            pkt = beacon_with_vendor_ie(odid_vendor_ie(odid_message_pack(basic_id_msg(), location_msg())))
            RemoteIDMonitor(db).process_packet(pkt)
            alerts = db.get_recent_alerts(limit=5)
            db.conn.close()
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0][1], "REMOTE_ID_DRONE")
        self.assertIn("1596F3B2C4D5E6F7", alerts[0][2])
        self.assertIn("40.7589", alerts[0][2])

    def test_does_not_match_non_odid_vendor_tag(self):
        # Different OUI: must NOT decode as ODID.
        self.assertIsNone(decode_vendor_ie(b"\x00\x11\x22\x01somedata"))

    def test_old_fake_trigger_no_longer_fires(self):
        # The previous version string-matched the ASCII "OPENDRONEID". A real
        # decoder must ignore that, it is not the ODID binary format.
        self.assertIsNone(decode_vendor_ie(b"\x00\x50\xf2OPENDRONEID:lab"))


if __name__ == "__main__":
    unittest.main()
