# Building Da Bklyn Bridge

This guide covers the technical requirements and build process for Da Bklyn Bridge.

## 💻 Hardware Requirements
- **Primary Adapter:** Alfa AWUS036ACH (RTL8812AU) is recommended.
- **Drivers:** Requires DKMS drivers with monitor mode and injection support.

## 🐧 Linux Installation (Native)

### 1. Driver Setup
```bash
sudo apt update
sudo apt install realtek-rtl88xxau-dkms
```

### 2. Dependency Installation
```bash
# Python dependencies
pip3 install -r python_tool/requirements.txt

# Frontend dependencies
npm install
```

### 3. Build Frontend
```bash
npm run build
```

## 🍎 macOS Installation (VM Method)
macOS does not support USB Wi-Fi monitor mode natively. To use Da Bklyn Bridge on a Mac:

1. **Install a VM:** Use [UTM](https://getutm.app/) (Free/Open Source) or Parallels.
2. **Setup Linux:** Install a minimal Debian or Kali Linux guest.
3. **USB Passthrough:** Connect your Alfa card and pass the USB device directly to the VM.
4. **Follow Linux Instructions:** Once inside the VM, follow the Linux installation steps above.

## 🚀 Troubleshooting
- **Monitor Mode:** If `main.py` fails to set monitor mode, try manual transition:
  ```bash
  sudo ip link set <interface> down
  sudo iw dev <interface> set monitor control
  sudo ip link set <interface> up
  ```
- **Permission Denied:** Ensure you run `main.py` with `sudo`.
- **UI Connectivity:** The React frontend expects the API bridge to be running on port 5000. Ensure `python3 api_bridge.py` is active.

---
*No shareware. No pricing. Just signal.*
