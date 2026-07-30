# Readiness Gap List

## Closed In This Pass

- Removed hardcoded DB key requirement by moving to `SENTINEL_DB_KEY`.
- Added local-lab insecure DB escape hatch: `SENTINEL_ALLOW_INSECURE_DB=1`.
- Locked API host default to `127.0.0.1`.
- Limited CORS default to local dev origins.
- Added optional bearer-token API protection via `SENTINEL_API_TOKEN`.
- Disabled update checks by default.
- Added active-mitigation safety gates.
- Added pcap replay harness.
- Added synthetic packet unit tests.
- Added trusted-access docs and ROE template.
- Added deterministic synthetic lab pcap generator.
- Added redacted report bundle exporter with config hash and DB summary.
- Added integration tests for synthetic pcap replay and report bundle generation.

## Still Open

- Full IEEE OUI database instead of small static vendor map.
- Real Remote ID parser beyond marker detection.
- Proper anomaly model lifecycle: train, persist metadata, show confidence, retest drift.
- More complete Wi-Fi 6/7 parsing and 6 GHz hardware profile.
- Dashboard wiring for deauth stats, rogue APs, night owls, and ghost networks.
- Curated real lab pcaps captured from owned hardware after trusted access is approved.
- Optional dashboard screenshot capture for report bundles.
- Packaging profile that excludes `node_modules`, `.DS_Store`, and local DB files.

## Risk Notes

- Active mitigation should remain lab-only.
- Wireless monitoring can collect bystander device identifiers; redact and minimize.
- Webhooks can leak evidence; keep disabled unless approved.
- SQLite fallback is acceptable for local replay but not trusted evidence storage.
