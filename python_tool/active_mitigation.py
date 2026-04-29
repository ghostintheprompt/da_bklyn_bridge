import subprocess
import time

class ActiveMitigation:
    def __init__(self, interface, db, alert_mgr):
        self.interface = interface
        self.db = db
        self.alert_mgr = alert_mgr
        self.bridge_mode_enabled = False # Must be explicitly enabled in config
        
    def enable(self):
        self.bridge_mode_enabled = True
        self.alert_mgr.log_and_alert("BRIDGE_MODE_ENGAGED", "Active mitigation (Deauth) is now ARMED.", "warning")

    def execute_targeted_deauth(self, bssid, client_mac="FF:FF:FF:FF:FF:FF", reason=7):
        """
        Phase 4: Active Perimeter Defense (The "Bridge" Logic)
        Executes a targeted deauthentication attack against a specific BSSID or Client.
        Requires 'aireplay-ng'.
        """
        if not self.bridge_mode_enabled:
            return False

        self.alert_mgr.log_and_alert("ACTIVE_MITIGATION", f"Executing targeted deauth against BSSID: {bssid}, Target: {client_mac}", "critical")
        
        try:
            # aireplay-ng -0 <count> -a <bssid> -c <client> <interface>
            cmd = ["aireplay-ng", "-0", "5", "-a", bssid, "-c", client_mac, self.interface]
            # We run this in the background so it doesn't block the main thread
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            self.alert_mgr.log_and_alert("MITIGATION_FAILED", f"Failed to execute aireplay-ng: {e}", "warning")
            return False
