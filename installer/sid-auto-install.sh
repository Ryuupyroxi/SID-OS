#!/bin/sh
# SID OS Auto-Installer — One command, zero prompts
# Boot Alpine from USB, login as root, tether phone, then run this.

set -e

SID_VERSION="0.5.2"
ALPINE_MIRROR="https://dl-cdn.alpinelinux.org/alpine/v3.24"
ANSWER_FILE="/tmp/sid-answers.conf"
SID_ANSWER_URL="https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/installer/sid-answers.conf"

echo "╔══════════════════════════════════════════╗"
echo "║     SID OS Auto-Installer v$SID_VERSION      ║"
echo "╚══════════════════════════════════════════╝"

# Step 1: Check we're root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Must run as root"
    exit 1
fi

# Step 2: Check internet
echo ""
echo "[1/5] Checking internet..."
if ! ping -c 1 -W 3 google.com >/dev/null 2>&1; then
    echo "  No internet. Attempting DHCP on usb0..."
    ip link set usb0 up 2>/dev/null || true
    udhcpc -i usb0 2>/dev/null || true
    sleep 2
    if ! ping -c 1 -W 3 google.com >/dev/null 2>&1; then
        echo ""
        echo "ERROR: No internet connection."
        echo "  Plug in phone, enable USB tethering, then run:"
        echo "    udhcpc -i usb0"
        echo "  Then re-run this script."
        exit 1
    fi
fi
echo "  ✓ Online"

# Step 3: Download the answer file
echo ""
echo "[2/5] Downloading install configuration..."
wget -q -O "$ANSWER_FILE" "$SID_ANSWER_URL" 2>/dev/null || {
    # Create answer file manually as fallback
    echo "  Creating answer file directly..."
    cat > "$ANSWER_FILE" << 'EOF'
# SID OS - Automated Alpine Install Keyfile
KEYMAPOPTS="us us"
HOSTNAMEOPTS="sid"
INTERFACESOPTS="auto lo
iface lo inet loopback

auto usb0
iface usb0 inet dhcp
"
TIMEZONEOPTS="America/Chicago"
PROXYOPTS="none"
APKREPOSOPTS="-1"
USEROPTS="none"
SSHDOPTS="openssh"
ROOTSSHKEY="none"
NTPOPTS="busybox"
DISKOPTS="-m sys /dev/sda"
EOF
}
echo "  ✓ Config ready"

# Step 4: Run setup-alpine with the answer file
echo ""
echo "[3/5] Installing Alpine Linux to USB (this takes 3-5 minutes)..."
setup-alpine -f "$ANSWER_FILE" 2>&1 || {
    echo ""
    echo "ERROR: Alpine installation failed."
    echo "  Common causes:"
    echo "  - USB drive not detected (try different port)"
    echo "  - Internet dropped during package download"
    echo "  - Wrong disk name (try 'sdb' instead of 'sda')"
    echo ""
    echo "  To retry with manual disk selection, edit the answer file:"
    echo "    vi $ANSWER_FILE"
    echo "  Change 'sda' to correct disk, then run:"
    echo "    setup-alpine -f $ANSWER_FILE"
    exit 1
}
echo "  ✓ Alpine installed"

# Step 5: Set up auto-boot and install SID on next login
echo ""
echo "[4/5] Configuring SID auto-start..."
cat >> /etc/profile.d/sid.sh << 'PROFILE'
# SID OS Auto-Launcher
if [ -f /root/SID-OS/src/main.py ]; then
    python3 /root/SID-OS/src/main.py
elif [ -f /root/get-sid.py ]; then
    python3 /root/get-sid.py
fi
PROFILE
chmod +x /etc/profile.d/sid.sh
echo "  ✓ Auto-start configured"

echo ""
echo "[5/5] Done!"
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  Installation complete!                  ║"
echo "║                                          ║"
echo "║  1. Type:  poweroff                      ║"
echo "║  2. Unplug USB, wait 10s, replug         ║"
echo "║  3. Reboot, spam F9, pick USB            ║"
echo "║  4. Login as root with password 'sid123' ║"
echo "║  5. Run: python3 /root/get-sid.py        ║"
echo "╚══════════════════════════════════════════╝"
