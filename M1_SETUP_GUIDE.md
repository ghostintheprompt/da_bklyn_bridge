# M1 Mac Alfa Setup: Low-Space, Plug-And-Play Path

This repo can be Mac-friendly, but the capture engine should not pretend macOS
is the right place for monitor mode. On Apple Silicon, run the Alfa inside a
small ARM Linux VM and keep the dashboard/build workflow on the Mac.

## The Answer

Yes, this can be made close to plug-and-play on an M1:

1. Use **UTM + Kali ARM64 or Debian ARM64** as the capture appliance.
2. Pass the Alfa USB adapter into the VM.
3. Run `scripts/alfa_doctor.sh` inside the VM.
4. Run passive capture with `scripts/run_passive.sh`.
5. View the dashboard from either the VM or the Mac browser.

Native macOS is fine for the React dashboard. Native macOS is not the practical
target for Alfa monitor-mode capture.

## Adapter Choice

| Adapter/chipset | Best use | M1 VM friction |
| :--- | :--- | :--- |
| Alfa AWUS036ACH / RTL8812AU | Good 2.4/5 GHz lab adapter if you already own it | Needs 88xxAU DKMS/driver work |
| Alfa AWUS036ACM / MT7612U | Better low-friction 2.4/5 GHz choice | Usually plug-and-play with Linux `mt76` |
| Alfa AWUS036NHA / AR9271 | Reliable 2.4 GHz monitor-mode classic | Usually plug-and-play with `ath9k_htc` |
| 6E/7 adapters | Needed for 6 GHz visibility | Only if Linux driver support is confirmed |

If you already have the AWUS036ACH, keep it. If you are buying a second adapter
for less driver pain, favor a MediaTek MT7612U or Atheros AR9271 Alfa.

## Disk Budget

Minimum working target:

| Item | Suggested size |
| :--- | :--- |
| UTM VM disk | 12-16 GB thin-provisioned |
| RAM | 2 GB |
| Desktop environment | Skip it |
| Python venv | Inside the repo |
| Node build | Prefer on macOS, not inside the VM |

The repo itself is small. `node_modules` is the big local folder, so keep Node
on the Mac and keep the VM focused on USB, drivers, Python capture, and the API.

## VM Setup

Kali has the smoother wireless-tooling path for AWUS036ACH. Debian is smaller,
but Realtek driver setup may take more fiddling.

1. Install UTM: <https://getutm.app/>
2. Create a virtualized ARM64 Linux VM.
3. Use Kali ARM64 if you want the easiest wireless tooling path.
4. Use 2 GB RAM and a 12-16 GB thin-provisioned disk.
5. Skip a heavy desktop if space is tight.
6. In UTM, attach the Alfa USB device to the VM.

Kali's UTM guide is here:
<https://www.kali.org/docs/virtualization/install-utm-guest-vm/>

## Inside The VM

From the repo root:

```bash
bash scripts/m1_vm_bootstrap.sh
bash scripts/alfa_doctor.sh
```

If your adapter is AWUS036ACH / RTL8812AU:

```bash
bash scripts/m1_vm_bootstrap.sh --rtl8812au --with-aircrack
bash scripts/alfa_doctor.sh
```

If the doctor sees the adapter and an interface, start passive capture:

```bash
bash scripts/run_passive.sh --lab-insecure
```

For real evidence work, use an encryption key instead of `--lab-insecure`:

```bash
export SENTINEL_DB_KEY="replace-with-a-strong-local-key"
bash scripts/run_passive.sh
```

## Dashboard From The Mac Browser

Option A: run the API in the VM and the frontend on the Mac.

Inside the VM:

```bash
bash scripts/run_api.sh --host-vm
```

On the Mac:

```bash
SENTINEL_PROXY_TARGET=http://<VM_IP>:5000 npm run dev
```

Then open the Vite URL on the Mac.

Option B: use the frontend's direct API base:

```bash
VITE_SENTINEL_API_BASE=http://<VM_IP>:5000 npm run dev
```

Keep `--host-vm` for trusted or host-only VM networks. The default API bind is
`127.0.0.1`.

## Troubleshooting Flow

Run:

```bash
bash scripts/alfa_doctor.sh
```

Read it top to bottom:

- USB missing means UTM did not pass the Alfa into the VM.
- USB present but no wireless interface usually means driver/chipset support.
- Interface present but not monitor-capable means driver mode support is wrong.
- Python import failures mean the venv is incomplete.

Optional local monitor transition probe:

```bash
sudo bash scripts/alfa_doctor.sh --probe-monitor wlan0
```

That probe only changes local interface mode. It does not transmit frames.

## Current References

- Alfa AWUS036ACH product driver page: <https://docs.alfa.com.tw/Product/AWUS036ACH/>
- Kali UTM guest VM guide: <https://www.kali.org/docs/virtualization/install-utm-guest-vm/>
- Aircrack-ng compatible-card guidance: <https://www.aircrack-ng.org/doku.php?id=compatible_cards>
- Aircrack-ng RTL8812AU driver: <https://github.com/aircrack-ng/rtl8812AU>
