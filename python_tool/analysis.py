import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np
import math

class AnomalyDetector:
    def __init__(self, db):
        self.db = db
        self.clf = IsolationForest(contamination=0.05, random_state=42)
        self.is_trained = False

    def train_baseline(self):
        # Fetch AP and Probe data for training
        query = """
            SELECT rssi, channel FROM aps
            UNION ALL
            SELECT rssi, CASE WHEN id % 2 == 0 THEN 1 ELSE 6 END as channel FROM probes
        """
        df = pd.read_sql_query(query, self.db.conn)
        
        if len(df) < 20: 
            return # Not enough data
        
        self.clf.fit(df[['rssi', 'channel']])
        self.is_trained = True
        return "[+] Baseline anomaly detection model trained."

    def check_anomaly(self, rssi, channel):
        if not self.is_trained:
            return False
            
        pred = self.clf.predict([[rssi, channel]])
        return pred[0] == -1 # Returns True if outlier

    # Phase 4: Actor Correlation (Signal Physics Fingerprinting)
    def calculate_entropy(self, data):
        """Calculate Shannon entropy of a byte string to detect encrypted/compressed payloads."""
        if not data:
            return 0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(bytes([x]))) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

    def fingerprint_actor(self, mac, rssi, probed_ssids):
        """
        Attempts to correlate a MAC address (even if randomized) to a profile
        based on signal strength stability and preferred network lists.
        """
        # In a full implementation, this would cluster MACs with similar RSSI variance 
        # and identical probed_ssids over time, assigning a persistent 'Actor ID'.
        # For now, we return a hash of the sorted SSIDs as a basic fingerprint.
        if not probed_ssids:
            return "UNKNOWN_ACTOR"
        
        fingerprint_source = "".join(sorted(list(probed_ssids)))
        import hashlib
        return f"ACTOR-{hashlib.md5(fingerprint_source.encode()).hexdigest()[:8].upper()}"

