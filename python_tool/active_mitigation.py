import subprocess
import time

class ActiveMitigation:
    def __init__(self, interface, db, alert_mgr):
        self.interface = interface
        self.db = db
        self.alert_mgr = alert_mgr
        self.bridge_mode_enabled = False
        self.config = alert_mgr.config or {}
        self.mitigation_config = self.config.get("active_mitigation", {})

    def _allowed_bssids(self):
        return set(
            bssid.upper()
            for bssid in (
                self.mitigation_config.get("allowed_bssids", [])
                or self.config.get("authorized_lab_bssids", [])
                or []
            )
            if isinstance(bssid, str)
        )

    def _safety_gate_ok(self):
        if self.config.get("operation_mode") != "lab":
            return False, "operation_mode must be 'lab'"
        if not self.config.get("trusted_access_ack"):
            return False, "trusted_access_ack must be true"
        if not self.mitigation_config.get("enabled"):
            return False, "active_mitigation.enabled must be true"
        if not self._allowed_bssids():
            return False, "at least one active_mitigation.allowed_bssid is required"
        return True, "ok"
        
    def enable(self):
        ok, reason = self._safety_gate_ok()
        if not ok:
            self.alert_mgr.log_and_alert(
                "BRIDGE_MODE_REFUSED",
                f"Active mitigation refused by safety gate: {reason}",
                "warning"
            )
            return False
        self.bridge_mode_enabled = True
        self.alert_mgr.log_and_alert("BRIDGE_MODE_ENGAGED", "Active mitigation (Deauth) is now ARMED.", "warning")
        return True

    def execute_targeted_deauth(self, bssid, client_mac="FF:FF:FF:FF:FF:FF", reason=7):
        """
        Phase 4: Active Perimeter Defense (The "Bridge" Logic)
        Executes a targeted deauthentication attack against a specific BSSID or Client.
        Requires 'aireplay-ng'.
        """
        if not self.bridge_mode_enabled:
            return False

        bssid = bssid.upper() if isinstance(bssid, str) else bssid
        client_mac = client_mac.upper() if isinstance(client_mac, str) else client_mac
        allowed = self._allowed_bssids()
        if bssid not in allowed:
            self.alert_mgr.log_and_alert(
                "MITIGATION_BLOCKED",
                f"Refused deauth for BSSID outside allowed lab list: {bssid}",
                "critical"
            )
            return False

        if client_mac == "FF:FF:FF:FF:FF:FF" and not self.mitigation_config.get("allow_broadcast_client"):
            self.alert_mgr.log_and_alert(
                "MITIGATION_BLOCKED",
                "Refused broadcast-client deauth. Set active_mitigation.allow_broadcast_client only in isolated lab scope.",
                "critical"
            )
            return False

        self.alert_mgr.log_and_alert("ACTIVE_MITIGATION", f"Executing targeted deauth against BSSID: {bssid}, Target: {client_mac}", "critical")
        
        try:
            # aireplay-ng -0 <count> -a <bssid> -c <client> <interface>
            count = str(min(int(self.mitigation_config.get("frame_count", 1)), 5))
            cmd = ["aireplay-ng", "-0", count, "-a", bssid, "-c", client_mac, self.interface]
            # We run this in the background so it doesn't block the main thread
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            self.alert_mgr.log_and_alert("MITIGATION_FAILED", f"Failed to execute aireplay-ng: {e}", "warning")
            return False
