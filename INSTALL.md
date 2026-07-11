# SID OS — Complete Installation Guide

> **Version**: v1.6.2  
> **Base**: Alpine Linux 3.24.1  
> **Target**: Old laptops/desktops (4GB RAM)  
> **Tested on**: HP Pavilion dv6 (1225dx)  
> **Starting from**: Windows 10 on the HP

---
---

## Quick Install — Step by Step

This guide has two paths. Choose one:

- **Path A — Install to internal drive** (recommended) — The USB is just the installer. Alpine wipes your internal drive and lives there permanently. Uses the answer file for automation.
- **Path B — Persistent USB drive** — Alpine lives on the USB itself. You carry the OS in your pocket. Must run interactively (no answer file).

Pick **Path A** unless you specifically need a portable USB OS.

---

### Step 1: Download Alpine Linux

On your Windows 10 laptop, open a web browser.

Go to this address:
```
https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/alpine-standard-3.24.1-x86_64.iso
```

The file downloads. Save it to your Downloads folder.

---

### Step 2: Download Rufus

Go to:
```
https://rufus.ie
```

Click the download link labeled "Rufus 4.x Portable". Save it to your Downloads folder.

---

### Step 3: Write the Alpine ISO to your USB drive

Open Rufus by double-clicking `rufus-4.x-portable.exe`. No installation needed.

Plug your USB drive into the laptop.

In the Rufus window, do the following:

**Drive:** Click the dropdown and select your USB drive (match the size to confirm it's the right one).

**Boot selection:** Click the SELECT button. Browse to your Downloads folder and pick `alpine-standard-3.24.1-x86_64.iso`. Click Open.

All other fields (Partition scheme, Target system, Volume label, File system, Cluster size) — leave them at their defaults.

Click the **START** button at the bottom of the window.

A popup appears with two options:
- `💿 Write in ISO Image mode` — do NOT pick this
- `💾 Write in DD Image mode` — pick this one

Click OK.

Another popup says "This will destroy all data..." Click OK.

Wait. A progress bar moves. When the bar reaches the end and the bottom of the window says **"Ready"** in green text, it's done. This takes about 2 minutes.

Close Rufus. Leave the USB plugged in.

---

### Step 4: Boot from the USB

> **UEFI users**: If your system uses UEFI (most laptops from 2012+), the ISO provides both BIOS and UEFI boot. You may need to disable **Secure Boot** in your BIOS settings for the UEFI boot to work.

Click the Windows Start menu. Click the power icon. Click **Restart**.

As soon as the screen goes black, start pressing the **F9** key once per second. Keep pressing until a boot menu appears with a list of devices.

If F9 doesn't work, try F10, F12, or Esc instead (HP uses F9 on most models but your model may differ).

The boot menu shows a list. Use the arrow keys to highlight your USB drive. Press Enter.

A blue screen appears with Alpine Linux boot options. Press **Enter**.

Wait 20-40 seconds. Text scrolls by. Eventually the screen shows:

```
localhost login:
```

At this prompt, type:
```
root
```
Press Enter. No password is needed.

You are now logged into Alpine Linux. The operating system is running entirely in your laptop's RAM. Nothing has been written to any hard drive or USB yet.

---

### Step 5: Connect your phone for internet

Plug your phone into the laptop's USB port using its charging cable.

On your phone, go to **Settings** → **Connections** → **Mobile Hotspot & Tethering** and turn on **USB tethering**.

Back at the Alpine prompt, type:
```
ip link show
```
Press Enter.

You'll see a list of network interfaces. Look for one called `usb0`. If you see `usb0`, that is your phone tether.

Now type:
```
ip link set usb0 up
```
Press Enter. No output means it worked.

Then type:
```
udhcpc -i usb0
```
Press Enter.

Wait 3 seconds. You should see:

```
udhcpc: lease of 10.x.x.x obtained from 10.x.x.x
```

(Your IP numbers will be different — that's fine.)

If you see "network is down" instead, run both commands again one at a time:
```
ip link set usb0 up
```
Enter.
```
udhcpc -i usb0
```
Enter.

To confirm the internet works, type:
```
ping -c 3 google.com
```
Press Enter. You should see replies with times like `time=25ms`. Press Ctrl+C after 3 replies to stop.

---

## Path A — Install to Internal Drive (Recommended)

The USB is a bootable installer. Alpine gets installed to your laptop's internal hard drive.

### Step 6A: Identify your internal drive

Type:
```
cat /proc/partitions
```
Press Enter.

You'll see a list of drives:
- `sda` = your internal hard drive (Windows is on this)
- `sdb` (or `sdc`) = your USB installer stick

**The installer will erase `sda` and install Alpine there.** The USB is just the installer tool — like a CD you boot from.

⚠ **Back up anything from Windows you want to keep before continuing.**

### Step 7A: Download the automated installer config

Type:
```
wget -O /tmp/sid-answers.conf https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/installer/sid-answers.conf
```
Press Enter.

Output shows a progress bar as it downloads (2-3 seconds). When it finishes, the prompt returns.

### Step 8A: Run the installer with the config file

Type:
```
setup-alpine -f /tmp/sid-answers.conf
```
Press Enter.

### Step 9A: Answer the installer prompts

The installer is now running. It will show you a series of prompts. Here is every single one, in order, with what to type:

| # | Prompt text | What to type | Then press |
|---|---|---|---|
| 1 | `Select keyboard layout:` | `us` | Enter |
| 2 | `Select variant (or 'abort'):` | `us` | Enter |
| 3 | `Enter system hostname (fully qualified form, e.g. 'foo.example.org')` | `sid` | Enter |
| 4 | *(shows "Available interfaces are: usb0." — this is informational, not a prompt)* | *(wait for the actual prompt to appear)* | |
| 5 | `Which one do you want to initialize? (or '?' or 'done')` | *(nothing — just press Enter — accepts usb0)* | Enter |
| 6 | `IPv4 address for usb0? (or 'dhcp', 'none', '?')` | `dhcp` | Enter |
| 7 | `IPv6 address for usb0? (or 'auto', 'dhcp', 'none', '?')` | `none` | Enter |
| 8 | `Do you want to do any manual network configuration? (y/n)` | `n` | Enter |
| 9 | `New password:` | Type a password you will remember (e.g. `sid123`) — the screen will not show what you type | Enter |
| 10 | `Retype password:` | Type the same password again | Enter |
| 11 | `Which timezone are you in? (or '?' or 'none')` | `America/Chicago` *(or your city/region)* | Enter |
| 12 | `HTTP/FTP proxy URL? (e.g. 'http://proxy:8080', or 'none')` | *(nothing — just press Enter)* | Enter |
| 13 | `Which NTP client to run? ('busybox', 'openntpd', 'chrony' or 'none')` | *(nothing — just press Enter)* | Enter |
| | *(shows "Finding fastest mirror..." and tests mirror speeds)* | | |
| 14 | *(auto-selected — answer file uses -f to pick the fastest)* | *(nothing to type)* | |
| | *(shows "Updating repository index... Done" — wait for it, may take 10-60 seconds)* | | |
| 15 | `Setup a user? (enter a lower-case loginname, or 'no')` | **`no`** | Enter |
| 16 | `Which ssh server? ('openssh', 'dropbear' or 'none')` | *(nothing — just press Enter)* | Enter |
| 17 | `Allow root ssh login? ('?' for help)` | **`yes`** | Enter |
| 18 | `Enter ssh key or URL for root (or 'none')` | **`none`** | Enter |
| | *(shows "Available disks are:" with disk info — this is info, not a prompt)* | *(wait)* | |
| 19 | `Which disk(s) would you like to use? (or '?' for help or 'none')` | Type **`sda`** (your internal drive) | Enter |
| | *(shows more info about the selected disk)* | *(wait)* | |
| 20 | `How would you like to use it? ('sys', 'data' or '?' for help)` | **`sys`** | Enter |
| 21 | `WARNING: The following disk(s) will be erased: /dev/sda. Continue? (y/n)` | **`y`** | Enter |

### Step 10A: Wait for installation to finish

The installer now formats the internal drive and copies Alpine onto it. You will see messages like:

```
mke2fs 1.x.x
Creating journal...
Installing system on /dev/sda...
```

Do not touch anything. This takes 3-5 minutes. When it finishes, you will see:

```
Installation is complete. Please reboot.
```

### Step 11A: Reboot

Type:
```
poweroff
```
Press Enter. Wait for the laptop to shut down completely (the screen goes black and the fan stops).

### Step 12A: Boot from the internal drive

Unplug the USB drive. Turn the laptop back on.

Alpine's boot menu should appear. If it doesn't, press F9/F10/F12 during boot and select your internal drive (not the USB).

Wait. You will see:

```
localhost login:
```

Type:
```
root
```
Press Enter.

Type the password you set in Step 9A (prompt #9). Press Enter.

You are now logged into Alpine Linux installed on your internal drive. Everything you do from here will be saved.

---

## Path B — Persistent USB Drive (Interactive)

Alpine lives on the USB itself. You can boot any computer from it. This must be done interactively because the installer needs to unmount the USB to install onto it.

### Step 6B: Find your USB drive name

Type:
```
cat /proc/partitions
```
Press Enter.

You'll see a list of drives:
- `sda` = your internal hard drive (Windows)
- `sdb` (or `sdc`) = your USB stick

Write the USB name down (e.g. `sdb`). **This will be erased.**

### Step 7B: Run the installer interactively (no answer file)

```
setup-alpine
```
Press Enter. **Do not use the `-f` flag** — we need to answer prompts manually.

### Step 8B: Answer the prompts

The prompts are the same as Path A Steps 1-18 above (keyboard, hostname, network, password, timezone, mirror, user, SSH). Answer them the same way.

When you reach the disk prompt:

- **Prompt: "Available disks are:"** — you may see no disks listed at first because the USB is in use as the boot device.
- **Prompt: "Which disk(s) would you like to use? (or '?' for help or 'none')"** — if no disks are listed, a new prompt will appear:
  - **"No disks available. Try boot media /dev/sdX? (y/n)"** — type **`y`**
  - Alpine copies the boot files to RAM and unmounts the USB.
  - The disk prompt appears again. Now type your USB name (e.g. **`sdb`**).
- **Prompt: "How would you like to use it? ('sys', 'data' or '?' for help)"** — type **`sys`**
- **Prompt: "WARNING: The following disk(s) will be erased: /dev/sdX. Continue?"** — type **`y`**

### Step 9B: Wait and reboot

Same as Steps 10A-11A. The installer writes Alpine to the USB.

### Step 10B: Boot from the persistent USB

When the install finishes and you poweroff:
1. **Leave the USB plugged in** (it IS the installed system now)
2. Turn the laptop back on
3. Press F9 during boot, select the USB drive

Login as `root` with your password. You now have a portable Alpine system on a USB.

---

## Both Paths — Install SID OS

These steps are the same regardless of where Alpine was installed.

### Step 13: Connect to the internet again

```
ip link set usb0 up
```
Enter.

```
udhcpc -i usb0
```
Enter.

```
ping -c 3 google.com
```
Enter to confirm.

### Step 14: Install the SID OS software

Type:
```
apk add curl python3
```
Press Enter. Wait for it to install (10-20 seconds). You'll see package download messages.

Then type:
```
curl -sL https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py | python3
```
Press Enter.

SID downloads and launches automatically. You will see:

```
sid⏣
```
