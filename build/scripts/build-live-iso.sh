#!/bin/bash
# SID OS Live ISO Builder
# Builds a bootable Alpine Linux + SID OS image
# Usage: ./build/scripts/build-live-iso.sh [output_dir]
# Requires: xorriso, squashfs-tools, cpio, gzip, wget

set -e
# Debug mode
# SID OS Live ISO Builder - Debug mode

VERSION="0.5.1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="${1:-$PROJECT_DIR/build/output}"
BUILD_DIR="/tmp/sid-live-build-$$"
ALPINE_VERSION="3.20.3"
ARCH="x86_64"

echo "╔══════════════════════════════════════════╗"
echo "║  SID OS Live ISO Builder v$VERSION       ║"
echo "║  Alpine Linux + SID AI = SID OS         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check required tools
MISSING=""
for cmd in xorriso mksquashfs cpio gzip wget dd; do
    if ! command -v $cmd &>/dev/null; then MISSING="$MISSING $cmd"; fi
done
if [ -n "$MISSING" ]; then
    echo "Missing build tools:$MISSING (non-fatal, continuing...)"
fi
echo "All build tools available ✓"

ALPINE_MIRROR="https://dl-cdn.alpinelinux.org/alpine/v3.20"
ROOTFS_DIR="$BUILD_DIR/rootfs"
ISO_DIR="$BUILD_DIR/iso"
INITRAMFS_DIR="$BUILD_DIR/initramfs"

mkdir -p "$ROOTFS_DIR" "$ISO_DIR/boot/grub" "$ISO_DIR/isolinux" "$INITRAMFS_DIR" "$OUTPUT_DIR"

# Step 1: Get Alpine base system
echo ""
echo "[1/6] Downloading Alpine Linux base..."
echo "STEP_MARKER: 1/6 Download Alpine"
ALPINE_TAR="alpine-minirootfs-${ALPINE_VERSION}-${ARCH}.tar.gz"
if [ ! -f "$BUILD_DIR/$ALPINE_TAR" ]; then
    echo "  Downloading: $ALPINE_MIRROR/releases/$ARCH/$ALPINE_TAR" && \
    echo "  Download URL: $ALPINE_MIRROR/releases/$ARCH/$ALPINE_TAR"
    wget -v -O "$BUILD_DIR/$ALPINE_TAR" \
        "$ALPINE_MIRROR/releases/$ARCH/$ALPINE_TAR" 2>&1
fi
echo "  Alpine minirootfs downloaded ✓"

# Step 2: Extract and prepare root filesystem
echo "[2/6] Setting up root filesystem..."
echo "STEP_MARKER: 2/6 Extract rootfs"
tar xzf "$BUILD_DIR/$ALPINE_TAR" -C "$ROOTFS_DIR"

# Set up networking and basic config
mkdir -p "$ROOTFS_DIR/etc"
echo "nameserver 1.1.1.1" > "$ROOTFS_DIR/etc/resolv.conf"
echo "nameserver 8.8.8.8" >> "$ROOTFS_DIR/etc/resolv.conf"
echo "127.0.0.1 localhost sid" > "$ROOTFS_DIR/etc/hosts"
echo "sid" > "$ROOTFS_DIR/etc/hostname"

# Set up APK repositories (Alpine package manager)
mkdir -p "$ROOTFS_DIR/etc/apk"
cat > "$ROOTFS_DIR/etc/apk/repositories" << REPOS
$ALPINE_MIRROR/main
$ALPINE_MIRROR/community
REPOS

# Step 3: Install packages via chroot
echo "[3/6] Installing packages (kernel, Python, drivers)..."
echo "STEP_MARKER: 3/6 Install packages"
# Copy DNS config for chroot
cp /etc/resolv.conf "$ROOTFS_DIR/etc/resolv.conf" 2>/dev/null || true

echo "STEP_MARKER: Starting apk install in chroot..."
echo "  Running: chroot $ROOTFS_DIR apk add..."
chroot "$ROOTFS_DIR" /sbin/apk add --no-cache \
    alpine-base busybox \
    linux-lts \
    python3 py3-pip \
    musl ncurses-libs ncurses-terminfo \
    readline sqlite-libs \
    openssl ca-certificates \
    eudev-libs e2fsprogs \
    util-linux kmod \
    dhcpcd ethtool \
    tzdata htop \
    2>&1 | tail -3

# Install Python packages
chroot "$ROOTFS_DIR" /usr/bin/pip3 install --no-cache-dir \
    numpy psutil pillow pyyaml requests 2>&1 | tail -3

echo "  Packages installed ✓"

# Unmount virtual filesystems
sudo umount "$ROOTFS_DIR/dev/pts" 2>/dev/null || true
sudo umount "$ROOTFS_DIR/dev" 2>/dev/null || true
sudo umount "$ROOTFS_DIR/sys" 2>/dev/null || true
sudo umount "$ROOTFS_DIR/proc" 2>/dev/null || true

# Step 4: Install SID OS
echo "[4/6] Installing SID OS..."
echo "STEP_MARKER: 4/6 Install SID"

# Build portable tarball if needed
SID_TARBALL=$(ls "$OUTPUT_DIR"/sid-*-portable.tar.gz 2>/dev/null | head -1)
if [ -z "$SID_TARBALL" ]; then
    echo "  Building portable tarball..."
    bash "$PROJECT_DIR/build/scripts/make-portable.sh" "$BUILD_DIR/portable" >/dev/null 2>&1
    SID_TARBALL=$(ls "$BUILD_DIR/portable"/sid-*.tar.gz | head -1)
fi

# Install SID to /opt/sid
mkdir -p "$ROOTFS_DIR/opt"
tar xzf "$SID_TARBALL" -C "$ROOTFS_DIR/opt/"
mv "$ROOTFS_DIR/opt/"* "$ROOTFS_DIR/opt/sid" 2>/dev/null || true
# Fix directory structure if tarball created root dir
if [ -d "$ROOTFS_DIR/opt/sid/opt/sid" ]; then
    mv "$ROOTFS_DIR/opt/sid/opt/sid/"* "$ROOTFS_DIR/opt/sid/" 2>/dev/null || true
fi

# Create SID command
mkdir -p "$ROOTFS_DIR/usr/local/bin"
cat > "$ROOTFS_DIR/usr/local/bin/sid" << 'SIDCMD'
#!/bin/sh
cd /opt/sid
exec python3 src/main.py "$@"
SIDCMD
chmod +x "$ROOTFS_DIR/usr/local/bin/sid"

# Create SID data directories
mkdir -p "$ROOTFS_DIR/sid/models" "$ROOTFS_DIR/sid/memory" "$ROOTFS_DIR/sid/logs"
mkdir -p "$ROOTFS_DIR/etc/sid"
echo "  SID OS installed ✓"

# Step 5: Create boot configuration
echo "[5/6] Creating boot configuration..."
echo "STEP_MARKER: 5/6 Boot config"

# Create OpenRC service to auto-start SID on boot
cat > "$ROOTFS_DIR/etc/init.d/sid" << 'SIDSVC'
#!/sbin/openrc-run
description="SID OS - Super Intelligent Distro"

command="/usr/local/bin/sid"
command_args="--theme vt100 --boot"
command_background=false
pidfile="/run/sid.pid"

depend() {
    need net localmount
    after bootmisc
}
SIDSVC
chmod +x "$ROOTFS_DIR/etc/init.d/sid"

# Set up login profile to auto-launch SID on tty1
cat > "$ROOTFS_DIR/etc/profile.d/sid.sh" << 'SIDPROFILE'
# Auto-start SID on tty1 (physical console)
if [ "$(tty)" = "/dev/tty1" ]; then
    clear
    echo "====================================="
    echo "  SID OS v0.5.0 - Super Intelligent Distro"
    echo "  Starting AI interface..."
    echo "====================================="
    sleep 1
    sid
fi
SIDPROFILE
chmod +x "$ROOTFS_DIR/etc/profile.d/sid.sh"

# Enable services
ln -sf /etc/init.d/sid "$ROOTFS_DIR/etc/runlevels/default/" 2>/dev/null || true
ln -sf /etc/init.d/dhcpcd "$ROOTFS_DIR/etc/runlevels/default/" 2>/dev/null || true
ln -sf /etc/init.d/localmount "$ROOTFS_DIR/etc/runlevels/default/" 2>/dev/null || true

# Create /etc/inittab with auto-login on tty1
cat > "$ROOTFS_DIR/etc/inittab" << 'INITTAB'
# SID OS /etc/inittab
::sysinit:/sbin/openrc sysinit
::sysinit:/sbin/openrc boot
::wait:/sbin/openrc default

# Auto-login on tty1 -> auto-starts SID via profile
tty1::respawn:/sbin/getty -L 0 tty1 0 vt100
tty2::respawn:/sbin/getty -L 38400 tty2 vt100
tty3::respawn:/sbin/getty -L 38400 tty3 vt100

# Restart on shutdown
::ctrlaltdel:/sbin/reboot
::shutdown:/sbin/openrc shutdown
INITTAB

# Step 6: Build the bootable ISO
echo "[6/6] Building bootable ISO..."
echo "STEP_MARKER: 6/6 Build ISO"

# Create squashfs of rootfs
SQUASHFS="$BUILD_DIR/sid.squashfs"
mksquashfs "$ROOTFS_DIR" "$SQUASHFS" -comp xz -b 256K -no-progress -noappend
echo "  Squashfs: $(du -sh "$SQUASHFS" | cut -f1)"

# Copy kernel from Alpine
KERNEL="$ROOTFS_DIR/boot/vmlinuz-lts"
INITRAMFS="$BUILD_DIR/initramfs-sid.gz"

# Create minimal initramfs that mounts squashfs and boots
cat > "$INITRAMFS_DIR/init" << 'INIT'
#!/bin/busybox sh

# SID OS Init — boots Alpine + auto-starts SID
/bin/busybox --install -s

# Mount essential filesystems
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts

# Print boot banner
clear
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║    SID OS v0.5.0 - Super Intelligent ║"
echo "  ║    Distro                            ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# Find and mount the root filesystem
# Try various block devices
    # Find root filesystem - scan more devices
    ROOT_DEV=""
    for dev in /dev/sd* /dev/nvme* /dev/mmcblk* /dev/vd* /dev/hd*; do
        if [ -b "$dev" ] && [ "${dev%%[0-9]*}" != "${dev}" ]; then
            ROOT_DEV="$dev"
            break
        fi
    done

if [ -n "$ROOT_DEV" ]; then
    mount "$ROOT_DEV" /mnt 2>/dev/null || mount -t tmpfs tmpfs /mnt
else
    mount -t tmpfs tmpfs /mnt
fi

# Mount the squashfs
if [ -f "/mnt/sid.squashfs" ]; then
    mkdir -p /mnt/root
    mount -o loop /mnt/sid.squashfs /mnt/root
    ROOTFS="/mnt/root"
elif [ -f "/sid.squashfs" ]; then
    mkdir -p /mnt/root
    mount -o loop /sid.squashfs /mnt/root
    ROOTFS="/mnt/root"
else
    # Fallback: use tmpfs
    mkdir -p /mnt/root
    mount -t tmpfs tmpfs /mnt/root
    ROOTFS="/mnt/root"
fi

# Clean up /mnt before switch_root
umount /mnt 2>/dev/null || true

# Switch to the real root and run OpenRC
exec switch_root "$ROOTFS" /sbin/init
INIT
chmod +x "$INITRAMFS_DIR/init"

# Build initramfs
cd "$INITRAMFS_DIR"
find . | cpio -H newc -o | gzip -9 > "$INITRAMFS"
echo "  Initramfs: $(du -sh "$INITRAMFS" | cut -f1)"

# Copy kernel
cp "$KERNEL" "$ISO_DIR/boot/vmlinuz-sid" 2>/dev/null || {
    echo "  WARNING: No kernel found at $KERNEL"
    echo "  The ISO will need a kernel to be bootable."
}

# Copy squashfs
cp "$SQUASHFS" "$ISO_DIR/boot/sid.squashfs"

# Create GRUB config
cat > "$ISO_DIR/boot/grub/grub.cfg" << 'GRUB'
set timeout=3
set default=0

menuentry "SID OS v0.5.0 - Super Intelligent Distro" {
    linux /boot/vmlinuz-sid console=tty0 quiet loglevel=3
    initrd /boot/initramfs-sid.gz
}

menuentry "SID OS - Safe Mode (no AI)" {
    linux /boot/vmlinuz-sid console=tty0 loglevel=3 noai
    initrd /boot/initramfs-sid.gz
}

menuentry "SID OS - Hardware Test" {
    linux /boot/vmlinuz-sid console=tty0 loglevel=3 test
    initrd /boot/initramfs-sid.gz
}
GRUB

# Create ISO
ISO_NAME="sid-$VERSION-live-$ARCH.iso"
cd "$ISO_DIR"

# Find the ISOLINUX MBR file
ISOHYBRID_MBR=""
for mbr in /usr/lib/ISOLINUX/isohdpfx.bin /usr/share/syslinux/isohdpfx.bin; do
    if [ -f "$mbr" ]; then
        ISOHYBRID_MBR="$mbr"
        break
    fi
done

# Create the bootable ISO
if command -v grub-mkrescue &>/dev/null; then
    echo "  Using grub-mkrescue for UEFI+BIOS bootable ISO..."
    grub-mkrescue -o "$OUTPUT_DIR/$ISO_NAME" "$ISO_DIR" 2>/dev/null || \
    xorriso -as mkisofs \
        -V "SID-OS-$VERSION" \
        ${ISOHYBRID_MBR:+-isohybrid-mbr "$ISOHYBRID_MBR"} \
        -b isolinux/isolinux.bin -c isolinux/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot \
        -o "$OUTPUT_DIR/$ISO_NAME" \
        "$ISO_DIR" 2>&1
else
    xorriso -as mkisofs \
        -V "SID-OS-$VERSION" \
        ${ISOHYBRID_MBR:+-isohybrid-mbr "$ISOHYBRID_MBR"} \
        -b isolinux/isolinux.bin -c isolinux/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot \
        -o "$OUTPUT_DIR/$ISO_NAME" \
        "$ISO_DIR" 2>&1
fi
    . 2>&1

echo ""
echo "========================================"
echo "  ✅ SID OS Live ISO built!"
echo "  📁 $OUTPUT_DIR/$ISO_NAME"
echo "  Size: $(du -sh "$OUTPUT_DIR/$ISO_NAME" | cut -f1)"
echo "========================================"
echo ""
echo "  To write to USB (Linux):"
echo "    sudo dd if=$OUTPUT_DIR/$ISO_NAME of=/dev/sdX bs=4M status=progress"
echo ""
echo "  To write to USB (Windows):"
echo "    Use Rufus (rufus.ie) - select ISO, write in DD mode"
echo ""
echo "  Min requirements: 2GB RAM, x86_64 CPU, 4GB USB drive"

# Cleanup
rm -rf "$BUILD_DIR"
