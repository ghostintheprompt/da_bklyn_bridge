from scapy.all import Dot11Beacon, Dot11

class RemoteIDMonitor:
    """
    Experimental monitor for Drone Remote ID (ASTM F3411 / ASD-STAN 4709-002)
    broadcasted over Wi-Fi Beacons or OUI-specific vendor tags.
    """
    def __init__(self, db):
        self.db = db

    def iter_vendor_tags(self, pkt):
        elt = pkt.getlayer(Dot11Beacon).payload
        while hasattr(elt, 'ID'):
            if elt.ID == 221 and getattr(elt, "info", None):
                info = bytes(elt.info)
                if len(info) >= 3:
                    oui = ":".join(f"{byte:02X}" for byte in info[:3])
                    yield oui, info[3:]
            elt = elt.payload

    def parse_remote_id_marker(self, pkt):
        bssid = pkt.addr3.upper() if isinstance(pkt.addr3, str) else pkt.addr3
        for oui, payload in self.iter_vendor_tags(pkt):
            upper_payload = payload.upper()
            if b"REMOTEID" in upper_payload or b"OPENDRONEID" in upper_payload:
                return {
                    "bssid": bssid,
                    "oui": oui,
                    "payload_len": len(payload),
                    "marker": "OpenDroneID" if b"OPENDRONEID" in upper_payload else "RemoteID",
                }
        return None

    def process_packet(self, pkt):
        if not pkt.haslayer(Dot11Beacon):
            return

        # Remote ID can appear in vendor-specific management-frame elements.
        # This parser extracts tag structure and flags recognizable lab markers.
        try:
            marker = self.parse_remote_id_marker(pkt)
            if marker:
                self.db.log_alert(
                    "REMOTE_ID_DRONE",
                    f"{marker['marker']} beacon marker detected from {marker['bssid']} via OUI {marker['oui']} ({marker['payload_len']} bytes)",
                    "warning",
                )
        except Exception:
            pass
