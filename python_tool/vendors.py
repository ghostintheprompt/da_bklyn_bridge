import csv
import os
from functools import lru_cache
from pathlib import Path


VENDORS = {
    "00:03:93": "Apple",
    "00:25:00": "Apple",
    "8C:85:90": "Apple",
    "F8:27:93": "Apple",
    "00:16:E3": "Samsung",
    "00:21:7C": "Samsung",
    "00:0C:E5": "Oracle",
    "00:0B:86": "Aruba",
    "00:14:22": "Dell",
    "00:1D:09": "Dell",
    "00:21:00": "Cisco",
    "00:21:A0": "Cisco",
    "3C:CE:73": "Espressif",
    "24:B2:DE": "Espressif",
    "B4:E6:2D": "Espressif",
    "00:E0:4C": "Realtek",
    "00:1E:E5": "Intel",
    "AC:D1:B8": "Intel",
    "DC:A6:32": "Raspberry Pi",
    "B8:27:EB": "Raspberry Pi",
}


def normalize_oui(value):
    if not value:
        return None
    cleaned = "".join(ch for ch in value.upper() if ch in "0123456789ABCDEF")
    if len(cleaned) < 6:
        return None
    return ":".join([cleaned[:2], cleaned[2:4], cleaned[4:6]])


def is_locally_administered(mac):
    try:
        first_byte = int(str(mac).split(':')[0], 16)
        return (first_byte & 0b00000010) != 0
    except (TypeError, ValueError, IndexError):
        return False


def _value(row, *names):
    lowered = {key.lower().strip(): value for key, value in row.items() if key is not None}
    for name in names:
        value = lowered.get(name.lower())
        if value:
            return value.strip()
    return None


@lru_cache(maxsize=4)
def load_oui_file(path):
    """Load an IEEE-style OUI CSV or a simple prefix,vendor CSV."""
    csv_path = Path(path)
    if not csv_path.exists():
        return {}

    loaded = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        has_header = csv.Sniffer().has_header(sample)
        if has_header:
            reader = csv.DictReader(handle)
            for row in reader:
                prefix = normalize_oui(_value(row, "Assignment", "OUI", "MAC Prefix", "prefix"))
                vendor = _value(row, "Organization Name", "Organization", "Vendor", "vendor")
                if prefix and vendor:
                    loaded[prefix] = vendor
        else:
            reader = csv.reader(handle)
            for row in reader:
                if len(row) >= 2:
                    prefix = normalize_oui(row[0])
                    vendor = row[1].strip()
                    if prefix and vendor:
                        loaded[prefix] = vendor
    return loaded


def vendor_map(oui_path=None):
    path = oui_path or os.environ.get("SENTINEL_OUI_CSV")
    if not path:
        return VENDORS
    return {**VENDORS, **load_oui_file(path)}


def resolve_vendor(mac, oui_path=None):
    if not mac:
        return "Unknown"

    # Check for Locally Administered Address (Randomized MAC)
    # The second least significant bit of the first byte is the 'U/L' bit.
    # If it's a 1, it's locally administered (likely randomized).
    if is_locally_administered(mac):
        return "Randomized (LAA)"

    prefix = normalize_oui(mac)
    return vendor_map(oui_path).get(prefix, "Unknown")
