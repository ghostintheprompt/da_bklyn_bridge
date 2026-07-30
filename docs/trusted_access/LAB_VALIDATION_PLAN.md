# Lab Validation Plan

Use this to prove the suite works before requesting or using trusted access.

## Lab Inventory

| Item | Value |
| --- | --- |
| Operator | |
| Date | |
| Location | |
| Wireless adapter | Alfa AWUS036ACH or equivalent |
| Host | Linux VM or native Linux |
| Interface | |
| Owned AP SSID | |
| Authorized BSSID list | |
| Evidence folder | |

## Passive Validation

| Test | Expected result | Evidence |
| --- | --- | --- |
| AP beacon capture | AP row appears in DB/dashboard | |
| Probe request capture | Probe row appears in DB/dashboard | |
| Watched SSID authorized BSSID | No rogue AP alert | |
| Watched SSID unauthorized lab BSSID | Rogue AP alert | |
| Deauth spike replay | Deauth alert in DB/dashboard | |
| EAPOL frame replay | WPA handshake alert | |
| Vendor tag entropy replay | Covert-channel-suspected alert if threshold exceeded | |

## Offline Replay Validation

| Replay file | Packet count | AP rows | Probe rows | Alerts | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| | | | | | |

Recommended no-RF smoke test:

```bash
cd python_tool
python3 generate_lab_pcap.py --out /tmp/bridge_lab_validation.pcap --write-config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 replay_pcap.py /tmp/bridge_lab_validation.pcap --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 report_bundle.py --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml --out /tmp/bridge_reports
```

Expected minimum results:

| Result | Expected value |
| --- | --- |
| Replayed packets | 7 |
| AP rows | 3 or more |
| Probe rows | 1 |
| Alert rows | Rogue AP, deauth spike, EAPOL handshake, high-entropy vendor tag |
| Report bundle | `SUMMARY.md` and `manifest.json` |

## Active Mitigation Gate Validation

Do not transmit frames unless operating inside an isolated lab with written approval.

| Gate | Expected result |
| --- | --- |
| `--arm` without lab config | Refused |
| `operation_mode: passive` | Refused |
| `trusted_access_ack: false` | Refused |
| Empty allowed BSSID list | Refused |
| Target outside allowed BSSID list | Refused |
| Broadcast client without explicit allow | Refused |

## Report Artifacts

- Scope/ROE.
- Config used.
- Test command log.
- Replay output.
- Report bundle summary and manifest.
- Unit test output.
- Dashboard screenshot.
- Database export or selected redacted rows.
- Findings and limitations.
