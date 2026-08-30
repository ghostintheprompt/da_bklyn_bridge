# Apple Silicon + Alfa Setup

This is the current setup path for the M4 Mac mini and later Apple-silicon
Macs. The Mac runs the dashboard and an ARM64 Linux VM owns the Alfa USB
adapter, monitor-mode driver, capture engine, and evidence API.

## Recommended M4 Layout

- macOS: Node/Vite dashboard, report review, and client-facing presentation.
- ARM64 Linux VM: USB passthrough, monitor mode, Python capture, and API.
- VM resources on a 16 GB M4: 4 CPU cores, 4 GB RAM, and a 20 GB
  thin-provisioned disk. Reduce to 2 GB RAM when the optional ML stack is off.
- VM networking: host-only or otherwise isolated for field work; expose the API
  only with `scripts/run_api.sh --host-vm` and an API token.

## Adapter Guidance

| Adapter/chipset | Linux path |
| :--- | :--- |
| AWUS036ACH / RTL8812AU | Use `--rtl8812au`; DKMS driver required |
| AWUS036ACM / MT7612U | Usually handled by the in-kernel `mt76` driver |
| AWUS036NHA / AR9271 | Usually handled by `ath9k_htc` |

## VM Bootstrap

Create a virtualized Kali ARM64 or Debian ARM64 VM in UTM, attach the Alfa to
the VM, clone this repository inside the guest, then run:

```bash
bash scripts/apple_silicon_vm_bootstrap.sh
bash scripts/alfa_doctor.sh
```

For AWUS036ACH / RTL8812AU:

```bash
bash scripts/apple_silicon_vm_bootstrap.sh --rtl8812au --with-aircrack
bash scripts/alfa_doctor.sh
```

Validate monitor-mode transition without transmitting:

```bash
sudo bash scripts/alfa_doctor.sh --probe-monitor wlan0
```

## M4 Dashboard

On macOS:

```bash
npm ci
npm run app -- --api http://<VM_IP>:5000
```

Inside the VM, use encrypted evidence storage and a bearer token for client
work:

```bash
export SENTINEL_DB_KEY="<load-from-your-secret-manager>"
export SENTINEL_API_TOKEN="<load-from-your-secret-manager>"
bash scripts/run_api.sh --host-vm
```

Do not put either secret in the repository, shell history, screenshots, or
client reports. Keep active mitigation disabled unless the written scope,
allowed BSSIDs, lab acknowledgement, and runtime gates all agree.

This is the canonical Apple-silicon guide.
