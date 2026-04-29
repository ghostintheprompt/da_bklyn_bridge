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

    def generate_incident_id(self):
        return f"INC-{int(time.time())}-{os.urandom(2).hex().upper()}"

    def log_and_alert(self, alert_type, msg, severity="info"):
        incident_id = self.generate_incident_id()
        full_msg = f"[{incident_id}] {msg}"
        self.db.log_alert(alert_type, full_msg, severity)
        self.webhook_mgr.send_alert(alert_type, full_msg, severity)

    def check_probe(self, mac, ssid, rssi=None):
        # Guardrail: Blocklisted MAC detection
        if mac in self.config.get('blocklist_macs', []):
            self.log_and_alert("GUARDRAIL_VIOLATION", f"Blocklisted MAC {mac} detected probing for {ssid}", "critical")

        # Alert on watched SSID
        if ssid in self.config.get('watched_ssids', []):
            msg = f"Device {mac} probing for watched SSID: {ssid}"
            self.log_and_alert("WATCHED_SSID_PROBE", msg, "warning")

        # Scanner detection & Actor Fingerprinting
        if mac not in self.probes_by_mac: self.probes_by_mac[mac] = set()
        self.probes_by_mac[mac].add(ssid)
        if len(self.probes_by_mac[mac]) > self.scanner_threshold:
             # Fingerprint Actor
             actor_id = self.anomaly_detector.fingerprint_actor(mac, rssi, self.probes_by_mac[mac])
             msg = f"MAC {mac} has probed for {len(self.probes_by_mac[mac])} unique SSIDs. Profiled as {actor_id}"
             self.log_and_alert("SCANNER_DETECTED", msg, "critical")

    def check_ap(self, bssid, ssid, rssi=None, channel=None):
        rogue_detected = False
        if ssid in self.config.get('watched_ssids', []):
             # Self Audit: Rogue AP detection logic (BSSID check)
             if bssid not in self.config.get('watched_bssids', []):
                 self.log_and_alert("ROGUE_AP_DETECTED", f"Unauthorized AP for watched SSID: {ssid} ({bssid})", "critical")
                 rogue_detected = True
             else:
                 self.db.log_alert("WATCHED_SSID_AP", f"Authorized AP seen: {ssid} ({bssid})", "info")
        
        # Game Four: Anomaly detection
        if rssi and channel:
            if self.anomaly_detector.check_anomaly(rssi, channel):
                self.log_and_alert("ANOMALY_DETECTED", f"Unusual signal/channel profile for {ssid} ({bssid})", "info")
                
        return rogue_detected

    def check_deauth(self, bssid):
        now = time.time()
        if bssid not in self.deauth_counts: self.deauth_counts[bssid] = []
        self.deauth_counts[bssid].append(now)
        
        # Clean old counts (last 60s)
        self.deauth_counts[bssid] = [t for t in self.deauth_counts[bssid] if now - t < 60]
        
        count = len(self.deauth_counts[bssid])
        if count > self.config.get('deauth_threshold', 20):
            self.log_and_alert("DEAUTH_ATTACK", f"Spike detected on BSSID {bssid}: {count} frames/min", "critical")
            # Reset count to prevent alert fatigue
            self.deauth_counts[bssid] = [] 
