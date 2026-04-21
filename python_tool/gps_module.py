try:
    from gps import *
    import threading
except ImportError:
    pass

class GPSLogger:
    """
    Interfaces with gpsd to provide live lat/lon telemetry.
    Requires 'gpsd' and 'python3-gps' on the host.
    """
    def __init__(self):
        self.coords = (0.0, 0.0)
        self.running = False
        try:
            self.session = gps(mode=WATCH_ENABLE)
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
        except:
            print("[!] gpsd not found or GPS module disconnected. Geo-logging disabled.")

    def _update(self):
        while self.running:
            report = self.session.next()
            if report['class'] == 'TPV':
                self.coords = (getattr(report, 'lat', 0.0), getattr(report, 'lon', 0.0))

    def get_coords(self):
        return self.coords
