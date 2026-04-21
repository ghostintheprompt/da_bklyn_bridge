import requests
import json

class WebhookManager:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_alert(self, alert_type, msg, severity="info"):
        if not self.webhook_url:
            return

        color = 3447003 # Blue
        if severity == "critical":
            color = 15158332 # Red
        elif severity == "warning":
            color = 16776960 # Yellow

        payload = {
            "embeds": [{
                "title": f"Wireless Sentinel Alert: {alert_type}",
                "description": msg,
                "color": color,
                "footer": {"text": "Sent via Wireless Sentinel Engine"}
            }]
        }

        try:
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"[!] Failed to send Discord webhook: {e}")
