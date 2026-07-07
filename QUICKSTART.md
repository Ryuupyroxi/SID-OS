# SID OS — Quick Install Guide

> **Version**: v0.5.2 | **Base**: Alpine 3.24.1  
> **For people who've done this before. Need every detail? Read** `INSTALL.md`

---

This guide has two paths (see INSTALL.md for full details):
- **Path A — Internal drive** (recommended, uses answer file)
- **Path B — Persistent USB** (interactive, no answer file)

This quickstart covers Path A.

## What you need

- USB drive **8GB+** (everything erased)
- Phone with USB tethering
- Windows 10 on the HP (to prep the USB)

---

## Step 1: Download + write Alpine

Download Alpine 3.24.1 ISO:
```
https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/alpine-standard-3.24.1-x86_64.iso
```

Download Rufus portable from `https://rufus.ie`. Open it.

Select your USB drive → click SELECT → pick the Alpine ISO → click **START**.

When the popup appears, pick **"Write in DD Image mode"** (not ISO mode). Wait for "Ready".

## Step 2: Boot + login

Restart the HP. Spam **F9** during boot. Pick the USB drive. Press Enter at the Alpine menu.

At `localhost login:`, type `root` and press Enter.

## Step 3: Tether phone

Plug phone in, enable USB tethering in phone settings.

```bash
ip link set usb0 up
udhcpc -i usb0
```

Test: `ping -c 3 google.com`

## Step 4: Check your USB drive name

```bash
cat /proc/partitions
```

`sda` = internal drive, `sdb` = USB installer. We install to `sda`.

## Step 5: Run automated installer

```bash
wget -O /tmp/sid-answers.conf https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/installer/sid-answers.conf
setup-alpine -f /tmp/sid-answers.conf
```

The installer asks you for these::
- **Password** (type it twice)
- **Mirror** (auto-selected — the answer file uses -f to find the fastest, just wait)
- **Which disk** (type **`sda`** — your internal drive)
- **How to use it** (type `sys`)
- **Confirm** (type `y`)

Everything else is automated.

## Step 6: Reboot

```bash
poweroff
```

Unplug USB, wait 10s, replug, reboot (F9), pick USB, login as `root` with your password.

## Step 7: Install SID

```bash
ip link set usb0 up
udhcpc -i usb0
apk add curl python3
curl -sL https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py | python3
```

You'll see the `sid⏣` prompt. You're done.
