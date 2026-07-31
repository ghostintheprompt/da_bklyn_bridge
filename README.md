<div align="center">
<img width="500" height="500" alt="Da Bklyn Bridge Icon" src="icon.png" />

# Da Bklyn Bridge

**Passive-first wireless monitoring, trusted-access lab readiness, and red/blue signal discipline.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-orange.svg)](BUILD.md)
[![Trusted Access: Gated](https://img.shields.io/badge/Trusted_Access-Gated-emerald.svg)](docs/trusted_access/TRUSTED_ACCESS_PACKET.md)

</div>

## Overview

Da Bklyn Bridge is a wireless security monitoring suite built around Linux monitor mode and the Alfa AWUS036ACH class of adapters. It turns 802.11 management-frame telemetry into local forensic records, SOC-style alerts, dashboard statistics, offline replay evidence, and redacted review bundles.

The current posture is intentionally conservative: passive monitoring by default, localhost API by default, no outbound update checks unless enabled, and active mitigation blocked unless trusted-access lab gates are satisfied. The point is capability with restraint: prove the pipeline locally, document scope, preserve evidence, then operate only where authorization is real.

Use this only on networks, RF environments, devices, and lab equipment you own or are explicitly authorized to test.

## Portfolio Context

This repo is written for the same lane as my current work: red-team pressure testing, blue SOC reasoning, and frontier-model security workflows where local evidence and clear authorization matter.

- **Red-team signal:** trusted-access gates, lab-only active mode, adversarial RF thinking, and no-RF replay before live testing.
- **Blue SOC signal:** incident IDs, local alert records, dashboard metrics, anomaly status, report bundles, and evidence redaction.
- **Frontier-model security signal:** separates raw evidence from safe review artifacts, avoids surprise egress, treats replay fixtures as test harnesses, and keeps simulated capability distinct from live action.
- **Professional boundary:** no broad RF disruption, no hidden outbound calls, no production claims without instrumentation, and no active mode outside written scope.

## What It Does

| Capability | Implementation | Current Status |
| :--- | :--- | :--- |
| Passive AP/probe capture | `python_tool/capture.py` | Real local monitor-mode capture |
| SOC alerting | `python_tool/alerting.py` | Real local incident records with `INC-...` IDs |
| Actor correlation | `python_tool/analysis.py` | Local SSID history and anomaly-model support |
| Covert-channel review | `python_tool/capture.py` | Local entropy checks on vendor-specific tags |
| Wi-Fi 6/7 metadata | `python_tool/capture.py` | HE/EHT tag parsing where frames expose it |
| Remote ID review | `python_tool/remote_id.py` | Lab marker extraction and alerting |
| Evidence storage | `python_tool/storage.py` | SQLCipher when available; explicit insecure lab fallback |
| Local dashboard API | `python_tool/api_bridge.py` | `127.0.0.1:5000` by default, optional bearer token |
| Offline validation | `generate_lab_pcap.py`, `replay_pcap.py` | Real no-RF replay path |
| Report bundle | `report_bundle.py` | Redacted local output for review packets |
| Active mitigation | `active_mitigation.py` | Real lab-only capability behind config gates and `--arm` |

## Operating Model

- **Passive first:** capture and analyze management-frame telemetry without transmitting.
- **Local first:** API binds to `127.0.0.1` unless you explicitly change `SENTINEL_API_HOST`.
- **Evidence aware:** use `SENTINEL_DB_KEY` for encrypted storage when SQLCipher is available.
- **No surprise egress:** update checks are disabled unless `SENTINEL_CHECK_UPDATES=1`.
- **Trusted access only:** active mitigation requires lab mode, acknowledgement, and allowed BSSID scope.
- **No-RF validation:** synthetic pcap generation and replay let you prove the pipeline before touching hardware.
- **Ghost rule:** real capability is acceptable only when the warning, scope, and evidence story are equally real.

## Quick Start

### 1. Clone And Install

```bash
git clone https://github.com/ghostintheprompt/da_bklyn_bridge.git
cd da_bklyn_bridge

pip3 install -r python_tool/requirements.txt
npm install
npm run build
```

### 2. Configure Evidence Storage

For real evidence work, set an encryption key:

```bash
export SENTINEL_DB_KEY="replace-with-a-strong-local-key"
```

For local replay or unit tests only:

```bash
export SENTINEL_ALLOW_INSECURE_DB=1
```

### 3. Run Passive Monitoring

```bash
sudo python3 python_tool/main.py -i wlan0
```

The tool requires root for monitor-mode capture. On macOS, use a Linux VM with USB passthrough; macOS does not expose native Wi-Fi monitor mode for this workflow.

### 4. Run The Local API

```bash
export SENTINEL_API_TOKEN="optional-local-token"
python3 python_tool/api_bridge.py
```

The frontend reads dashboard state from `/api/stats`, including AP counts, rogue AP counts, deauth groups, temporal buckets, vendor enrichment, Remote ID alerts, and anomaly-model status.

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

Active mitigation is a real lab capability and should stay disabled for normal monitoring. `--arm` alone is not enough. The runtime refuses active mode unless all gates pass:

- `operation_mode: lab`
- `trusted_access_ack: true`
- at least one allowed lab BSSID
- target BSSID is inside the allowed lab list
- broadcast-client deauth remains disabled unless explicitly allowed for an isolated lab

Start from `python_tool/config.yaml` and document scope using the trusted-access materials before enabling active mode.

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

## Trusted Access Packet

Start here when preparing a formal lab or contract workflow:

- `docs/trusted_access/TRUSTED_ACCESS_PACKET.md`
- `docs/trusted_access/LAB_VALIDATION_PLAN.md`
- `docs/trusted_access/ROE_TEMPLATE.md`
- `docs/trusted_access/READINESS_GAP_LIST.md`

## Current Boundaries

- Full IEEE OUI distribution is not bundled; use `SENTINEL_OUI_CSV` for local enrichment.
- Remote ID support is currently structured lab-marker extraction, not a complete production decoder.
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
