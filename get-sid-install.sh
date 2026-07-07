#!/bin/sh
# SID OS — One-command installer
# Boot Alpine from USB, login as root, tether phone, then:
#   wget -qO- https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid-install.sh | sh

set -e
VERSION="0.5.2"
BASE_URL="https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main"
ANSWER_URL="$BASE_URL/installer/sid-answers.conf"

echo "╔══════════════════════════════════════════╗"
echo "║     SID OS Quick Install v$VERSION         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Step 1: Root check
if [ "$(id -u)" -ne 0 ]; then
    echo "✗ Must run as root. Login as root and try again."
    exit 1
fi

# Step 2: Internet check
echo "→ Checking internet..."
if ! ping -c 1 -W 3 google.com >/dev/null 2>&1; then
    echo "  No internet. Trying usb0..."
    ip link set usb0 up 2>/dev/null || true
    udhcpc -i usb0 2>/dev/null || true
    sleep 2
    if ! ping -c 1 -W 3 google.com >/dev/null 2>&1; then
        echo ""
        echo "✗ Need internet."
        echo "  Plug in phone → enable USB tethering → then run:"
        echo "    udhcpc -i usb0"
        echo "  Then re-run this command."
        exit 1
    fi
fi
echo "  ✓ Connected"

# Step 3: Download answer file
echo "→ Downloading install config..."
wget -q -O /tmp/sid-answers.conf "$ANSWER_URL" || {
    echo "✗ Could not download config. Check internet."
    exit 1
}
echo "  ✓ Config downloaded"

# Step 4: Run silent install
echo "→ Installing Alpine to USB (this takes 3-5 minutes)..."
echo ""
setup-alpine -f /tmp/sid-answers.conf 2>&1
echo ""
echo "  ✓ Alpine installed to USB"

# Step 5: Set up SID auto-start for next boot
echo "→ Configuring SID OS..."
cat > /etc/profile.d/sid.sh << 'PROFILE'
# SID OS auto-launch
if [ -f /root/SID-OS/src/main.py ]; then
    cd /root/SID-OS && python3 src/main.py
elif [ -f /root/get-sid.py ]; then
    python3 /root/get-sid.py
fi
PROFILE
chmod +x /etc/profile.d/sid.sh
echo "  ✓ SID configured"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅  ALL DONE!                          ║"
echo "║                                          ║"
echo "║  1. poweroff                            ║"
echo "║  2. Unplug USB, wait 10s, replug        ║"
echo "║  3. Boot from USB (F9)                  ║"
echo "║  4. Login: root / sid123                ║"
echo "║  5. Run:  python3 /root/get-sid.py      ║"
echo "╚══════════════════════════════════════════╝"
