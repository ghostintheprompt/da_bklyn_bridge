#!/usr/bin/env python3
"""
Train and persist the passive anomaly baseline from an existing DB.

This is an offline lifecycle step. It does not capture packets or touch a
wireless interface.
"""

import argparse
import json
import os
from pathlib import Path

from analysis import AnomalyDetector
from storage import Database


def train_model(db_path, model_dir, min_samples=20, contamination=0.05):
    os.environ.setdefault("SENTINEL_ALLOW_INSECURE_DB", "1")
    db = Database(str(db_path))
    try:
        detector = AnomalyDetector(db, model_dir=model_dir)
        return detector.train_baseline(min_samples=min_samples, contamination=contamination)
    finally:
        db.conn.close()


def main():
    parser = argparse.ArgumentParser(description="Train the Da Bklyn Bridge anomaly baseline from a local DB.")
    parser.add_argument("--db", default="sentinel.db", help="Input SQLite/SQLCipher database")
    parser.add_argument("--model-dir", default="models", help="Directory for model and metadata output")
    parser.add_argument("--min-samples", type=int, default=20, help="Minimum rows required to train")
    parser.add_argument("--contamination", type=float, default=0.05, help="IsolationForest contamination value")
    args = parser.parse_args()

    status = train_model(Path(args.db), Path(args.model_dir), args.min_samples, args.contamination)
    print(json.dumps(status, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
