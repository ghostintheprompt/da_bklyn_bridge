# Building Da Bklyn Bridge

This guide covers the technical requirements and build process for Da Bklyn Bridge.

## Hardware Requirements

Da Bklyn Bridge needs a Linux wireless interface that supports monitor mode.
The brand matters less than the chipset.

| Adapter/chipset | Status |
| :--- | :--- |
| Alfa AWUS036ACH / RTL8812AU | Supported, but usually needs 88xxAU driver/DKMS setup |
| Alfa AWUS036ACM / MT7612U | Recommended low-friction 2.4/5 GHz path |
| Alfa AWUS036NHA / AR9271 | Reliable 2.4 GHz path |
| 6E/7 adapters | Only for 6 GHz when Linux driver support is confirmed |

## Linux Installation

### 1. Lean System Packages

Debian/Kali/Ubuntu:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip iw iproute2 usbutils wireless-tools tcpdump
```

For AWUS036ACH / RTL8812AU:

```bash
sudo apt install -y dkms linux-headers-$(uname -r) realtek-rtl88xxau-dkms
```

If that package is unavailable on your distro, use the Aircrack-ng maintained
RTL8812AU driver path documented here:
<https://github.com/aircrack-ng/rtl8812AU>

### 2. Python Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r python_tool/requirements.txt
```

Optional extras:

```bash
pip install -r python_tool/requirements-ml.txt
pip install -r python_tool/requirements-evidence.txt
```

### 3. Frontend Dependencies

```bash
npm install
```

### 4. Build Frontend

```bash
npm run build
```

## macOS Installation (M1/M2/M3/M4)

macOS does not support USB Wi-Fi monitor mode natively. To use Da Bklyn Bridge on a Mac:

1. **Install a VM:** Use [UTM](https://getutm.app/) (Free/Open Source) or Parallels.
2. **Setup Linux:** Install a minimal ARM64 Debian or Kali Linux guest.
3. **USB Passthrough:** Connect your Alfa card and pass the USB device directly to the VM.
4. **Run the doctor:** `bash scripts/alfa_doctor.sh`
5. **Run passive capture:** `bash scripts/run_passive.sh --interface wlan0`

See `M1_SETUP_GUIDE.md` for the low-space path.

## Troubleshooting

- **USB missing:** In UTM, attach the Alfa to the VM from the USB device menu.
- **No wireless interface:** Run `bash scripts/alfa_doctor.sh` and check driver hints.
- **Monitor mode:** If automatic setup fails, try:
  ```bash
  sudo ip link set <interface> down
  sudo iw dev <interface> set type monitor
  sudo ip link set <interface> up
  ```
- **Permission Denied:** Ensure you run `main.py` with `sudo`.
- **UI Connectivity:** The React frontend expects the API bridge to be running on port 5000. Use `SENTINEL_PROXY_TARGET=http://<VM_IP>:5000 npm run dev` when the API runs in a VM.

---
*No shareware. No pricing. Just signal.*
