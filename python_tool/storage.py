try:
    from pysqlcipher3 import dbapi2 as sqlite3
    SQLCIPHER_AVAILABLE = True
except ImportError:
    # Fallback to standard sqlite3 if cipher is not installed.
    # This is acceptable for local lab replay, but not for trusted evidence.
    import sqlite3
    SQLCIPHER_AVAILABLE = False

import time
import os
import yaml

class Database:
    def __init__(self, db_path, key=None):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        key = key or os.environ.get("SENTINEL_DB_KEY")
        allow_insecure = os.environ.get("SENTINEL_ALLOW_INSECURE_DB") == "1"

        if SQLCIPHER_AVAILABLE:
            if not key:
                if not allow_insecure:
                    raise RuntimeError(
                        "SENTINEL_DB_KEY is required when SQLCipher is available. "
                        "Set SENTINEL_ALLOW_INSECURE_DB=1 only for local lab replay."
                    )
                print("[!] WARNING: SQLCipher available but DB encryption key is not set. Local lab mode only.")
            else:
                try:
                    escaped_key = key.replace("'", "''")
                    self.cursor.execute(f"PRAGMA key='{escaped_key}'")
                    self.cursor.execute("SELECT count(*) FROM sqlite_master;")
                except sqlite3.DatabaseError as exc:
                    raise RuntimeError("Database decryption failed. Incorrect key or corrupt file.") from exc
        elif not allow_insecure:
            print("[!] WARNING: SQLCipher unavailable. Evidence DB is not encrypted at rest.")
            
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

    # Game Five: Self Audit & Rogue AP Detection
    def get_rogue_aps(self, authorized_bssids):
        """Identify APs broadcasting watched SSIDs with unauthorized BSSIDs"""
        if not authorized_bssids:
            return []
        authorized_bssids = [bssid.upper() for bssid in authorized_bssids]
        placeholders = ', '.join(['?'] * len(authorized_bssids))
        query = f"""
            SELECT ssid, bssid, channel, rssi, crypto 
            FROM aps 
            WHERE UPPER(bssid) NOT IN ({placeholders})
            AND (ssid IN (SELECT DISTINCT ssid FROM aps WHERE UPPER(bssid) IN ({placeholders})))
        """
        self.cursor.execute(query, authorized_bssids + authorized_bssids)
        return self.cursor.fetchall()

    def get_night_owls(self):
        """Networks that only appear between midnight and 5am"""
        self.cursor.execute("""
            SELECT ssid, bssid, last_seen, rssi
            FROM aps
            WHERE strftime('%H', last_seen) BETWEEN '00' AND '04'
            ORDER BY last_seen DESC
        """)
        return self.cursor.fetchall()

    def get_ghost_networks(self):
        """Networks seen once and never again (conceptual filter)"""
        self.cursor.execute("""
            SELECT ssid, bssid, last_seen, rssi
            FROM aps 
            WHERE last_seen < datetime('now', '-1 hour')
            LIMIT 20
        """)
        return self.cursor.fetchall()

    def get_deauth_stats(self):
        """Get summary of recent deauth activity"""
        self.cursor.execute("""
            SELECT bssid, COUNT(*) as spike_count, MAX(timestamp) as last_spike
            FROM deauths
            WHERE timestamp > datetime('now', '-10 minutes')
            GROUP BY bssid
            ORDER BY spike_count DESC
        """)
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
