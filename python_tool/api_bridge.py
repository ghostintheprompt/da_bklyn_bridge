from flask import Flask, jsonify
from flask_cors import CORS
from storage import Database
import os

import argparse

parser = argparse.ArgumentParser(description="Da Bklyn Bridge API Bridge")
parser.add_argument("-i", "--interface", default="wlan0mon", help="Wireless interface name")
args = parser.parse_args()

app = Flask(__name__)
CORS(app) # Allow React dashboard to connect
db = Database("sentinel.db")

@app.route('/api/stats')
def get_stats():
    # Return real data from local SQLite
    aps = db.get_recent_aps(limit=20)
    probes = db.get_recent_probes(limit=20)
    alerts = db.get_recent_alerts(limit=10)
    
    return jsonify({
        "interface": args.interface,
        "mode": "Monitor",
        "channel": 1, # Placeholder for current hopping channel
        "aps": [{"bssid": a[0], "ssid": a[1], "channel": a[2], "rssi": a[3], "crypto": a[4], "lastSeen": a[5]} for a in aps],
        "probes": [{"mac": p[1], "ssid": p[2], "rssi": p[3], "timestamp": p[4]} for p in probes],
        "alerts": [{"type": al[1], "msg": al[2], "severity": al[3], "timestamp": al[4]} for al in alerts]
    })

if __name__ == '__main__':
    # Run on a different port to not conflict with web dev servers
    app.run(host='0.0.0.0', port=5000)
