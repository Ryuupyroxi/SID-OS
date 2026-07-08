#!/bin/sh
# SID OS - Super Intelligent Distro
# Alpine Linux bootstrap — turns Alpine into SID OS
# Usage: wget -O - https://git.io/... | sh
# Or: curl -L https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/build/alpine-setup.sh | sh

set -e

VERSION="1.6.1"
BRANCH="main"
BASE="https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/$BRANCH"
SID_TARBALL="$BASE/build/output/sid-$VERSION-portable.tar.gz"

echo "================================================"
echo "  SID OS v$VERSION - Alpine Linux Setup"
echo "  Turns Alpine into a Super Intelligent Distro"
echo "================================================"
echo ""

# Requirements check
if [ ! -f /etc/alpine-release ]; then
    echo "This script must be run on Alpine Linux."
    echo "Install Alpine first, then run this script."
    exit 1
fi

ALPINE_VER=$(cat /etc/alpine-release)
echo "  Alpine version: $ALPINE_VER"
echo "  SID OS version: $VERSION"
echo ""

# Step 1: Install system dependencies
echo "[1/5] Installing system packages..."
apk update -q
apk add -q python3 py3-pip py3-numpy py3-psutil py3-pillow py3-yaml py3-requests sudo wget curl

# Optional but recommended
apk add -q espeak-ng 2>/dev/null || true

# Step 2: Create SID user and directories
echo "[2/5] Creating SID OS directories..."
mkdir -p /opt/sid /sid/models /sid/memory /sid/logs /etc/sid

# Step 3: Download and install SID OS
echo "[3/5] Downloading SID OS..."
wget -q -O /tmp/sid.tar.gz "$SID_TARBALL" || \
    curl -sL -o /tmp/sid.tar.gz "$SID_TARBALL"
tar xzf /tmp/sid.tar.gz -C /opt/sid
rm -f /tmp/sid.tar.gz

# Step 4: Create SID command
echo "[4/5] Installing SID command..."
cat > /usr/local/bin/sid << 'CMD'
#!/bin/sh
cd /opt/sid
exec /usr/bin/python3 src/main.py "$@"
CMD
chmod +x /usr/local/bin/sid

# Step 5: Configure auto-start
echo "[5/5] Configuring auto-start..."
mkdir -p /etc/profile.d
cat > /etc/profile.d/sid.sh << PROFILE
# Auto-start SID OS on tty1 (physical console)
if [ "\$(tty)" = "/dev/tty1" ]; then
    clear
    cat << BANNER
===============================================
  SID OS v$VERSION - Super Intelligent Distro
  Alpine Linux base
===============================================
BANNER
    sleep 1
    sid
fi
PROFILE
chmod +x /etc/profile.d/sid.sh

# Add /usr/local/bin to PATH if not already
if ! grep -q "/usr/local/bin" /etc/profile 2>/dev/null; then
    echo 'export PATH=\$PATH:/usr/local/bin' >> /etc/profile
fi

echo ""
echo "==============================================="
echo "  ✅ SID OS installed on Alpine Linux!"
echo "==============================================="
echo ""
echo "  Quick start:"
echo "    sid       - Launch SID OS"
echo "    sid help  - Show commands"
echo ""
echo "  To auto-start on boot:"
echo "    echo '/usr/local/bin/sid' >> ~/.profile"
echo ""
echo "  To make a bootable SID OS USB:"
echo "    1. Write Alpine ISO to USB: dd if=alpine.iso of=/dev/sdX"
echo "    2. Boot Alpine, run this script"
echo "    3. Run: setup-alpine (set up disk, user, etc.)"
echo "    4. Reboot into SID OS"
echo ""
