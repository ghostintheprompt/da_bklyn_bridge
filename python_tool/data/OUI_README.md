# OUI Data

`vendors.py` ships with a small static fallback map and can now load a fuller
OUI CSV without code changes.

Set:

```bash
export SENTINEL_OUI_CSV=/path/to/oui.csv
```

Supported shapes:

- IEEE-style CSV with `Assignment` and `Organization Name` columns.
- Simple two-column CSV: `prefix,vendor`.

Keep downloaded vendor databases out of shared evidence bundles unless the
license and data-handling plan permit redistribution.
