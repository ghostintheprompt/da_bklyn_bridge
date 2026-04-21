import yaml
import os
import time
from analysis import AnomalyDetector
from webhooks import WebhookManager

class AlertManager:
    def __init__(self, db, config_path):
        self.db = db
        self.config = self.load_config(config_path)
        self.anomaly_detector = AnomalyDetector(db)
        self.webhook_mgr = WebhookManager(self.config.get('discord_webhook_url'))
        self.deauth_counts = {} 
        self.scanner_threshold = 10 # Unique SSIDs probed by one MAC
        self.probes_by_mac = {}

    def load_config(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        return {
            'watched_ssids': [],
            'watched_bssids': [],
            'blocklist_macs': [],
            'deauth_threshold': 20
        }

    def check_probe(self, mac, ssid):
        # Alert on watched SSID
        if ssid in self.config.get('watched_ssids', []):
            msg = f"Device {mac} probing for watched SSID: {ssid}"
            self.db.log_alert("WATCHED_SSID_PROBE", msg, "warning")
            self.webhook_mgr.send_alert("WATCHED_SSID_PROBE", msg, "warning")

        # Scanner detection
        if mac not in self.probes_by_mac: self.probes_by_mac[mac] = set()
        self.probes_by_mac[mac].add(ssid)
        if len(self.probes_by_mac[mac]) > self.scanner_threshold:
             msg = f"MAC {mac} has probed for {len(self.probes_by_mac[mac])} unique SSIDs"
             self.db.log_alert("SCANNER_DETECTED", msg, "critical")
             self.webhook_mgr.send_alert("SCANNER_DETECTED", msg, "critical")

    def check_ap(self, bssid, ssid, rssi=None, channel=None):
        if ssid in self.config.get('watched_ssids', []):
             self.db.log_alert("WATCHED_SSID_AP", f"New AP seen for watched SSID: {ssid} ({bssid})", "warning")
        
        # Game Four: Anomaly detection
        if rssi and channel:
            if self.anomaly_detector.check_anomaly(rssi, channel):
                self.db.log_alert("ANOMALY_DETECTED", f"Unusual signal/channel profile for {ssid} ({bssid})", "info")

    def check_deauth(self, bssid):
        now = time.time()
        if bssid not in self.deauth_counts: self.deauth_counts[bssid] = []
        self.deauth_counts[bssid].append(now)
        
        # Clean old counts (last 60s)
        self.deauth_counts[bssid] = [t for t in self.deauth_counts[bssid] if now - t < 60]
        
        if len(self.deauth_counts[bssid]) > self.config.get('deauth_threshold', 20):
            self.db.log_alert("DEAUTH_ATTACK", f"Spike detected on BSSID {bssid}: {len(self.deauth_counts[bssid])} frames/min", "critical")
            # Reset count to prevent alert fatigue
            self.deauth_counts[bssid] = [] 
