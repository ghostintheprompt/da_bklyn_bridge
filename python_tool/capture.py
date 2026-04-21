import threading
import time
import random
from scapy.all import sniff, Dot11, Dot11ProbeReq, Dot11Beacon, Dot11Deauth, EAPOL
from scapy.all import conf

class PacketCapturer:
    def __init__(self, interface, db, alert_mgr, remote_id=None, gps_logger=None):
        self.interface = interface
        self.db = db
        self.alert_mgr = alert_mgr
        self.remote_id = remote_id
        self.gps_logger = gps_logger
        self.stop_event = threading.Event()
        self.channels_24 = list(range(1, 14))
        self.channels_5 = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]
        self.all_channels = self.channels_24 + self.channels_5
        self.current_channel = 1

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

        # 1. Probe Request Logger
        if pkt.haslayer(Dot11ProbeReq):
            client_mac = pkt.addr2
            try:
                ssid = pkt.info.decode('utf-8')
            except:
                ssid = "<Hidden>"
            rssi = self.get_rssi(pkt)
            self.db.log_probe(client_mac, ssid, rssi, lat, lon)
            self.alert_mgr.check_probe(client_mac, ssid)

        # 2. AP Scanner (Beacons)
        elif pkt.haslayer(Dot11Beacon):
            bssid = pkt.addr3
            try:
                ssid = pkt.info.decode('utf-8')
            except:
                ssid = "<Hidden>"
            
            stats = pkt.getlayer(Dot11Beacon).network_stats()
            channel = stats.get('channel')
            crypto = "/".join(stats.get('crypto'))
            
            # 2026 Detection: Wi-Fi 6 (HE) and Wi-Fi 7 (EHT)
            # We check the tag ID 255 (Extension) in the beacon elements
            protocol = "802.11ac" # Default for this adapter range
            elt = pkt.getlayer(Dot11Beacon).payload
            while hasattr(elt, 'ID'):
                if elt.ID == 255: # Extension Tag
                    try:
                        ext_id = elt.info[0]
                        if ext_id in [35, 36]: protocol = "Wi-Fi 6 (HE)"
                        elif ext_id == 108: protocol = "Wi-Fi 7 (EHT)"
                    except: pass
                elt = elt.payload

            rssi = self.get_rssi(pkt)
            self.db.log_ap(bssid, ssid, channel, rssi, f"{protocol} {crypto}", lat, lon)
            self.alert_mgr.check_ap(bssid, ssid, rssi, channel)
            if self.remote_id:
                self.remote_id.process_packet(pkt)

        # 4. WPA Handshake (EAPOL) Detection
        elif pkt.haslayer(EAPOL):
            bssid = pkt[Dot11].addr3
            src = pkt[Dot11].addr2
            self.alert_mgr.db.log_alert("WPA_HANDSHAKE", f"EAPOL handshake frame captured for BSSID {bssid} from {src}", "info")

        # 3. Deauth Detector
        elif pkt.haslayer(Dot11Deauth):
            target = pkt.addr1
            source = pkt.addr2
            bssid = pkt.addr3
            reason = pkt.reason
            self.db.log_deauth(bssid, source, target, reason)
            self.alert_mgr.check_deauth(bssid)

    def get_rssi(self, pkt):
        if pkt.haslayer(conf.L2listen): # Radiotap
            try:
                return pkt.dBm_AntSignal
            except:
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
