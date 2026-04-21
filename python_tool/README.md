# Da Bklyn Bridge - Professional Wireless Intelligence Suite

**Da Bklyn Bridge** is a comprehensive Wi-Fi monitoring and threat detection suite, optimized for the **Alfa AWUS036ACH** (RTL8812AU) and designed for the 2026 wireless landscape.

## 🛰️ 2026 Core Capabilities
- **6GHz Ready Protocol Detection**: While the AWUS036ACH is dual-band, the software parses metadata to identify nearby Wi-Fi 6 (HE) and Wi-Fi 7 (EHT) infrastructure.
- **Privacy Detection (LAA)**: Automatically flags Randomized MAC addresses (Locally Administered Addresses), helping you distinguish between static devices and modern privacy-preserved hardware.
- **Drone Remote ID Monitor**: Captures and alerts on ASTM/ASD-STAN Remote ID beacons broadcast from nearby drones.
- **Anomaly Detection Engine**: Uses a Scikit-Learn `IsolationForest` model to establish environmental baselines and flag "ghost" signals or unusual signal physics.
- **War Driving / Geolocation**: Full integration with `gpsd` to log Latitude/Longitude for every captured probe and beacon.
- **EAPOL Handshake Logger**: Passively captures 4-way handshake frames for security auditing and exam study.

## 📊 Operational Modes (The Games)
1. **01: Neighborhood Census**: Broad-spectrum AP enumeration including hidden SSID discovery.
2. **02: Behavioral Probes**: Client travel history extraction through SSID leakage.
3. **03: Deauth Watch**: Real-time detection of spectral violations and deauthentication spikes.
4. **04: Time-Lapse**: Long-term pattern analysis focusing on "Night-Owl" and "Ghost" networks.
5. **05: Self Audit**: Leak detection and rogue AP auditing for your own perimeter.
6. **06: Academy**: Integrated exam-prep reference for CompTIA Security+/PenTest+ concepts.

## 🛠️ Hardware Setup: Alfa AWUS036ACH
The AWUS036ACH requires specific drivers for monitor mode and injection.

### 1. Driver Installation (Linux)
```bash
sudo apt update
sudo apt install realtek-rtl88xxau-dkms
# Manual install if repository is missing:
git clone https://github.com/aircrack-ng/rtl8812au.git
cd rtl8812au && sudo make dkms_install
```

### 2. Manual Monitor Mode Transition
```bash
sudo ip link set <interface> down
sudo iw dev <interface> set monitor control
sudo ip link set <interface> up
```

## 🚀 Running the Suite

### Main Engine & CLI Dashboard
Must be run as root:
```bash
cd python_tool
pip3 install -r requirements.txt
sudo python3 main.py -i wlan0
```

### Remote API & Web Dashboard
To expose stats to the React web dashboard:
```bash
python3 api_bridge.py
```

## 🔔 Alerting & Integration
- **Discord/Slack**: Configure `discord_webhook_url` in `config.yaml` for instant push notifications.
- **Systemd**: Use `sentinel.service` to run Da Bklyn Bridge as a headless background daemon on a Raspberry Pi.

---
*Educational use only. Built for the Ghost in the Prompt series.*
