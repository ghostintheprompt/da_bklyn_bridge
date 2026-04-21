# Simple OUI lookup for common vendors
# In a production environment, you'd use a full IEEE OUI CSV
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

def resolve_vendor(mac):
    if not mac: return "Unknown"
    
    # Check for Locally Administered Address (Randomized MAC)
    # The second least significant bit of the first byte is the 'U/L' bit.
    # If it's a 1, it's locally administered (likely randomized).
    try:
        first_byte = int(mac.split(':')[0], 16)
        is_local = (first_byte & 0b00000010) != 0
        if is_local:
            return "Randomized (LAA)"
    except:
        pass

    prefix = mac.upper()[:8]
    return VENDORS.get(prefix, "Unknown")
