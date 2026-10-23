"""
OpenDroneID (ASTM F3411 / ASD-STAN prEN 4709-002) decoder for Wi-Fi beacons.

This is a real decoder, not a string match. Drones that broadcast Remote ID over
Wi-Fi carry it in a vendor-specific information element (ID 221) under OUI
FA:0B:BC with vendor type 0x0D, holding an ODID message pack: a header plus N
fixed 25-byte messages. This parses the actual byte layout and extracts the
fields that matter to a monitor, the UAS ID (serial), the aircraft location, and
the operator ID.

Scope, stated honestly: validated against spec-conformant synthetic frames built
to the ASTM F3411 byte layout (see tests/test_remote_id.py). It has not yet been
confirmed against a live drone or an external reference implementation. It
decodes Basic ID (type 0), Location/Vector (type 1), Self-ID (type 3), System
(type 4), and Operator ID (type 5); Authentication (type 2) is recognized but
not fully parsed.

Reference: opendroneid-core-c, ASTM F3411-22a.
"""

import struct

ODID_OUI = b"\xfa\x0b\xbc"
ODID_VENDOR_TYPE = 0x0D
MESSAGE_SIZE = 25

ID_TYPE = {0: "None", 1: "Serial (CTA-2063-A)", 2: "CAA Registration", 3: "UTM UUID", 4: "Specific Session"}
UA_TYPE = {
    0: "None", 1: "Aeroplane", 2: "Helicopter/Multirotor", 3: "Gyroplane",
    4: "Hybrid Lift", 5: "Ornithopter", 6: "Glider", 7: "Kite", 8: "Free Balloon",
    9: "Captive Balloon", 10: "Airship", 11: "Free Fall/Parachute", 12: "Rocket",
    13: "Tethered Powered", 14: "Ground Obstacle", 15: "Other",
}
OP_STATUS = {0: "Undeclared", 1: "Ground", 2: "Airborne", 3: "Emergency", 4: "Remote ID System Failure"}


def _ascii(raw):
    return raw.split(b"\x00", 1)[0].decode("ascii", "replace").strip()


def _parse_basic_id(m):
    return {
        "msg": "BasicID",
        "id_type": ID_TYPE.get(m[1] >> 4, f"0x{m[1] >> 4:x}"),
        "ua_type": UA_TYPE.get(m[1] & 0x0F, f"0x{m[1] & 0x0F:x}"),
        "uas_id": _ascii(m[2:22]),
    }


def _parse_location(m):
    flags = m[1] & 0x0F
    ew_segment = bool(flags & 0x02)
    speed_mult = bool(flags & 0x01)
    track = m[2] + (180 if ew_segment else 0)
    speed_raw = m[3]
    speed = speed_raw * 0.25 if not speed_mult else speed_raw * 0.75 + 255 * 0.25
    vert_speed = struct.unpack("<b", m[4:5])[0] * 0.5
    lat = struct.unpack("<i", m[5:9])[0] * 1e-7
    lon = struct.unpack("<i", m[9:13])[0] * 1e-7
    geo_alt = struct.unpack("<H", m[15:17])[0] * 0.5 - 1000
    height = struct.unpack("<H", m[17:19])[0] * 0.5 - 1000
    return {
        "msg": "Location",
        "status": OP_STATUS.get(m[1] >> 4, f"0x{m[1] >> 4:x}"),
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "geo_alt_m": round(geo_alt, 1),
        "height_agl_m": round(height, 1),
        "speed_mps": round(speed, 2),
        "vert_speed_mps": round(vert_speed, 2),
        "track_deg": track,
    }


def _parse_self_id(m):
    return {"msg": "SelfID", "description": _ascii(m[2:25])}


def _parse_system(m):
    op_lat = struct.unpack("<i", m[2:6])[0] * 1e-7
    op_lon = struct.unpack("<i", m[6:10])[0] * 1e-7
    return {"msg": "System", "operator_lat": round(op_lat, 7), "operator_lon": round(op_lon, 7)}


def _parse_operator_id(m):
    return {"msg": "OperatorID", "operator_id": _ascii(m[2:22])}


_PARSERS = {0: _parse_basic_id, 1: _parse_location, 3: _parse_self_id, 4: _parse_system, 5: _parse_operator_id}


def parse_message(m):
    """Decode one 25-byte ODID message."""
    if len(m) < MESSAGE_SIZE:
        return None
    msg_type = m[0] >> 4
    parser = _PARSERS.get(msg_type)
    if parser is None:
        return {"msg": "Type2-Auth" if msg_type == 2 else f"Unknown(0x{msg_type:x})"}
    try:
        return parser(m)
    except (struct.error, IndexError):
        return None


def parse_odid_payload(data):
    """Decode the ODID payload (a message pack, or a single message)."""
    if not data:
        return []
    if (data[0] >> 4) == 0xF and len(data) >= 3:  # message pack
        single_size, count = data[1], data[2]
        if single_size == 0:
            return []
        out, off = [], 3
        for _ in range(count):
            chunk = data[off:off + single_size]
            if len(chunk) < single_size:
                break
            parsed = parse_message(chunk)
            if parsed:
                out.append(parsed)
            off += single_size
        return out
    parsed = parse_message(data[:MESSAGE_SIZE])
    return [parsed] if parsed else []


def decode_vendor_ie(info):
    """Decode a vendor-specific IE's info bytes if it is an ODID element."""
    if len(info) < 5 or info[0:3] != ODID_OUI or info[3] != ODID_VENDOR_TYPE:
        return None
    return parse_odid_payload(info[4:])


class RemoteIDMonitor:
    """Watches beacons for OpenDroneID and logs decoded drone Remote ID."""

    def __init__(self, db):
        self.db = db

    def iter_vendor_ies(self, pkt):
        try:
            from scapy.all import Dot11Beacon, Dot11Elt
        except Exception:
            return
        beacon = pkt.getlayer(Dot11Beacon)
        if beacon is None:
            return
        elt = beacon.payload
        while isinstance(elt, Dot11Elt):
            if elt.ID == 221 and getattr(elt, "info", None):
                yield bytes(elt.info)
            elt = elt.payload

    def decode(self, pkt):
        """Return a list of decoded ODID messages for a packet, or []."""
        messages = []
        for info in self.iter_vendor_ies(pkt):
            decoded = decode_vendor_ie(info)
            if decoded:
                messages.extend(decoded)
        return messages

    def process_packet(self, pkt):
        try:
            messages = self.decode(pkt)
        except Exception:
            return
        if not messages:
            return

        uas_id = next((m.get("uas_id") for m in messages if m.get("msg") == "BasicID"), None)
        loc = next((m for m in messages if m.get("msg") == "Location"), None)
        op_id = next((m.get("operator_id") for m in messages if m.get("msg") == "OperatorID"), None)

        parts = [f"UAS ID {uas_id}" if uas_id else "UAS ID unknown"]
        if loc:
            parts.append(f"at {loc['lat']},{loc['lon']} alt {loc['geo_alt_m']}m spd {loc['speed_mps']}m/s")
        if op_id:
            parts.append(f"operator {op_id}")
        self.db.log_alert("REMOTE_ID_DRONE", "OpenDroneID drone detected: " + ", ".join(parts), "warning")
