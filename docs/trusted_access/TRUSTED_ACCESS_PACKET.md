# Trusted Access Packet

This packet is for reviewers who need to understand what Da Bklyn Bridge does, how it is controlled, and how it can be validated without touching live RF space.

## Purpose

Da Bklyn Bridge is a wireless monitoring and forensic dashboard for authorized environments. It focuses on passive 802.11 observation, local evidence capture, and SOC-friendly alerting for:

- Access point census.
- Probe request visibility.
- Rogue AP detection.
- Deauthentication spike detection.
- WPA handshake observation.
- Vendor tag entropy review.
- Local dashboard and alert history.

## Default Operating Posture

- Passive by default.
- Local API by default: `127.0.0.1:5000`.
- CORS limited to local dev origins by default.
- No outbound update check unless `SENTINEL_CHECK_UPDATES=1`.
- No active mitigation unless all lab safety gates pass.
- Database encryption key is supplied by environment: `SENTINEL_DB_KEY`.

## Explicit Non-Goals

- No unsanctioned RF transmission.
- No credential attacks.
- No production deauthentication.
- No cracking workflow.
- No automatic exfiltration of captured data.
- No cloud upload by default.

## Safety Gates For Active Mitigation

Active mitigation remains blocked unless all of these are true:

- CLI flag `--arm` is set.
- `operation_mode: lab`.
- `trusted_access_ack: true`.
- `active_mitigation.enabled: true`.
- At least one allowed lab BSSID is configured.
- Target BSSID is in the allowed lab list.
- Broadcast-client deauth is disabled unless explicitly allowed for an isolated lab.

Recommended policy: keep active mitigation disabled outside a shielded, owned lab.

## Evidence Controls

- Use `SENTINEL_DB_KEY` for encrypted persistence where SQLCipher is available.
- Store raw capture files separately from report-ready evidence.
- Redact MAC addresses when they are not needed for proof.
- Record operator, scope, date, interface, config hash, and replay/capture method.

## Offline Validation

Preferred validation method before trusted access:

```bash
cd python_tool
python3 generate_lab_pcap.py --out /tmp/bridge_lab_validation.pcap --write-config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 replay_pcap.py /tmp/bridge_lab_validation.pcap --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml
SENTINEL_ALLOW_INSECURE_DB=1 python3 train_anomaly_model.py --db /tmp/bridge_replay.db --model-dir /tmp/bridge_models --min-samples 2
SENTINEL_ALLOW_INSECURE_DB=1 python3 report_bundle.py --db /tmp/bridge_replay.db --config /tmp/bridge_lab_config.yaml --out /tmp/bridge_reports
python3 -m unittest discover -s tests
```

This exercises parser, alert, and report logic without setting monitor mode, hopping channels, or transmitting frames.

## Reviewer Checklist

- Scope and ROE document exists.
- Data handling plan exists.
- Passive mode validated.
- Offline replay tests pass.
- Active mitigation disabled by default.
- API bound to localhost or protected by token.
- No hardcoded secret is required for operation.
- Outbound update checks disabled by default.
- Evidence examples are redacted and reproducible.
- Report bundle includes config hash, table counts, rogue AP review, deauth summary, recent alerts, redacted AP/probe samples, and `stats_snapshot.json`.
- Anomaly model status is persisted in metadata and exposed to API/dashboard consumers.
- Optional OUI enrichment can use `SENTINEL_OUI_CSV` without modifying code.
