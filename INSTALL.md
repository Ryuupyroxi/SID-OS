# SID OS — Complete Installation Guide

> **Version**: v0.5.2  
> **Base**: Alpine Linux 3.24.1  
> **Target**: Old laptops/desktops (4GB RAM)  
> **Tested on**: HP Pavilion dv6 (1225dx)  
> **Starting from**: Windows 10 on the HP

---
---

## Quick Method (recommended)

Skip the 20-prompt setup-alpine by using the answer file. Same result, zero typing.

### What you need

Same as the full method — Alpine ISO, Rufus, USB drive, phone tether.

### Steps

**1-3:** Same as Sections 1-3 — download Alpine, write USB with Rufus (DD mode), boot, login as root, connect tether.

**4. Check which disk is your USB:**

```bash
cat /proc/partitions
```

The internal hard drive (Windows) is usually `sda`. Your USB drive will be the other one — typically `sdb` or `sdc`. Note the name.

**5. Download and run the answer file:**

```bash
wget -O /tmp/sid-answers.conf https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/installer/sid-answers.conf
setup-alpine -f /tmp/sid-answers.conf
```

The installer will still prompt you for:
- **Root password** (type it twice)
- **Mirror number** (pick the closest one)
- **Which disk** (type `sdb` or whatever your USB is — **not** `sda` which is Windows)
- **How to use it** (type `sys`)
- **Confirm** (type `y`)

**6.** When done: `poweroff` → unplug USB → wait 10s → replug → reboot.

> **⚠️ WARNING**: When the installer asks "Which disk(s)?" — do NOT type `sda`. That's your Windows drive. Type the USB name you noted in step 4 (usually `sdb` or `sdc`).

**7.** Login as `root` with the password you set. Then:

```bash
apk add curl python3
curl -sL https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py | python3
```

---



## What you're building

A persistent bootable USB that runs SID OS — an AI-first CLI operating system for old hardware. Alpine Linux is the hidden base. SID auto-launches on boot.

---

## What you need

- HP Pavilion (or any old x86_64 computer)
- USB drive **8GB+** (everything on it gets erased)
- Phone with USB tethering (for internet during install)
- This guide printed or open on another device

---

## Section 1: Download Alpine Linux

Open **Edge** or **Chrome** on the HP (tethered to your phone or on WiFi).

Go to this URL:

```
https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/alpine-standard-3.24.1-x86_64.iso
```

Save the file to your **Downloads** folder. It's about 450MB.

---

## Section 2: Write Alpine to USB with Rufus

### 2.1 — Download Rufus

Go to:

```
https://rufus.ie
```

Click the download link for the **portable version** (not the installer). Save it to Downloads.

### 2.2 — Open Rufus

Double-click `rufus-4.x-portable.exe`. You don't need to install it.

### 2.3 — Set up Rufus

Plug in your USB drive. In Rufus, set every field:

| Field | Setting |
|---|---|
| **Drive** | Select your USB drive (check the size to pick the right one) |
| **Boot selection** | Click SELECT → pick `alpine-standard-3.24.1-x86_64.iso` from your Downloads |
| **Partition scheme** | MBR (greyed out until you pick a mode — leave it) |
| **Target system** | BIOS or UEFI (leave default) |
| **Volume label** | Leave as-is |
| **File system** | Large FAT32 (leave default) |
| **Cluster size** | 4096 bytes (leave default) |

### 2.4 — Start writing

Click **START** at the bottom.

A popup appears with two radio buttons:

- `💿 Write in ISO Image mode` ← DO NOT PICK THIS
- `💾 Write in DD Image mode` ← PICK THIS

Click **OK**.

Rufus warns "This will destroy all data" — click **OK**.

Wait for the green **"Ready"** bar at the bottom. About 2 minutes.

### 2.5 — Verify in Disk Management (optional)

1. Press `Windows + X` → click **Disk Management**
2. Find your USB drive
3. You should see a **1MB FAT partition** (EFI System) and the rest as **unallocated**

This is correct. Alpine's hybrid ISO appears this way in Windows.

### 2.6 — Boot from the USB

1. Leave the USB plugged in
2. Click **Restart** in Windows
3. During boot, immediately start pressing **F9** repeatedly (about once per second)
4. Keep pressing until a boot menu appears
5. Use arrow keys to select your USB drive
6. Press Enter

> **If F9 doesn't work**: Try `F10`, `F12`, or `Esc` instead. HP uses F9 for the boot menu on most models.

### 2.7 — Alpine boots

You'll see a blue screen with Alpine Linux boot options. Press **Enter**.

Wait about 30 seconds. Eventually you'll see:

```
localhost login:
```

Type:
```
root
```
Press **Enter**. No password needed.

You're now logged into Alpine Linux running entirely in RAM. Nothing is written to the USB yet.

---

## Section 3: Connect to the internet

### 3.1 — Phone tether

1. Plug your phone into the HP via USB
2. On your phone, go to **Settings** → **Connections** → **Mobile Hotspot & Tethering**
3. Enable **USB tethering**

### 3.2 — Find the interface

At the Alpine prompt, type:

```bash
ip link show
```

Also check which disk is your USB (so you don't accidentally wipe Windows later):

```bash
cat /proc/partitions
```

The internal drive (Windows) is `sda`. Your USB will be `sdb` or `sdc` — note it.

Look for `usb0`, `enp0s20u1`, or similar. You should see it listed. Also ignore `lo` (loopback).

### 3.3 — Get an IP address

```bash
udhcpc -i usb0
```

(Replace `usb0` with whatever your interface is called)

Wait 3-5 seconds. You should see:

```
udhcpc: lease of 10.x.x.x obtained from 10.x.x.x
```

> **If it says "network is down":** The interface needs to be brought up first.
> ```bash
> ip link set usb0 up
> udhcpc -i usb0
> ```

### 3.4 — Confirm internet works

```bash
ping -c 3 google.com
```

You should see replies.

> **If it doesn't work the first time:** Unplug the USB cable from the phone, wait 5 seconds, plug it back, re-enable tethering, and run `udhcpc -i usb0` again.

---

## Section 4: Install Alpine persistently to USB

Run the Alpine installer:

```bash
setup-alpine
```

This will show a series of prompts. **Follow every line in the table below in exact order.**

### Important notes before you start:

- **Lines marked `(just press Enter)`**: Press Enter only — do not type anything
- **Lines marked with text**: Type the text shown, then press Enter
- If you can't see the bottom of your screen (broken display), just follow the table blindly
- If you see something not in this table, **stop and write it down**

### The complete prompt table

| # | What you see on screen | What to type | Then press |
|---|---|---|---|
| | *(script starts)* | *(nothing, just wait for first prompt)* | |
| 1 | `Select keyboard layout:` | `us` | Enter |
| 2 | `Select variant (or 'abort'):` | `us` | Enter |
| 3 | `Enter system hostname (fully qualified form, e.g. 'foo.example.org')` | `sid` | Enter |
| | *(shows "Available interfaces are: usb0." — this is info, not a prompt)* | *(wait for the actual prompt)* | |
| 4 | `Which one do you want to initialize? (or '?' or 'done')` | *(just press Enter — defaults to usb0)* | Enter |
| 5 | `IPv4 address for usb0? (or 'dhcp', 'none', '?')` | `dhcp` | Enter |
| | *(IP address gets assigned)* | *(wait 3 seconds)* | |
| 6 | `IPv6 address for usb0? (or 'auto', 'dhcp', 'none', '?')` | `none` | Enter |
| 7 | `Do you want to do any manual network configuration? (y/n)` | `n` | Enter |
| 8 | `New password:` | Choose a password (e.g. `sid123`) | Enter |
| 9 | `Retype password:` | Same password again | Enter |
| 10 | `Which timezone are you in? (or '?' or 'none')` | `America/Chicago` *(or your timezone)* | Enter |
| 11 | `HTTP/FTP proxy URL? (e.g. 'http://proxy:8080', or 'none')` | *(just press Enter — defaults to none)* | Enter |
| 12 | `Which NTP client to run? ('busybox', 'openntpd', 'chrony' or 'none')` | *(just press Enter — defaults to busybox)* | Enter |
| | *(shows mirror list with numbers)* | | |
| 13 | `Enter mirror number or URL:` | Pick the number closest to you (e.g. 23 for USA) | Enter |
| | *(shows "Updating repository index... Done")* | *(wait for it to finish — this may take 10-60 seconds)* | |
| 14 | `Setup a user? (enter a lower-case loginname, or 'no')` | **`no`** (must be full word) | Enter |
| 15 | `Which ssh server? ('openssh', 'dropbear' or 'none')` | *(just press Enter — defaults to openssh)* | Enter |
| 16 | `Allow root ssh login? ('?' for help)` | **`yes`** | Enter |
| 17 | `Enter ssh key or URL for root (or 'none')` | **`none`** | Enter |
| | *(shows "Available disks are:" with disk info — this is info)* | *(wait for the actual prompt)* | |
| 18 | `Which disk(s) would you like to use? (or '?' for help or 'none')` | `sdb` *(or whatever your USB showed up as — NOT sda)* | Enter |
| | *(shows info about the selected disk)* | *(wait for the actual prompt)* | |
| 19 | `How would you like to use it? ('sys', 'data' or '?' for help)` | `sys` | Enter |
| 20 | `WARNING: The following disk(s) will be erased: /dev/sda. Continue? (y/n)` | **`y`** | Enter |

### After the last prompt

The installer now formats the USB and installs Alpine. You'll see:

```
mke2fs messages...
Installing system on /dev/sda...
Installation is complete. Please reboot.
```

This takes about **3-5 minutes**.

### Reboot

```bash
poweroff
```

(It may ask to confirm — just press Enter again.)

---

## Section 5: Boot into persistent Alpine

1. **Unplug the USB** from the laptop
2. **Wait 10 seconds**
3. **Plug the USB back in**
4. **Restart the laptop**
5. Spam **F9** during boot
6. Pick the USB drive from the menu
7. Wait for `localhost login:`
8. Type: `root` → Enter
9. Type: the password you set in Section 4, step 8 → Enter
10. Reconnect the phone tether:

```bash
udhcpc -i usb0
```

11. Verify internet:

```bash
ping -c 3 google.com
```

---

## Section 6: Install SID OS

With internet working:

```bash
apk add curl python3
```

Wait for it to install (10-20 seconds). Then:

```bash
curl -sL https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py | python3
```

SID downloads, extracts, and launches automatically. You'll see:

```
sid⏣
```

From now on, **every time you boot this USB**, SID starts automatically. Alpine is underneath but you rarely need to see it.

---

## Section 7: Basic usage

Once inside SID:

| Command | What it does |
|---|---|
| `ai what's my CPU temp?` | Ask the AI anything |
| `sys info` | System information |
| `config set theme vt100` | Switch to retro theme |
| `help` | Full command list |
| `benchmark` | See if your system can run larger AI models |

Type naturally — the AI understands `how much RAM do I have left?` as well as `sys mem`.

---

## Troubleshooting

### "No such file or directory" when running get-sid.py

Make sure curl finished downloading properly:

```bash
curl -sL -o get-sid.py https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py
ls -la get-sid.py
python3 get-sid.py
```

### Internet stops working during setup-alpine

Run this again and retry:

```bash
udhcpc -i usb0
```

### "Network is down" when running udhcpc

The interface needs to be brought up first:

```bash
ip link set usb0 up
udhcpc -i usb0
```

If still failing, unplug and re-plug the phone's USB cable, re-enable tethering, then repeat.


### "python3: not found"

Alpine is minimal — `apk add python3` installs it. If that command failed, run it again:

```bash
apk update
apk add python3
```

### Bottom of screen cut off

Follow the table in Section 4 blindly. Every prompt is listed in order. If you hit something not in the table, write it down and stop.

### USB not visible in Windows File Explorer after Rufus

**Normal.** DD Image mode writes a Linux filesystem. Windows can't read it. The drive still works for booting.

---

## Quick Reference — Section 4 answers only

If you've already booted Alpine and just need the 20 prompt answers:

| # | Answer |
|---|---|
| 1 | `us` |
| 2 | `us` |
| 3 | `sid` |
| 4 | *(Enter)* |
| 5 | `dhcp` |
| 6 | `none` |
| 7 | `n` |
| 8 | *your password* |
| 9 | *same password* |
| 10 | `America/Chicago` |
| 11 | *(Enter)* |
| 12 | *(Enter)* |
| 13 | *pick a mirror number* |
| 14 | **`no`** |
| 15 | *(Enter)* |
| 16 | **`yes`** |
| 17 | **`none`** |
| 18 | `sdb` *(or your USB disk)* |
| 19 | **`sys`** |
| 20 | **`y`** |

---

> Found a bug? Open an issue at: https://github.com/Ryuupyroxi/SID-OS/issues
