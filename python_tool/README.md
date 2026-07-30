# Da Bklyn Bridge - Monitoring Engine & Forensic Core

The backend engine for Da Bklyn Bridge is a Python-based spectral analysis suite designed for the **Alfa AWUS036ACH** chipset.

## 🛰️ Ghost-Protocol Core Capabilities
- **Actor Fingerprinting**: Uses `IsolationForest` and SSID history clustering to correlate persistent actors even when they utilize MAC randomization (Locally Administered Addresses).
- **Entropy-Based Exfiltration Detection**: Automatically audits `802.11` management frame tags for high-entropy payloads, flagging potential covert exfiltration channels.
- **Active Bridge Mode**: Programmatic perimeter defense via targeted disassociation injection. Enable with the `--arm` flag to neutralize Rogue APs in real-time.
- **Driver-Stack Integrity**: Monitoring thread that heartbeats the `rtl8812au` driver to ensure monitor mode is not silently disabled by kernel-level hooks.
- **Encrypted Persistence**: All logs, probes, and captured handshakes are stored in a **SQLCipher-encrypted** SQLite database (`sentinel.db`).

## 📊 Operational Modes (Operationalized)
1. **01: Neighborhood Census**: Full AP enumeration including HE/EHT (Wi-Fi 6/7) metadata parsing.
2. **02: Behavioral Probes**: Deep-profile client travel history via SSID leakage analysis.
3. **03: Deauth Watch**: Real-time spectral violation detection with active counter-measures.
4. **04: Time-Lapse**: Forensic pattern analysis identifying "Night-Owl" and "Ghost" (ephemeral) networks.
5. **05: Self Audit**: Authorized BSSID enforcement and automated Rogue AP neutralizing.
6. **06: Academy**: Integrated exam-prep reference (Security+/PenTest+) linked to live capture logic.

## 🚀 Execution & Command Line Arguments
```bash
sudo python3 main.py -i <interface> [OPTIONS]
```

| Flag | Description |
| :--- | :--- |
| `-i, --interface` | **REQUIRED.** Wireless interface in monitor mode (e.g., `wlan0`). |
| `-c, --config` | Path to custom `config.yaml` (Defines watched SSIDs/BSSIDs). |
| `--arm` | **DANGER.** Enables Bridge Mode for active disassociation mitigation. |

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

Offline validation:

```bash
python3 generate_lab_pcap.py --out /tmp/bridge_lab_validation.pcap --write-config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 replay_pcap.py /tmp/bridge_lab_validation.pcap --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 report_bundle.py --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml --out /tmp/bridge_reports
python3 -m unittest discover -s tests
```

---
*Educational and Forensic use only. UIP V1.5 Compliant.*
