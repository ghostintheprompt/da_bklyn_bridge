# Da Bklyn Bridge - Monitoring Engine & Forensic Core

The backend engine for Da Bklyn Bridge is a Python-based 802.11 monitoring suite designed for Alfa-class USB adapters running inside Linux monitor mode.

## 🛰️ Ghost-Protocol Core Capabilities
- **Actor Fingerprinting**: Uses `IsolationForest` and SSID history clustering to correlate persistent actors even when they utilize MAC randomization (Locally Administered Addresses).
- **Entropy-Based Exfiltration Detection**: Automatically audits `802.11` management frame tags for high-entropy payloads, flagging potential covert exfiltration channels.
- **Lab-Gated Bridge Mode**: Programmatic disassociation is real, but remains blocked unless the trusted-access lab gates pass.
- **Driver-Stack Integrity**: Monitoring thread that heartbeats the selected interface to ensure monitor mode is not silently disabled.
- **Encrypted Persistence**: SQLCipher is used when available. Local SQLite fallback requires explicit lab/test acknowledgement.

## 📊 Operational Modes (Operationalized)
1. **01: Neighborhood Census**: Full AP enumeration including HE/EHT (Wi-Fi 6/7) metadata parsing.
2. **02: Behavioral Probes**: Deep-profile client travel history via SSID leakage analysis.
3. **03: Deauth Watch**: Real-time spectral violation detection with active counter-measures.
4. **04: Time-Lapse**: Forensic pattern analysis identifying "Night-Owl" and "Ghost" (ephemeral) networks.
5. **05: Self Audit**: Authorized BSSID enforcement and automated Rogue AP neutralizing.
6. **06: Academy**: Integrated exam-prep reference (Security+/PenTest+) linked to live capture logic.

## 🚀 Execution & Command Line Arguments
```bash
sudo python3 main.py [-i <interface>] [OPTIONS]
```

| Flag | Description |
| :--- | :--- |
| `-i, --interface` | Wireless interface (for example `wlan0`). Autodetected when omitted. |
| `-c, --config` | Path to custom `config.yaml` (Defines watched SSIDs/BSSIDs). |
| `--db` | Evidence database path. |
| `--skip-monitor-setup` | Use an interface already placed in monitor mode. |
| `--arm` | **DANGER.** Enables Bridge Mode for active disassociation mitigation. |

Prefer the wrapper from the repo root:

```bash
bash scripts/run_passive.sh --interface wlan0
```

## 🔔 SOC Integration
Standardized Incident IDs are generated for all alerts:
`[INC-TIMESTAMP-UUID] ALERT_TYPE: Description`

## Trusted Access Defaults

- Use `SENTINEL_DB_KEY` for encrypted evidence storage when SQLCipher is available.
- Use `SENTINEL_ALLOW_INSECURE_DB=1` only for local lab replay or unit tests.
- The API bridge binds to `127.0.0.1` unless `SENTINEL_API_HOST` is set.
- Set `SENTINEL_API_TOKEN` to require bearer-token access to `/api/stats`.
- Update checks are disabled unless `SENTINEL_CHECK_UPDATES=1`.
- `--arm` does not enable active mitigation unless the config passes lab safety gates.
- Run `bash scripts/alfa_doctor.sh` inside the Linux VM when USB, driver, or monitor-mode setup is unclear.

Offline validation:

```bash
python3 generate_lab_pcap.py --out /tmp/bridge_lab_validation.pcap --write-config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 replay_pcap.py /tmp/bridge_lab_validation.pcap --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 train_anomaly_model.py --db /tmp/bridge_replay.db --model-dir /tmp/bridge_models --min-samples 2
SENTINEL_ALLOW_INSECURE_DB=1 python3 report_bundle.py --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml --out /tmp/bridge_reports
python3 -m unittest discover -s tests
```

OUI enrichment:

```bash
export SENTINEL_OUI_CSV=/path/to/oui.csv
```

The anomaly trainer writes `anomaly_model.pkl` and `anomaly_metadata.json` to the selected model directory when ML dependencies are available.

---
*Educational and Forensic use only. UIP V1.5 Compliant.*
