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
- Added redacted `stats_snapshot.json` to report bundles for machine-readable review.
- Added anomaly model lifecycle: offline training CLI, persisted model pickle, metadata JSON, model status API/dashboard exposure.
- Added pluggable OUI CSV loading via `SENTINEL_OUI_CSV` while keeping the static fallback map.
- Wired dashboard views for rogue APs, deauth stats, night owls, ghost networks, vendor names, and anomaly model status.
- Added `/api/health` and richer `/api/stats` summary fields.
- Tightened release packaging excludes and added release manifest generation.

## Still Open

- Bundled/licensed full IEEE OUI database or approved download/update workflow.
- Production anomaly lifecycle across owned field data: curated baseline sets, confidence display, drift retest cadence, and model review notes.
- More complete Wi-Fi 6/7 parsing and 6 GHz hardware profile.
- Curated real lab pcaps captured from owned hardware after trusted access is approved.
- Optional dashboard screenshot capture for report bundles.
- Signed/versioned release artifact workflow after packaging requirements are settled.

## Risk Notes

- Active mitigation should remain lab-only.
- Wireless monitoring can collect bystander device identifiers; redact and minimize.
- Webhooks can leak evidence; keep disabled unless approved.
- SQLite fallback is acceptable for local replay but not trusted evidence storage.
