# Start Here

Da Bklyn Bridge is now best treated as an app-like field console, not a heavy
native Mac app.

## What To Plug In

- **Alfa USB Wi-Fi adapter:** yes, plug it into the Mac, then pass it into the
  Linux VM through UTM. That is what enables monitor-mode capture.
- **Alfa router/AP:** useful as your owned lab target. It does not replace the
  monitor-mode adapter.

## What To Run Today

On the Mac:

```bash
npm install
npm run app
```

If the API is running inside the VM:

```bash
npm run app -- --api http://<VM_IP>:5000
```

Inside the Linux VM:

```bash
bash scripts/m1_vm_bootstrap.sh --rtl8812au --with-aircrack
bash scripts/alfa_doctor.sh
bash scripts/run_passive.sh --interface wlan0
```

## Should This Be A Native App?

Not yet. The smart 2026 version is:

1. **Mac dashboard:** app-like local web console for preflight, evidence review,
   and portfolio polish.
2. **Linux VM capture appliance:** tiny UTM/Kali or Debian ARM VM that owns USB,
   drivers, monitor mode, and capture.
3. **Future native wrapper:** Tauri/Electron only after the workflow is stable
   and you want double-click packaging.

That keeps disk use low, keeps the risky hardware pieces where they actually
work, and still presents like a serious tool.
