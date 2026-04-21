import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np

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
