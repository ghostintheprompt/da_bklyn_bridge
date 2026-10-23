<div align="center">
<img width="500" height="500" alt="Da Bklyn Bridge Icon" src="icon.png" />

# Da Bklyn Bridge

**Authorized wireless red-team tooling: recon, detection, and engagement-scoped active mitigation.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-orange.svg)](BUILD.md)
[![Trusted Access: Gated](https://img.shields.io/badge/Trusted_Access-Gated-emerald.svg)](docs/trusted_access/TRUSTED_ACCESS_PACKET.md)

</div>

## Overview

Da Bklyn Bridge is a wireless security monitoring suite built around Linux monitor mode and Alfa-class USB adapters. It turns 802.11 management-frame telemetry into local forensic records, SOC-style alerts, dashboard statistics, offline replay evidence, and redacted review bundles.

The posture is passive by default: recon and detection transmit nothing. The localhost API stays local, update checks are off unless enabled, and active deauth is off unless you arm it with `--arm` against a declared engagement scope. Capability with scope discipline: the tool only touches what your rules of engagement authorize, enforced in code.

Use this only on networks, RF environments, devices, and lab equipment you own or are explicitly authorized to test.

Start with `START_HERE.md` when you want the shortest path from Mac + Alfa to
dashboard.

## Portfolio Context

This repo is written for the same lane as my current work: red-team pressure testing, blue SOC reasoning, and frontier-model security workflows where local evidence and clear authorization matter.

- **Red-team signal:** engagement-scoped active deauth, adversarial RF thinking, and no-RF replay to prove the pipeline before live testing.
- **Blue SOC signal:** incident IDs, local alert records, dashboard metrics, anomaly status, report bundles, and evidence redaction.
- **Frontier-model security signal:** separates raw evidence from safe review artifacts, avoids surprise egress, treats replay fixtures as test harnesses, and keeps simulated capability distinct from live action.
- **Professional boundary:** no broad RF disruption, no hidden outbound calls, no production claims without instrumentation, and no active mode outside written scope.

## What It Does

| Capability | Implementation | Current Status |
| :--- | :--- | :--- |
| Passive AP/probe capture | `python_tool/capture.py` | Real local monitor-mode capture |
| SOC alerting | `python_tool/alerting.py` | Real local incident records with `INC-...` IDs |
| Actor correlation | `python_tool/analysis.py` | SSID-history heuristic plus an optional IsolationForest anomaly model (needs ML extras) |
| Covert-channel review | `python_tool/capture.py` | Local entropy checks on vendor-specific tags |
| Wi-Fi 6/7 metadata | `python_tool/capture.py` | HE/EHT tag parsing where frames expose it |
| Drone Remote ID | `python_tool/remote_id.py` | Real OpenDroneID (ASTM F3411) Wi-Fi decoder: Basic ID, Location, Operator ID. Validated vs spec vectors, not yet a live drone |
| Evidence storage | `python_tool/storage.py` | SQLCipher when available; explicit insecure lab fallback |
| Local dashboard API | `python_tool/api_bridge.py` | `127.0.0.1:5000` by default, optional bearer token |
| Offline validation | `generate_lab_pcap.py`, `replay_pcap.py` | Real no-RF replay path |
| Report bundle | `report_bundle.py` | Redacted local output for review packets |
| Active mitigation | `active_mitigation.py` | Scoped targeted deauth; fires only at in-scope BSSIDs with `--arm` |
| Offensive wireless ops | `wireless_ops.py` | Scoped `capture` / `wps` / `eviltwin` / `ble`, orchestrates the standard tools (airodump, reaver, eaphammer, hcxtools, hashcat), prints each command as it runs, enforces ROE scope |
| Findings export | `findings_report.py` | Turns detections into an engagement findings section (severity, ATT&CK/ATLAS mapping, evidence, remediation) |

## Operating Model

- **Passive first:** capture and analyze management-frame telemetry without transmitting.
- **Local first:** API binds to `127.0.0.1` unless you explicitly change `SENTINEL_API_HOST`.
- **Evidence aware:** use `SENTINEL_DB_KEY` for encrypted storage when SQLCipher is available.
- **No surprise egress:** update checks are disabled unless `SENTINEL_CHECK_UPDATES=1`.
- **Scope-locked:** active deauth fires only at BSSIDs in your declared engagement scope, and only with `--arm`.
- **No-RF validation:** synthetic pcap generation and replay let you prove the pipeline before touching hardware.
- **Ghost rule:** real capability is acceptable only when the warning, scope, and evidence story are equally real.

## Quick Start

### 1. App-Like Mac Dashboard

```bash
git clone https://github.com/ghostintheprompt/da_bklyn_bridge.git
cd da_bklyn_bridge
npm install
npm run app
```

If the capture API is running inside the Linux VM:

```bash
npm run app -- --api http://<VM_IP>:5000
```

### 2. Prove The Pipeline Without RF

```bash
npm install
npm run build

cd python_tool
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
SENTINEL_ALLOW_INSECURE_DB=1 python3 -m unittest discover -s tests
```

### 3. Apple Silicon Mac + Alfa Path

macOS can run the dashboard, but Alfa monitor-mode capture should run inside a
small ARM Linux VM with USB passthrough.

```bash
bash scripts/apple_silicon_vm_bootstrap.sh
bash scripts/alfa_doctor.sh
```

If your adapter is AWUS036ACH / RTL8812AU, use the optional driver path:

```bash
bash scripts/apple_silicon_vm_bootstrap.sh --rtl8812au --with-aircrack
bash scripts/alfa_doctor.sh
```

See `APPLE_SILICON_SETUP_GUIDE.md` for the M4-tuned UTM workflow.

### 4. Configure Evidence Storage

For real evidence work, set an encryption key:

```bash
export SENTINEL_DB_KEY="replace-with-a-strong-local-key"
```

For local replay or unit tests only:

```bash
export SENTINEL_ALLOW_INSECURE_DB=1
```

### 5. Run Passive Monitoring

```bash
bash scripts/run_passive.sh --interface wlan0
```

Omit `--interface` to let the tool autodetect a wireless interface. The wrapper
will ask for scope confirmation, then elevate with `sudo` for monitor-mode
capture.

### 6. Run The Local API

```bash
export SENTINEL_API_TOKEN="optional-local-token"
bash scripts/run_api.sh
```

The frontend reads dashboard state from `/api/stats`, including AP counts,
rogue AP counts, deauth groups, temporal buckets, vendor enrichment,
anomaly-model status, and hardware readiness.

For a Mac browser pointed at a VM API:

```bash
# inside the VM
bash scripts/run_api.sh --host-vm

# on the Mac
SENTINEL_PROXY_TARGET=http://<VM_IP>:5000 npm run dev
```

## No-RF Validation

Use this path before requesting or using trusted access:

```bash
cd python_tool
python3 generate_lab_pcap.py --out /tmp/bridge_lab_validation.pcap --write-config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 replay_pcap.py /tmp/bridge_lab_validation.pcap --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 train_anomaly_model.py --db /tmp/bridge_replay.db --model-dir /tmp/bridge_models --min-samples 2
SENTINEL_ALLOW_INSECURE_DB=1 python3 report_bundle.py --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml --out /tmp/bridge_reports
```

## Active Mitigation

Active mitigation is a real offensive capability (targeted deauth via `aireplay-ng`) for authorized engagements: handshake capture, client-isolation testing, rogue-AP takedown. It is governed by engagement scope, not a lab lock. It fires only when both are true:

- you start with `--arm`, and
- the target BSSID is in your declared scope.

Load your scope from your signed rules of engagement, either `active_mitigation.scope_bssids` in `python_tool/config.yaml` or a `--scope engagement.txt` file (one BSSID per line). An empty scope keeps the tool passive: recon and detection only, nothing transmitted. The scope is enforced in code, so the tool cannot deauth a BSSID you did not authorize.

## Environment Variables

| Variable | Purpose | Default |
| :--- | :--- | :--- |
| `SENTINEL_DB_KEY` | SQLCipher evidence database key | unset |
| `SENTINEL_ALLOW_INSECURE_DB` | Allow SQLite fallback for local lab replay/tests | unset |
| `SENTINEL_API_HOST` | API bind host | `127.0.0.1` |
| `SENTINEL_API_PORT` | API port | `5000` |
| `SENTINEL_API_TOKEN` | Optional bearer-token guard for API routes | unset |
| `SENTINEL_CORS_ORIGINS` | Allowed local frontend origins | `localhost` and `127.0.0.1` Vite origins |
| `SENTINEL_CHECK_UPDATES` | Enable outbound GitHub release checks | unset |
| `SENTINEL_OUI_CSV` | Optional local OUI CSV enrichment source | unset |
| `SENTINEL_MODEL_DIR` | Optional anomaly model directory | unset |
| `SENTINEL_PROXY_TARGET` | Vite dev proxy target for VM API access | `http://localhost:5000` |
| `VITE_SENTINEL_API_BASE` | Direct browser API base for cross-host dashboard use | unset |

## Low-Space Notes

- Keep `node_modules` on the Mac, not inside the VM, when possible.
- The default Python requirements are now the lean capture/API set.
- Optional ML extras live in `python_tool/requirements-ml.txt`.
- Optional SQLCipher evidence extras live in `python_tool/requirements-evidence.txt`.
- `scripts/alfa_doctor.sh` tells you whether the problem is USB passthrough, driver support, monitor mode, or Python setup.

## Trusted Access Packet

Start here when preparing a formal lab or contract workflow:

- `docs/trusted_access/TRUSTED_ACCESS_PACKET.md`
- `docs/trusted_access/LAB_VALIDATION_PLAN.md`
- `docs/trusted_access/ROE_TEMPLATE.md`
- `docs/trusted_access/READINESS_GAP_LIST.md`

## Current Boundaries

- Full IEEE OUI distribution is not bundled; use `SENTINEL_OUI_CSV` for local enrichment.
- Curated real pcaps should be captured only from owned hardware after trusted access is approved.
- SQLite fallback is acceptable for local replay, not trusted evidence storage.

## Verification

```bash
npm run lint
npm run build

cd python_tool
SENTINEL_ALLOW_INSECURE_DB=1 python3 -m unittest discover -s tests
```

## License

MIT. Built by **MDRN Corp** - [mdrn.app](https://mdrn.app)
