# M1 Mac "Lightweight" Stealth Setup

Since you are on an M1 with limited space, we want to avoid heavy VirtualBox or VMware installs. This is the surgical approach to get the Alfa card running tonight.

## 1. The VM Engine: UTM (Apple Virtualization)
UTM is the most lightweight way to run Linux on Apple Silicon. It uses Apple's native Virtualization.framework.

- **Download:** [getutm.app](https://getutm.app/)
- **Image:** Download the **Debian 12 (ARM64) Netinst ISO** (~600MB).
- **Resources:** Allocate only 2GB RAM and 10GB Disk (Thinly provisioned).

## 2. USB Passthrough (The Critical Step)
1. Plug your **Alfa AWUS036ACH** into your Mac.
2. In UTM settings for your VM, go to **USB**.
3. Click **New** and select the Realtek/Alfa device.
4. When you start the VM, macOS may ask for permission to "Connect to Terminal"—say Yes.

## 3. The "Stealth" Driver Setup (Inside VM)
Inside your Debian VM, run these commands to get the 2026-ready drivers:

```bash
sudo apt update
sudo apt install -y realtek-rtl88xxau-dkms gpsd gpsd-clients python3-pip

# Verify the card is seen as a USB device
lsusb 
# You should see: Realtek Semiconductor Corp. RTL8812AU 802.11a/b/g/n/ac 
```

## 4. Launching the Suite
Navigate to the project folder inside the VM and fire it up:

```bash
# Terminal 1: The Engine
cd da-bklyn-bridge/python_tool
sudo python3 main.py -i wlan0

# Terminal 2: The API
cd da-bklyn-bridge/python_tool
python3 api_bridge.py -i wlan0
```

## 5. Viewing the Dashboard
Since the VM has its own IP, you can view the dashboard from your **Mac's browser** (outside the VM):
1. Find the VM IP: `ip addr show eth0`
2. On your Mac, browse to: `http://<VM_IP>:5000` (after running the React build).

**Stealth Note:** Because the Alfa card is in Monitor Mode, the VM's internal networking (eth0) remains completely separate from the wireless "listening" interface (wlan0). You are essentially a black hole in the RF spectrum—consuming data without emitting a single bit.
