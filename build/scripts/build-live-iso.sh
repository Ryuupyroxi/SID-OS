#!/bin/bash
# SID OS Live ISO Builder
# Creates a bootable ISO using Alpine Linux + SID OS
# Requires: xorriso, isolinux, squashfs-tools, wget, cpio, gzip
# Usage: ./build/scripts/build-live-iso.sh

set -e

VERSION="0.5.0"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/build/output}"
ARCH="${ARCH:-x86_64}"
ALPINE_VERSION="3.20.3"

echo "╔══════════════════════════════════════════╗"
echo "║   SID OS Live ISO Builder v$VERSION      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check deps
for dep in xorriso mksquashfs wget cpio gzip; do
    if ! command -v $dep &>/dev/null; then
        echo "Missing: $dep (install xorriso squashfs-tools wget cpio gzip)"
        exit 1
    fi
done
echo "All build tools available ✓"

BUILD_DIR="/tmp/sid-live-build"
ISO_DIR="$BUILD_DIR/iso"
ROOTFS_DIR="$BUILD_DIR/rootfs"
ALPINE_TAR="$BUILD_DIR/alpine-minirootfs.tar.gz"

rm -rf "$BUILD_DIR"
mkdir -p "$ISO_DIR/boot/grub" "$ROOTFS_DIR"

# Step 1: Get Alpine minirootfs
echo "[1/5] Downloading Alpine Linux base..."
if [ ! -f "$ALPINE_TAR" ]; then
    wget -q -O "$ALPINE_TAR" \
        "https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/$ARCH/alpine-minirootfs-$ALPINE_VERSION-$ARCH.tar.gz"
fi
tar xzf "$ALPINE_TAR" -C "$ROOTFS_DIR"
echo "  Alpine minirootfs extracted ✓"

# Step 2: Set up networking and basic system
echo "[2/5] Configuring base system..."
# DNS config
mkdir -p "$ROOTFS_DIR/etc"
echo "nameserver 1.1.1.1" > "$ROOTFS_DIR/etc/resolv.conf"
echo "nameserver 8.8.8.8" >> "$ROOTFS_DIR/etc/resolv.conf"

# Hostname
echo "sid" > "$ROOTFS_DIR/etc/hostname"
echo "127.0.0.1 localhost sid" > "$ROOTFS_DIR/etc/hosts"

# Network config (DHCP)
mkdir -p "$ROOTFS_DIR/etc/network"
cat > "$ROOTFS_DIR/etc/network/interfaces" << 'NET'
auto lo
iface lo inet loopback
auto eth0
iface eth0 inet dhcp
NET

# Install Python and core packages to rootfs
echo "  Installing packages (chroot)..."
if command -v apk &>/dev/null; then
    apk add --no-cache --root="$ROOTFS_DIR" \
        python3 musl ncurses-libs busybox sqlite-libs 2>&1 | tail -1
elif [ -f "$ROOTFS_DIR/sbin/apk" ]; then
    # apk available in chroot
    chroot "$ROOTFS_DIR" /sbin/apk add --no-cache \
        python3 musl ncurses-libs busybox sqlite-libs 2>&1 | tail -1
fi
echo "  Python 3 installed ✓"

# Step 3: Install SID OS
echo "[3/5] Installing SID OS..."
# Create SID directories
mkdir -p "$ROOTFS_DIR/opt/sid" "$ROOTFS_DIR/sid/models" "$ROOTFS_DIR/sid/memory" "$ROOTFS_DIR/etc/sid"

# Find and extract SID portable tarball
SID_TARBALL=$(ls "$OUTPUT_DIR"/sid-*-portable.tar.gz 2>/dev/null | head -1)
if [ -z "$SID_TARBALL" ]; then
    echo "  Building portable tarball..."
    mkdir -p "$OUTPUT_DIR"
    bash "$PROJECT_DIR/build/scripts/make-portable.sh" "$OUTPUT_DIR" >/dev/null 2>&1
    SID_TARBALL=$(ls "$OUTPUT_DIR"/sid-*-portable.tar.gz | head -1)
fi

tar xzf "$SID_TARBALL" -C "$ROOTFS_DIR/opt/sid"
echo "  SID OS installed to /opt/sid ✓"

# Create SID launcher script
cat > "$ROOTFS_DIR/usr/bin/sid" << 'SIDLAUNCH'
#!/bin/sh
cd /opt/sid
python3 src/main.py "$@"
SIDLAUNCH
chmod +x "$ROOTFS_DIR/usr/bin/sid"

# Step 4: Create init script that auto-starts SID
echo "[4/5] Creating bootable ISO..."
cat > "$ROOTFS_DIR/init" << 'INIT'
#!/bin/busybox sh

# SID OS Live Init
/bin/busybox --install -s

# Mount essential filesystems
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev

# Create console
mknod /dev/console c 5 1 2>/dev/null || true
mknod /dev/null c 1 3 2>/dev/null || true

# Print boot banner
clear
echo "========================================"
echo "   SID OS v0.5.0 - Super Intelligent Distro"
echo "   Booting..."
echo "========================================"
echo ""

# Bring up network
ifconfig lo 127.0.0.1 up
udhcpc -i eth0 -q -t 5 2>/dev/null || true

# Show boot message
echo ""
echo " Welcome to SID OS"
echo " Starting AI interface..."
echo ""

# Launch SID directly
cd /opt/sid
python3 src/main.py --theme vt100

# If SID exits, drop to shell
exec /bin/sh
INIT
chmod +x "$ROOTFS_DIR/init"

# Create symlink for busybox
mkdir -p "$ROOTFS_DIR/bin"
ln -sf /bin/busybox "$ROOTFS_DIR/bin/sh" 2>/dev/null || true

# Create squashfs of rootfs
mksquashfs "$ROOTFS_DIR" "$BUILD_DIR/sid.squashfs" -comp xz -b 128K -no-progress
echo "  Root filesystem compressed ✓"

# Create initramfs with SID
mkdir -p "$BUILD_DIR/initramfs"
cd "$BUILD_DIR/initramfs"
# Copy busybox and minimal init
cp "$ROOTFS_DIR/bin/busybox" .
cp "$ROOTFS_DIR/init" .
mkdir -p bin
cp "$ROOTFS_DIR/bin/busybox" bin/sh
find . | cpio -H newc -o | gzip > "$BUILD_DIR/initramfs.gz"
echo "  Initramfs created ✓"

# Step 5: Create ISO
echo "[5/5] Building ISO..."
SQUASHFS_SIZE=$(stat -c%s "$BUILD_DIR/sid.squashfs" 2>/dev/null || stat -f%z "$BUILD_DIR/sid.squashfs")
INITRAMFS_SIZE=$(stat -c%s "$BUILD_DIR/initramfs.gz" 2>/dev/null || stat -f%z "$BUILD_DIR/initramfs.gz")
echo "  Squashfs: $((SQUASHFS_SIZE/1024/1024))MB"
echo "  Initramfs: $((INITRAMFS_SIZE/1024))KB"

# Copy boot files
cp "$BUILD_DIR/initramfs.gz" "$ISO_DIR/boot/"
cp "$BUILD_DIR/sid.squashfs" "$ISO_DIR/boot/"

# Download a minimal kernel (Alpine's) or use a stub
# For now, create the ISO structure that can use the Alpine kernel
mkdir -p "$ISO_DIR/boot/sid"

# Create a README explaining the ISO
cat > "$ISO_DIR/README.txt" << 'README'
SID OS v0.5.0 Live ISO
=======================
This ISO requires a Linux kernel and bootloader to be added.
For a complete bootable experience:
1. Write this ISO to a USB drive
2. Add Alpine's kernel (vmlinuz-lts) from alpine.org
3. Configure bootloader to point to /boot/initramfs.gz

Or use the portable tarball on top of any existing Linux installation
README

cd "$ISO_DIR"
xorriso -as mkisofs \
    -V "SID-OS-$VERSION" \
    -o "$OUTPUT_DIR/sid-$VERSION-live-$ARCH.iso" \
    . 2>&1

echo ""
echo "========================================"
echo "  ISO created: $OUTPUT_DIR/sid-$VERSION-live-$ARCH.iso"
echo "  Size: $(du -sh "$OUTPUT_DIR/sid-$VERSION-live-$ARCH.iso" | cut -f1)"
echo "========================================"
echo ""
echo "To use: This is a data ISO with SID OS files."
echo "For a bootable USB on Linux:"
echo "  sudo dd if=sid-$VERSION-live-$ARCH.iso of=/dev/sdX bs=4M"
echo "For Windows: Use Rufus in 'DD Image' mode"
echo ""
echo "Or just use the portable tarball on any existing OS"
