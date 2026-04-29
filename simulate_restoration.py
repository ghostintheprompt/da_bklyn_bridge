import sqlite3
import time
import os

# Connect to the restored database
db_path = "sentinel.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def simulate_event(alert_type, msg, severity):
    incident_id = f"INC-{int(time.time())}-SIM"
    full_msg = f"[{incident_id}] {msg}"
    cursor.execute("INSERT INTO alerts (type, msg, severity) VALUES (?, ?, ?)", 
                  (alert_type, full_msg, severity))
    conn.commit()
    print(f"[+] Simulated Restoration Event: {full_msg}")

# 1. Simulate Rogue AP Detection (s5)
simulate_event("ROGUE_AP_DETECTED", "Unauthorized AP for watched SSID: Home_WiFi (DE:AD:BE:EF:CA:FE)", "critical")

# 2. Simulate Temporal Anomaly (s4)
try:
    cursor.execute("INSERT INTO aps (bssid, ssid, last_seen, channel, rssi, crypto) VALUES (?, ?, ?, ?, ?, ?)",
                  ("00:11:22:33:44:55", "Night_Owl_GND", "2026-04-29 02:00:00", 6, -75, "WPA2"))
    conn.commit()
    print("[+] Simulated Night Owl Network entry.")
except sqlite3.IntegrityError:
    print("[*] Night Owl Network entry already exists.")

# 3. Simulate Deauth Attack (s3)
cursor.execute("INSERT INTO deauths (bssid, source, target, reason) VALUES (?, ?, ?, ?)",
              ("AA:BB:CC:DD:EE:FF", "SP-OO-FE-RR", "TA-RG-ET", 7))
conn.commit()
print("[+] Simulated Deauth Spike entry.")

conn.close()
