<div align="center">
<img width="500" height="500" alt="Da Bklyn Bridge Icon" src="icon.png" />

# Da Bklyn Bridge

**Professional Wi-Fi Monitoring & Threat Intelligence for the 2026 Spectral Landscape.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-orange.svg)](BUILD.md)
[![Release: v1.0.0](https://img.shields.io/badge/Release-v1.0.0-green.svg)](https://github.com/ghostintheprompt/da-bklyn-bridge/releases)

</div>

## 🛰️ Overview
**Da Bklyn Bridge** is a precision wireless intelligence suite optimized for the **Alfa AWUS036ACH**. It bridges the gap between raw packet capture and actionable security intelligence, providing a high-fidelity dashboard for airspace enumeration, behavioral client profiling, and anomaly detection.

## 🛠️ Feature Matrix
| Feature | Implementation | Description |
| :--- | :--- | :--- |
| **Wi-Fi 6/7 Detection** | `capture.py` | Parses HE/EHT extension tags to identify modern infrastructure. |
| **Privacy Analysis** | `vendors.py` | Automatically flags Randomized MAC (LAA) addresses. |
| **Drone Monitoring** | `remote_id.py` | Captures and decodes ASTM/ASD-STAN Drone Remote ID beacons. |
| **Anomaly Engine** | `analysis.py` | Uses `IsolationForest` to establish environmental signal baselines. |
| **Deauth Watch** | `alerting.py` | Detects spectral violations and targeted disassociation attacks. |
| **EAPOL Logger** | `capture.py` | Passively captures 4-way handshakes for security auditing. |
| **Geo-Logging** | `gps_module.py` | Full `gpsd` integration for high-precision war-driving. |

## 🚀 Installation

### 1. Build from Source
```bash
# Clone the repository
git clone https://github.com/ghostintheprompt/da-bklyn-bridge.git
cd da-bklyn-bridge

# Install Backend Dependencies
pip3 install -r python_tool/requirements.txt

# Build Frontend Assets
npm install
npm run build
```

### 2. Run the Suite
```bash
# Start the monitoring engine (requires root)
sudo python3 python_tool/main.py -i wlan0

# Start the API bridge (in a separate terminal)
python3 python_tool/api_bridge.py -i wlan0
```

*For detailed setup on macOS via VM, see [BUILD.md](BUILD.md).*

## 🛡️ Privacy Statement
**Local Only. No Telemetry.** 
Da Bklyn Bridge operates entirely on your local machine. No data, captures, or telemetry are ever sent to external servers. All processing is done passively in-memory or stored in a local SQLite database (`sentinel.db`).

---
**Built by MDRN Corp — [mdrn.app](https://mdrn.app)**
*Read the full implementation story at [ghostintheprompt.com](https://ghostintheprompt.com/articles/da-bklyn-bridge)*
