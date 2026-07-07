# SID OS — Complete Installation Guide

> **Version**: v0.5.2  
> **Base**: Alpine Linux 3.24.1  
> **Target**: Old laptops/desktops with 4GB RAM  
> **Tested on**: HP Pavilion dv6 (1225dx)

---

## What You're Building

SID OS is an AI-first CLI operating system. Alpine Linux is the hidden base — SID launches automatically on boot. The result feels like a single OS.

---

## Two Paths

| Path | Difficulty | What you get |
|------|-----------|--------------|
| **Portable** (Windows/Linux/macOS) | Easy | SID runs as a Python app on top of your existing OS |
| **Full OS** (bootable USB / disk install) | Medium | SID boots directly, replaces Windows |

This guide covers the **Full OS** path.

---

## Path 2 — Full OS Install

### What you need

- HP Pavilion (or any old x86_64 laptop/desktop)
- USB drive **8GB+** (everything on it will be erased)
- Phone with USB tethering (or Ethernet/WiFi adapter)
- Windows 10 on the HP (to prep the USB)

---

### Step 1: Download Alpine 3.24.1 ISO

On the HP, open a browser and download:

```
https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/alpine-standard-3.24.1-x86_64.iso
```

Save it to your Downloads folder.

---

### Step 2: Write the USB

1. Download **Rufus** from `https://rufus.ie` (portable version is fine)
2. Plug in your USB drive
3. Open Rufus
4. Click **SELECT** → pick the Alpine ISO you just downloaded
5. Click **START**
6. A popup appears with two options: **"Write in ISO Image mode"** and **"Write in DD Image mode"**
7. **Choose "Write in DD Image mode"** (this is critical — DD mode writes the ISO raw)
8. Click OK to confirm
9. Wait for "Ready" in green at the bottom
10. Close Rufus, **leave USB plugged in**

---

### Step 3: Boot Alpine (RAM mode)

1. Restart the HP
2. During boot, spam **F9** repeatedly until the boot menu appears
3. Select your USB drive from the list
4. Alpine boots to a blue screen with options — press **Enter**
5. Wait for: `localhost login:`
6. Type: `root` → press Enter (no password)

---

### Step 4: Get online (phone tether)

1. Plug phone into USB port, enable **USB tethering** in phone settings
2. At the Alpine prompt:

```bash
ip link show
```

Look for `usb0` (or `enp0s20u1`). Then:

```bash
udhcpc -i usb0
```

3. Test the connection:

```bash
ping -c 3 google.com
```

If it doesn't work, unplug and re-plug the phone, then run `udhcpc -i usb0` again.

---

### Step 5: Install Alpine persistently to USB

Run:

```bash
setup-alpine
```

Then follow every prompt **in order**:

| # | What you see | Type this | Press |
|---|---|---|---|
| 1 | `Select keyboard layout:` | `us` | Enter |
| 2 | `Select variant (or 'abort'):` | `us` | Enter |
| 3 | `Enter system hostname (fully qualified form...)` | `sid` | Enter |
| 4 | *(shows "Available interfaces are: usb0.")* | *(wait for prompt)* | — |
| 5 | `Which one do you want to initialize? (or '?' or 'done')` | `usb0` (or just Enter) | Enter |
| 6 | `IPv4 address for usb0? (or 'dhcp', 'none', '?')` | `dhcp` | Enter |
| 7 | `IPv6 address for usb0? (or 'auto', 'dhcp', 'none', '?')` | `none` | Enter |
| 8 | `Do you want to do any manual network configuration? (y/n)` | `n` | Enter |
| 9 | `New password:` | choose a password | Enter |
| 10 | `Retype password:` | same password | Enter |
| 11 | `Which timezone are you in? (or '?' or 'none')` | `America/Chicago` (or yours) | Enter |
| 12 | `HTTP/FTP proxy URL? (e.g. 'http://proxy:8080', or 'none')` | *(nothing)* | Enter |
| 13 | `Which NTP client to run? ('busybox', 'openntpd', 'chrony' or 'none')` | *(nothing)* | Enter |
| 14 | `Enter mirror number or URL:` | pick a number from the list | Enter |
| *(wait for "Updating repository index... Done")* | | | |
| 15 | `Setup a user? (enter a lower-case loginname, or 'no')` | **`no`** | Enter |
| 16 | `Which ssh server? ('openssh', 'dropbear' or 'none')` | *(nothing)* | Enter |
| 17 | `Allow root ssh login? ('?' for help)` | **`yes`** | Enter |
| 18 | `Enter ssh key or URL for root (or 'none')` | **`none`** | Enter |
| 19 | `Which disk(s) would you like to use? (or '?' for help or 'none')` | `sda` | Enter |
| 20 | *(shows disk info — just info)* | *(wait)* | — |
| 21 | `How would you like to use it? ('sys', 'data' or '?' for help)` | **`sys`** | Enter |
| 22 | `WARNING: The following disk(s) will be erased: /dev/sda. Continue? (y/n)` | **`y`** | Enter |

> **Total: 16 prompts that need input** (the rest accept defaults with just Enter).

The installer will format the USB and install Alpine. It takes 2-5 minutes.

When you see:

```
Installation is complete. Please reboot.
```

Type:

```bash
poweroff
```

---

### Step 6: Boot into persistent Alpine

1. Unplug the USB, wait 10 seconds
2. Plug it back in
3. Reboot, spam **F9**, pick the USB
4. Login: `root` → enter the password you chose in Step 5 (#9)
5. Reconnect phone tether:

```bash
udhcpc -i usb0
```

6. Test: `ping -c 3 google.com`

---

### Step 7: Install SID OS

```bash
apk add curl python3
curl -sL https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py | python3
```

SID downloads, extracts, and launches. You'll see the SID prompt:

```
sid⏣
```

From this point on, SID launches automatically every time you boot.

---

### Step 8 (optional): Build the all-in-one SID ISO

While booted into Alpine with SID installed:

```bash
apk add sudo xorriso squashfs-tools
cd /root/SID-OS/build/scripts
./build-live-iso.sh
```

Output: `/root/SID-OS/build/output/sid-0.5.2-live-x86_64.iso`

Upload to GitHub:

```bash
apk add github-cli
gh auth login
gh release upload v0.5.2 /root/SID-OS/build/output/sid-0.5.2-live-x86_64.iso
```

---

## Troubleshooting

### "ip link show" doesn't show usb0
- Make sure USB tethering is enabled in your phone's settings
- Try a different USB port
- Unplug and re-plug the USB cable between HP and phone

### Internet keeps dropping during setup-alpine
- Run `udhcpc -i usb0` again to renew the IP
- If it keeps failing, try a different mirror in Step 5 (#14)

### Bottom of screen cut off / can't see prompts
- Every prompt from Step 5 is listed in order above
- If you see text you don't recognize, **stop** and write down exactly what it says
- Do not guess — ask for help

### Can't see the USB in File Explorer on Windows
- **Normal**. DD Image mode writes a Linux filesystem that Windows can't read
- The USB is working fine — it's only bootable on the HP, not browsable in Windows

---

## File an Issue

Found something wrong in this guide? Open an issue at:
`https://github.com/Ryuupyroxi/SID-OS/issues`
