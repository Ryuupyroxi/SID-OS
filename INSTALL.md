# SID OS — Complete Installation Guide

> **Version**: v0.5.2  
> **Base**: Alpine Linux 3.24.1  
> **Target**: Old laptops/desktops (4GB RAM)  
> **Tested on**: HP Pavilion dv6 (1225dx)  
> **Starting from**: Windows 10 on the HP

---
---

## Quick Install — Step by Step

This is the exact process, in order, with what to type and what you'll see.

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

### Step 6: Find your USB drive name (so you don't wipe Windows)

Type:
```
cat /proc/partitions
```
Press Enter.

You'll see a list of drives. One will say `sda` with a size around 120GB — that is your Windows hard drive. There will be another entry like `sdb` or `sdc` with a size matching your USB stick (8GB, 16GB, 32GB, etc.). That is your USB drive.

Write the USB name down. For the rest of this guide, we'll call it `sdb` — but if yours is `sdc` or `sdd`, use that instead.

---

### Step 7: Download the automated installer config

Type:
```
wget -O /tmp/sid-answers.conf https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/installer/sid-answers.conf
```
Press Enter.

Output shows a progress bar as it downloads (2-3 seconds). When it finishes, the prompt returns.

---

### Step 8: Run the installer with the config file

Type:
```
setup-alpine -f /tmp/sid-answers.conf
```
Press Enter.

---

### Step 9: Answer the installer prompts

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
| | *(shows a numbered list of mirrors — about 30-40 of them)* | | |
| 14 | `Enter mirror number or URL:` | Type the number of the mirror closest to you (23 is USA, 1 is the CDN auto-select) | Enter |
| | *(shows "Updating repository index... Done" — wait for it, may take 10-60 seconds)* | | |
| 15 | `Setup a user? (enter a lower-case loginname, or 'no')` | **`no`** | Enter |
| 16 | `Which ssh server? ('openssh', 'dropbear' or 'none')` | *(nothing — just press Enter)* | Enter |
| 17 | `Allow root ssh login? ('?' for help)` | **`yes`** | Enter |
| 18 | `Enter ssh key or URL for root (or 'none')` | **`none`** | Enter |
| | *(shows "Available disks are:" with disk info — this is info, not a prompt)* | *(wait)* | |
| 19 | `Which disk(s) would you like to use? (or '?' for help or 'none')` | Type the USB name you found in Step 6 — **not** `sda` | Enter |
| | *(shows more info about the selected disk)* | *(wait)* | |
| 20 | `How would you like to use it? ('sys', 'data' or '?' for help)` | **`sys`** | Enter |
| 21 | `WARNING: The following disk(s) will be erased: /dev/sdX. Continue? (y/n)` | **`y`** | Enter |

---

### Step 10: Wait for installation to finish

The installer now formats the USB and copies Alpine onto it. You will see messages like:

```
mke2fs 1.x.x
Creating journal...
Installing system on /dev/sdb...
```

Do not touch anything. This takes 3-5 minutes. When it finishes, you will see:

```
Installation is complete. Please reboot.
```

---

### Step 11: Reboot

Type:
```
poweroff
```
Press Enter. Wait for the laptop to shut down completely (the screen goes black and the fan stops).

---

### Step 12: Boot from the new persistent USB

Unplug the USB drive from the laptop. Wait 10 seconds. Plug the USB drive back in.

Turn the laptop on. Press F9 repeatedly during boot. Select your USB drive from the boot menu.

Wait. You will see:

```
localhost login:
```

Type:
```
root```
Press Enter.

Type the password you set in Step 9 (prompt #9). Press Enter.

You are now logged into Alpine Linux running from the USB drive. Everything you do from here will be saved.

---

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

---

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

Follow the prompt table in Step 9. Every prompt is listed in order. If you hit something not in the table, write it down and stop.

### USB not visible in Windows File Explorer after Rufus

**Normal.** DD Image mode writes a Linux filesystem. Windows can't read it. The drive still works for booting.

---

