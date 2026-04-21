# Da Bklyn Bridge Academy: Exam Prep Reference

This guide links features of Da Bklyn Bridge to core concepts in the CompTIA Security+ / PenTest+ / CASP+ exams.

## 1. The 802.11 Stack (Network Basics)
Wireless monitoring requires understanding frame types.

*   **Management Frames**: Beacon, Probe Request, Probe Response, Authentication, Association, Deauthentication.
    *   *Sentinel Link*: "Neighborhood Census" (Beacons) and "Behavioral Probes".
*   **Control Frames**: RTS (Request to Send), CTS (Clear to Send), ACK (Acknowledgement).
    *   *Exam Tip*: These manage access to the medium to prevent collisions (CSMA/CA).
*   **Data Frames**: Contain the actual payload (encrypted if WPA2/3 is used).

## 2. Common Wireless Attacks
*   **Deauthentication Attack**: Sending spoofed deauth frames to kick a user. 
    *   *Goal*: Force a re-handshake to capture the 4-way handshake (EAPOL) for offline cracking.
    *   *Sentinel Link*: "Deauth Watch" detects these spikes.
*   **Rogue Access Point**: An unauthorized AP connected to a secure network.
    *   *Sentinel Link*: "Self Audit" flags APs with your SSID but unfamiliar BSSIDs.
*   **Evil Twin**: A rogue AP using the same SSID as a legitimate one to trick users into connecting.
*   **War Driving**: Probing for wireless networks while moving in a vehicle.
    *   *Sentinel Link*: GPS Logging (see Future Additions) automates this.

## 3. Defense Mechanisms
*   **802.11w (Management Frame Protection)**: Encrypts certain management frames (like Deauth) to prevent spoofing attacks.
    *   *Exam Tip*: Required for WPA3; optional but rare in WPA2.
*   **WPA2 vs WPA3**: 
    *   WPA2 uses 4-way handshake (vulnerable to dictionary attacks).
    *   WPA3 uses SAE (Simultaneous Authentication of Equals) to prevent offline cracking.
*   **MAC Filtering**: Often bypassable because MAC addresses are sent in plaintext in the 802.11 header. (The Sentinel proves this by resolving vendors for every frame).

## 4. Encryption Protocols
*   **WEP**: Deprecated, uses RC4 (vulnerability: IV reuse).
*   **WPA/TKIP**: Intermediate fix for WEP, also uses RC4.
*   **WPA2/AES-CCMP**: Current standard, uses AES.
*   **WPA3/GCMP**: Stronger encryption (AES-256) and forward secrecy.
