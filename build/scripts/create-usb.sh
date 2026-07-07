#!/bin/bash
# SID OS USB Creator — Creates a bootable USB drive
# Works on Linux and macOS (for Windows, see instructions below)
# Usage: sudo ./create-usb.sh /dev/sdX

set -e

VERSION="0.5.1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║     SID OS USB Creator v$VERSION          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo $0 /dev/sdX"
    echo ""
    echo "⚠ WARNING: This will DESTROY ALL DATA on the target drive!"
    echo ""
    echo "Windows users: use Rufus (rufus.ie) with an Alpine Linux ISO"
    echo "1. Download Alpine Linux: https://alpinelinux.org/downloads/"
    echo "2. Download SID portable tarball from GitHub Releases"
    echo "3. Use Rufus to write Alpine ISO to USB"
    echo "4. After booting Alpine, download and run SID"
    exit 1
fi

DEVICE="$1"
if [ -z "$DEVICE" ]; then
    echo "Usage: sudo $0 /dev/sdX"
    echo "Example: sudo $0 /dev/sdb"
    echo ""
    lsblk -d -o NAME,SIZE,MODEL | grep -v loop
    exit 1
fi

echo "Target device: $DEVICE"
echo "All data on $DEVICE will be destroyed!"
echo ""
read -p "Type YES to continue: " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "[1/4] Downloading Alpine Linux base..."
ALPINE_ISO=$(mktemp)
wget -q -O "$ALPINE_ISO" "https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/x86_64/alpine-standard-3.20.3-x86_64.iso"
echo "  Downloaded Alpine ISO"

echo "[2/4] Creating bootable USB..."
dd if="$ALPINE_ISO" of="$DEVICE" bs=4M status=progress conv=fsync
echo "  Base ISO written"

echo "[3/4] Extracting SID OS to USB data partition..."
# Create ext4 partition for SID data
echo -e "n\np\n\n\n\nw" | fdisk "$DEVICE"
PARTITION="${DEVICE}2"
sleep 2
mkfs.ext4 "$PARTITION"
mkdir -p /mnt/sid-usb
mount "$PARTITION" /mnt/sid-usb

# Copy SID portable
if [ -f "$PROJECT_DIR/build/output/sid-$VERSION-portable.tar.gz" ]; then
    cp "$PROJECT_DIR/build/output/sid-$VERSION-portable.tar.gz" /mnt/sid-usb/
    echo "  SID portable release copied"
else
    echo "  Building portable release first..."
    bash "$PROJECT_DIR/build/scripts/make-portable.sh" /tmp/sid-build
    cp /tmp/sid-build/sid-$VERSION-portable.tar.gz /mnt/sid-usb/
fi

# Create auto-setup script
cat > /mnt/sid-usb/setup-sid.sh << 'SETUP'
#!/bin/sh
# Auto-setup SID OS after Alpine Linux boots
echo "╔══════════════════════════════════════════╗"
echo "║       SID OS - Quick Setup               ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Extracting SID OS..."
tar xzf /media/sid-usb/sid-*.tar.gz -C /home/sid/
echo "Starting SID OS..."
cd /home/sid/sid-*
python3 src/main.py --theme vt100
SETUP
chmod +x /mnt/sid-usb/setup-sid.sh

umount /mnt/sid-usb
echo "  SID data partition written"

echo "[4/4] Done!"
echo ""
echo "USB drive created successfully!"
echo ""
echo "To use:"
echo "  1. Boot from USB (may need to disable Secure Boot)"
echo "  2. Alpine Linux will start in RAM"
echo "  3. Run: sh /media/sid-usb/setup-sid.sh"
echo "  4. SID OS will start"
echo ""
echo "Or for Windows: use Rufus with Alpine ISO, then copy SID tarball manually"
rm -f "$ALPINE_ISO"
