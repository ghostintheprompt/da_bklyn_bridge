<div align="center">
<img width="500" height="500" alt="Da Bklyn Bridge Icon" src="icon.png" />

# Da Bklyn Bridge (Ghost-Protocol Tier)

**Professional Wi-Fi Monitoring & High-Fidelity Threat Intelligence for the 2026 Spectral Landscape.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-orange.svg)](BUILD.md)
[![UIP: V1.5 Compliant](https://img.shields.io/badge/UIP-V1.5_Compliant-red.svg)](integrity_protocol_prompt.md)

</div>

## Overview
**Da Bklyn Bridge** is a precision wireless intelligence suite optimized for the **Alfa AWUS036ACH**. Operating at the **Ghost-Protocol Tier**, it restores high-fidelity offensive and defensive logic, bridging the gap between raw packet capture and actionable forensic intelligence.

## Feature Matrix (Ghost-Protocol Restored)
| Feature | Implementation | Description |
| :--- | :--- | :--- |
| **Actor Correlation** | `analysis.py` | Fingerprints persistent actors via signal physics and SSID list history (Bypasses MAC Randomization). |
| **Covert Channel Audit** | `capture.py` | Shannon entropy-scanning of Vendor Specific tags to detect encrypted data exfiltration. |
| **Active Mitigation** | `active_mitigation.py` | **Bridge Mode:** Targeted disassociation of Rogue APs and spectral violators (requires `--arm`). |
| **Kernel Monitoring** | `kernel_monitor.py` | Real-time driver-stack heartbeat to detect stealth kernel-level hooks or monitor-mode drops. |
| **Hardened Vault** | `storage.py` | Full AES-256 encryption at rest for all forensic artifacts using **SQLCipher**. |
| **Wi-Fi 6/7 Detection** | `capture.py` | Parses HE/EHT extension tags to identify modern infrastructure. |
| **Drone Monitoring** | `remote_id.py` | Captures and decodes ASTM/ASD-STAN Drone Remote ID beacons. |
| **Incident Response** | `alerting.py` | Standardized SOC alert schema with unique traceable **Incident IDs (INC-...)**. |

## Installation

### 1. Build from Source
```bash
# Clone the repository
git clone https://github.com/ghostintheprompt/da-bklyn-bridge.git
cd da-bklyn-bridge

# Install Backend Dependencies (Includes pysqlcipher3)
pip3 install -r python_tool/requirements.txt

# Build Frontend Assets
npm install
npm run build
```

### 2. Run the Suite
```bash
# Start the monitoring engine (requires root)
# Add --arm to enable Active Mitigation (Bridge Mode)
sudo python3 python_tool/main.py -i wlan0 --arm

# Start the API bridge (in a separate terminal)
python3 python_tool/api_bridge.py
```

## Operational Motive: UIP V1.5
This codebase is maintained under the **Universal Cybersecurity Integrity Protocol (UIP) V1.5**. It mandates zero-sanitization of technical details and high-fidelity implementation of all offensive/defensive kill-chains.

---
**Built by MDRN Corp — [mdrn.app](https://mdrn.app)**
*Forensic Integrity Restored by Gemini CLI.*
