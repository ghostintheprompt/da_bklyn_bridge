import hashlib
import json
import math
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path

try:
    import pandas as pd
    from sklearn.ensemble import IsolationForest
    ML_AVAILABLE = True
except ImportError:
    pd = None
    IsolationForest = None
    ML_AVAILABLE = False


FEATURE_NAMES = ["rssi", "channel"]


class AnomalyDetector:
    def __init__(self, db, model_dir=None):
        self.db = db
        configured_dir = model_dir or os.environ.get("SENTINEL_MODEL_DIR")
        self.model_dir = Path(configured_dir) if configured_dir else Path(__file__).resolve().parent / "models"
        self.model_path = self.model_dir / "anomaly_model.pkl"
        self.metadata_path = self.model_dir / "anomaly_metadata.json"
        self.clf = IsolationForest(contamination=0.05, random_state=42) if ML_AVAILABLE else None
        self.is_trained = False
        self.metadata = self._default_metadata()
        self.load_model()

    def _default_metadata(self):
        return {
            "status": "untrained" if ML_AVAILABLE else "ml_unavailable",
            "ml_available": ML_AVAILABLE,
            "feature_names": FEATURE_NAMES,
            "trained_at": None,
            "sample_count": 0,
            "contamination": None,
            "data_sha256": None,
            "model_path": str(self.model_path),
        }

    def _fetch_training_frame(self):
        query = """
            SELECT rssi, channel FROM aps
            WHERE rssi IS NOT NULL AND channel IS NOT NULL
            UNION ALL
            SELECT rssi, CASE WHEN id % 2 == 0 THEN 1 ELSE 6 END as channel FROM probes
            WHERE rssi IS NOT NULL
        """
        df = pd.read_sql_query(query, self.db.conn)
        return df.dropna(subset=FEATURE_NAMES)

    def _data_hash(self, df):
        payload = df[FEATURE_NAMES].to_csv(index=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _write_metadata(self):
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path.write_text(json.dumps(self.metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def load_model(self):
        if not ML_AVAILABLE:
            return False
        if self.metadata_path.exists():
            try:
                self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.metadata = self._default_metadata()
                self.metadata["status"] = "metadata_unreadable"
        if self.model_path.exists():
            try:
                with self.model_path.open("rb") as handle:
                    self.clf = pickle.load(handle)
                self.is_trained = True
                if self.metadata.get("status") in {"untrained", "metadata_unreadable"}:
                    self.metadata["status"] = "loaded_without_metadata"
                return True
            except (OSError, pickle.PickleError, EOFError):
                self.is_trained = False
                self.metadata["status"] = "model_unreadable"
        return False

    def status(self):
        status = dict(self.metadata)
        status["loaded"] = bool(self.is_trained)
        status["model_exists"] = self.model_path.exists()
        status["metadata_exists"] = self.metadata_path.exists()
        return status

    def train_baseline(self, min_samples=20, contamination=0.05):
        if not ML_AVAILABLE:
            self.metadata = self._default_metadata()
            return self.status()

        # Fetch AP and Probe data for training
        df = self._fetch_training_frame()
        
        if len(df) < min_samples:
            self.metadata = {
                **self._default_metadata(),
                "status": "insufficient_data",
                "sample_count": int(len(df)),
                "min_samples": int(min_samples),
                "data_sha256": self._data_hash(df) if len(df) else None,
            }
            self._write_metadata()
            return self.status()
        
        self.clf = IsolationForest(contamination=contamination, random_state=42)
        self.clf.fit(df[FEATURE_NAMES])
        self.is_trained = True
        self.model_dir.mkdir(parents=True, exist_ok=True)
        with self.model_path.open("wb") as handle:
            pickle.dump(self.clf, handle)

        self.metadata = {
            **self._default_metadata(),
            "status": "trained",
            "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "sample_count": int(len(df)),
            "min_samples": int(min_samples),
            "contamination": contamination,
            "data_sha256": self._data_hash(df),
        }
        self._write_metadata()
        return self.status()

    def check_anomaly(self, rssi, channel):
        if not ML_AVAILABLE or not self.is_trained:
            return False
            
        pred = self.clf.predict(pd.DataFrame([[rssi, channel]], columns=FEATURE_NAMES))
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
