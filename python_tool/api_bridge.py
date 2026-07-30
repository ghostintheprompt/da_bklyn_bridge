import os
import yaml
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from storage import Database
from analysis import AnomalyDetector
from vendors import resolve_vendor

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                origin.strip()
                for origin in os.environ.get(
                    "SENTINEL_CORS_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173"
                ).split(",")
                if origin.strip()
            ]
        }
    },
)
db = Database("sentinel.db")

def require_api_token():
    token = os.environ.get("SENTINEL_API_TOKEN")
    if not token:
        return
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {token}":
        abort(401)

def load_runtime_config(config_path="config.yaml"):
    interface = "wlan0" # Default
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
            interface = config.get('interface', interface)
    return config, interface


def build_stats(config_path="config.yaml"):
    config, interface = load_runtime_config(config_path)

    aps = db.get_recent_aps(limit=50)
    probes = db.get_recent_probes(limit=50)
    alerts = db.get_recent_alerts(limit=10)
    night_owls = db.get_night_owls()
    ghosts = db.get_ghost_networks()
    deauth_stats = db.get_deauth_stats()
    authorized_bssids = config.get('watched_bssids', [])
    rogue_aps = db.get_rogue_aps(authorized_bssids) if authorized_bssids else []
    anomaly_status = AnomalyDetector(db).status()
    active_alerts = [alert for alert in alerts if alert[3] in {"warning", "critical"}]

    return {
        "interface": interface,
        "mode": config.get("operation_mode", "passive"),
        "channel": 1,  # Placeholder for current channel
        "summary": {
            "ap_count": len(aps),
            "probe_count": len(probes),
            "alert_count": len(alerts),
            "active_alert_count": len(active_alerts),
            "rogue_ap_count": len(rogue_aps),
            "deauth_group_count": len(deauth_stats),
            "night_owl_count": len(night_owls),
            "ghost_network_count": len(ghosts),
            "remote_id_alert_count": sum(1 for alert in alerts if alert[1] == "REMOTE_ID_DRONE"),
        },
        "aps": [
            {
                "bssid": a[0],
                "ssid": a[1],
                "channel": a[2],
                "rssi": a[3],
                "crypto": a[4],
                "vendor": resolve_vendor(a[0]),
                "lastSeen": a[7],
            }
            for a in aps
        ],
        "probes": [{"mac": p[1], "ssid": p[2], "rssi": p[3], "timestamp": p[6]} for p in probes],
        "alerts": [{"type": al[1], "msg": al[2], "severity": al[3], "timestamp": al[4]} for al in alerts],
        "timelapse": {
            "night_owls": [{"ssid": n[0], "bssid": n[1], "time": n[2]} for n in night_owls],
            "ghosts": [{"ssid": g[0], "bssid": g[1], "time": g[2]} for g in ghosts]
        },
        "deauth_stats": [{"bssid": d[0], "count": d[1], "last": d[2]} for d in deauth_stats],
        "rogue_aps": [{"ssid": r[0], "bssid": r[1], "channel": r[2], "rssi": r[3], "crypto": r[4]} for r in rogue_aps],
        "anomaly_model": anomaly_status,
    }


@app.route('/api/health')
def get_health():
    require_api_token()
    config, interface = load_runtime_config()
    return jsonify({
        "status": "ok",
        "interface": interface,
        "mode": config.get("operation_mode", "passive"),
        "api_host": os.environ.get("SENTINEL_API_HOST", "127.0.0.1"),
        "token_required": bool(os.environ.get("SENTINEL_API_TOKEN")),
    })


@app.route('/api/stats')
def get_stats():
    require_api_token()
    stats = build_stats()
    return jsonify(stats)

if __name__ == '__main__':
    host = os.environ.get("SENTINEL_API_HOST", "127.0.0.1")
    port = int(os.environ.get("SENTINEL_API_PORT", "5000"))
    app.run(host=host, port=port)
