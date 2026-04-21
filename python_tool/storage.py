import sqlite3
import time

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS probes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mac TEXT,
                ssid TEXT,
                rssi INTEGER,
                lat FLOAT,
                lon FLOAT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS aps (
                bssid TEXT PRIMARY KEY,
                ssid TEXT,
                channel INTEGER,
                rssi INTEGER,
                crypto TEXT,
                lat FLOAT,
                lon FLOAT,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS deauths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bssid TEXT,
                source TEXT,
                target TEXT,
                reason INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                msg TEXT,
                severity TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def log_probe(self, mac, ssid, rssi, lat=0.0, lon=0.0):
        self.cursor.execute("INSERT INTO probes (mac, ssid, rssi, lat, lon) VALUES (?, ?, ?, ?, ?)", 
                           (mac, ssid, rssi, lat, lon))
        self.conn.commit()

    def log_ap(self, bssid, ssid, channel, rssi, crypto, lat=0.0, lon=0.0):
        self.cursor.execute("""
            INSERT INTO aps (bssid, ssid, channel, rssi, crypto, lat, lon, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(bssid) DO UPDATE SET 
                ssid=excluded.ssid, 
                channel=excluded.channel, 
                rssi=excluded.rssi, 
                crypto=excluded.crypto,
                lat=excluded.lat,
                lon=excluded.lon,
                last_seen=CURRENT_TIMESTAMP
        """, (bssid, ssid, channel, rssi, crypto, lat, lon))
        self.conn.commit()

    def log_deauth(self, bssid, source, target, reason):
        self.cursor.execute("INSERT INTO deauths (bssid, source, target, reason) VALUES (?, ?, ?, ?)", 
                           (bssid, source, target, reason))
        self.conn.commit()

    def log_alert(self, alert_type, msg, severity="info"):
        self.cursor.execute("INSERT INTO alerts (type, msg, severity) VALUES (?, ?, ?)", 
                           (alert_type, msg, severity))
        self.conn.commit()

    # Game Four: The Time-Lapse Queries
    def get_night_owls(self):
        """Networks that only appear between midnight and 5am"""
        self.cursor.execute("""
            SELECT ssid, bssid, MIN(last_seen) as appeared, COUNT(*) as beacon_count
            FROM aps
            WHERE strftime('%H', last_seen) BETWEEN '00' AND '04'
            GROUP BY bssid
            ORDER BY beacon_count DESC
        """)
        return self.cursor.fetchall()

    def get_ghost_networks(self):
        """Networks seen once and never again"""
        # Logic: last_seen close to first_seen (in a real log we'd need multiple entries, 
        # but for this schema we can simulate with a count of updates if we had it. 
        # For now, let's just return a placeholder)
        self.cursor.execute("SELECT ssid, bssid, last_seen FROM aps WHERE last_seen < datetime('now', '-1 day')")
        return self.cursor.fetchall()

    def get_recent_aps(self, limit=20):
        self.cursor.execute("SELECT * FROM aps ORDER BY last_seen DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_recent_probes(self, limit=20):
        self.cursor.execute("SELECT * FROM probes ORDER BY timestamp DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_recent_alerts(self, limit=10):
        self.cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()
