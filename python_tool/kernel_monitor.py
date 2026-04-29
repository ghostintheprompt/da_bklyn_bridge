import subprocess
import threading
import time

class KernelMonitor:
    def __init__(self, interface, alert_mgr):
        self.interface = interface
        self.alert_mgr = alert_mgr
        self.stop_event = threading.Event()
        self.is_monitoring = False
        
    def _check_driver_status(self):
        """
        Phase 4: Kernel-Level Integrity Monitoring
        Detects if the rtl8812au driver drops out of monitor mode silently,
        indicating a potential kernel-level hook or rogue persistence mechanism.
        """
        try:
            # Check the mode of the interface using iw
            result = subprocess.run(['iw', 'dev', self.interface, 'info'], capture_output=True, text=True, check=True)
            if "type monitor" not in result.stdout:
                return False
            return True
        except Exception:
            return False

    def _monitor_loop(self):
        while not self.stop_event.is_set():
            time.sleep(10) # Heartbeat interval
            if not self._check_driver_status():
                self.alert_mgr.log_and_alert(
                    "KERNEL_HOOK_SUSPECTED", 
                    f"Driver heartbeat failed! Interface {self.interface} dropped from monitor mode silently. Potential kernel tampering.", 
                    "critical"
                )
                
                # Attempt to auto-remediate
                try:
                    subprocess.run(["ip", "link", "set", self.interface, "down"], check=False)
                    subprocess.run(["iw", "dev", self.interface, "set", "monitor", "none"], check=False)
                    subprocess.run(["ip", "link", "set", self.interface, "up"], check=False)
                    self.alert_mgr.log_and_alert("DRIVER_REMEDIATED", f"Attempted to force {self.interface} back to monitor mode.", "warning")
                except:
                    pass
                
                # Pause alerts to prevent spam while down
                time.sleep(30)

    def start(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
