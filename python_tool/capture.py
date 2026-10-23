import threading
import time
from scapy.all import sniff, Dot11, Dot11ProbeReq, Dot11Beacon, Dot11Deauth, Dot11Elt, EAPOL
from scapy.all import conf
from active_mitigation import ActiveMitigation
import math


def normalize_mac(mac):
    return mac.upper() if isinstance(mac, str) else mac


class PacketCapturer:
    def __init__(self, interface, db, alert_mgr, gps_logger=None):
        self.interface = interface
        self.db = db
        self.alert_mgr = alert_mgr
        self.gps_logger = gps_logger
        self.stop_event = threading.Event()
        self.channels_24 = list(range(1, 14))
        self.channels_5 = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]
        self.all_channels = self.channels_24 + self.channels_5
        self.current_channel = 1
        
        # Phase 4: Active Mitigation (Bridge Mode)
        self.mitigator = ActiveMitigation(interface, db, alert_mgr)

    def extract_ssid(self, pkt):
        """Extract SSID from the first 802.11 SSID information element."""
        elt = pkt.getlayer(Dot11Elt)
        while elt is not None and hasattr(elt, "ID"):
            if elt.ID == 0:
                try:
                    return elt.info.decode("utf-8", errors="replace") or "<Hidden>"
                except Exception:
                    return "<Hidden>"
            elt = elt.payload
        return "<Hidden>"

    def calculate_entropy(self, data):
        """Calculate Shannon entropy of a byte string."""
        if not data:
            return 0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(bytes([x]))) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

    def channel_hopper(self):
        while not self.stop_event.is_set():
            for ch in self.all_channels:
                if self.stop_event.is_set(): break
                try:
                    import subprocess
                    subprocess.run(["iw", "dev", self.interface, "set", "channel", str(ch)], check=False)
                    self.current_channel = ch
                except:
                    pass
                time.sleep(2) # Dwell time

    def packet_callback(self, pkt):
        if not pkt.haslayer(Dot11):
            return

        lat, lon = (0.0, 0.0)
        if self.gps_logger:
            lat, lon = self.gps_logger.get_coords()

        # 1. Probe Request Logger & Actor Fingerprinting
        if pkt.haslayer(Dot11ProbeReq):
            client_mac = normalize_mac(pkt.addr2)
            ssid = self.extract_ssid(pkt)
            rssi = self.get_rssi(pkt)
            self.db.log_probe(client_mac, ssid, rssi, lat, lon)
            
            # Phase 4: Actor Correlation (Signal Fingerprinting)
            # This logic leverages analysis.py conceptually via alert_mgr
            self.alert_mgr.check_probe(client_mac, ssid, rssi)

        # 2. AP Scanner (Beacons) & Covert Channel Detection
        elif pkt.haslayer(Dot11Beacon):
            bssid = normalize_mac(pkt.addr3)
            ssid = self.extract_ssid(pkt)
            
            stats = pkt.getlayer(Dot11Beacon).network_stats()
            channel = stats.get('channel')
            crypto = "/".join(stats.get('crypto'))
            
            # 2026 Detection & Covert Channel Audit
            protocol = "802.11ac" # Default
            elt = pkt.getlayer(Dot11Beacon).payload
            while hasattr(elt, 'ID'):
                if elt.ID == 255: # Extension Tag
                    try:
                        ext_id = elt.info[0]
                        if ext_id in [35, 36]: protocol = "Wi-Fi 6 (HE)"
                        elif ext_id == 108: protocol = "Wi-Fi 7 (EHT)"
                    except: pass
                # Phase 4: Covert Channel Audit (Vendor Specific Tags)
                elif elt.ID == 221: # Vendor Specific
                    try:
                        entropy = self.calculate_entropy(elt.info)
                        # High entropy (approaching 8.0) suggests encryption/compression (potential exfiltration)
                        if entropy > 7.5:
                            self.alert_mgr.log_and_alert("COVERT_CHANNEL_SUSPECTED", f"High entropy vendor tag ({entropy:.2f}) found on {bssid}. Possible exfiltration.", "critical")
                    except: pass
                elt = elt.payload

            rssi = self.get_rssi(pkt)
            self.db.log_ap(bssid, ssid, channel, rssi, f"{protocol} {crypto}", lat, lon)
            
            # Trigger mitigation logic during check_ap
            rogue_detected = self.alert_mgr.check_ap(bssid, ssid, rssi, channel)
            if rogue_detected and self.mitigator.bridge_mode_enabled:
                self.mitigator.execute_targeted_deauth(bssid)
                
        # 4. WPA Handshake (EAPOL) Detection
        elif pkt.haslayer(EAPOL):
            bssid = normalize_mac(pkt[Dot11].addr3)
            src = normalize_mac(pkt[Dot11].addr2)
            self.alert_mgr.log_and_alert("WPA_HANDSHAKE", f"EAPOL handshake frame captured for BSSID {bssid} from {src}", "info")

        # 3. Deauth Detector
        elif pkt.haslayer(Dot11Deauth):
            target = normalize_mac(pkt.addr1)
            source = normalize_mac(pkt.addr2)
            bssid = normalize_mac(pkt.addr3)
            reason = pkt.reason
            self.db.log_deauth(bssid, source, target, reason)
            self.alert_mgr.check_deauth(bssid)

    def get_rssi(self, pkt):
        try:
            return int(getattr(pkt, "dBm_AntSignal"))
        except Exception:
            pass
        return -100 # Fallback

    def start(self):
        self.hop_thread = threading.Thread(target=self.channel_hopper, daemon=True)
        self.hop_thread.start()
        
        # Sniffing in a separate thread to not block main
        self.sniff_thread = threading.Thread(target=self._run_sniff, daemon=True)
        self.sniff_thread.start()

    def _run_sniff(self):
        sniff(iface=self.interface, prn=self.packet_callback, store=0, stop_filter=lambda x: self.stop_event.is_set())

    def stop(self):
        self.stop_event.set()
