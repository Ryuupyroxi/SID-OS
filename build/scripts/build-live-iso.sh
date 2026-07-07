#!/bin/bash
# SID OS Live ISO Builder - Builds a complete bootable Alpine + SID OS image
# Usage: ./build/scripts/build-live-iso.sh [output_dir]
# Requires: xorriso, squashfs-tools, cpio, gzip, wget
set -eo pipefail

VERSION="${VERSION:-0.5.2}"
ALPINE_VERSION="3.24.1"
ARCH="x86_64"
ALPINE_MIRROR="https://dl-cdn.alpinelinux.org/alpine/v3.24"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$(realpath "${1:-$PROJECT_DIR/build/output}")"
BUILD_DIR="/tmp/sid-live-build-$$"
ROOTFS_DIR="$BUILD_DIR/rootfs"
ISO_DIR="$BUILD_DIR/iso"
PKG_CACHE="$BUILD_DIR/packages"

mkdir -p "$ROOTFS_DIR" "$ISO_DIR/boot/grub" "$PKG_CACHE" "$OUTPUT_DIR"

echo "╔══════════════════════════════════════════╗"
echo "║  SID OS v$VERSION - Live ISO Builder     "
echo "║  Alpine $ALPINE_VERSION $ARCH base"
echo "╚══════════════════════════════════════════╝"

# ---- Step 1: Get Alpine base ----
echo "[1/6] Alpine minirootfs..."
ALPINE_TAR="alpine-minirootfs-${ALPINE_VERSION}-${ARCH}.tar.gz"
wget -q -O "$PKG_CACHE/$ALPINE_TAR" "$ALPINE_MIRROR/releases/$ARCH/$ALPINE_TAR"
tar xzf "$PKG_CACHE/$ALPINE_TAR" -C "$ROOTFS_DIR"
echo "  Base: $(du -sh "$ROOTFS_DIR" | cut -f1)"

# ---- Step 2: Download APKINDEX ----
echo "[2/6] Package indexes..."
for repo in main community; do
    wget -q -O "$PKG_CACHE/APKINDEX-${repo}.tar.gz" "$ALPINE_MIRROR/$repo/$ARCH/APKINDEX.tar.gz"
    tar xzf "$PKG_CACHE/APKINDEX-${repo}.tar.gz" -C "$PKG_CACHE/" 2>/dev/null || true
    [ -f "$PKG_CACHE/APKINDEX" ] && mv "$PKG_CACHE/APKINDEX" "$PKG_CACHE/APKINDEX-$repo" 2>/dev/null || true
done

# ---- Step 3: Download and install packages ----
echo "[3/6] Installing packages..."
install_pkg() {
    local name="$1" ver=""
    for repo in main community; do
        ver=$(grep -A20 "^P:$name$" "$PKG_CACHE/APKINDEX-$repo" 2>/dev/null | grep "^V:" | head -1 | cut -d: -f2-)
        [ -n "$ver" ] && break
    done
    [ -z "$ver" ] && echo "  ? $name (not found)" && return 1
    local file="${name}-${ver}.apk"
    if [ ! -f "$PKG_CACHE/$file" ]; then
        echo "  ↓ $name ($ver)"
        for repo in main community; do
            wget -q -O "$PKG_CACHE/$file" "$ALPINE_MIRROR/$repo/$ARCH/$file" 2>/dev/null && break
        done
    fi
    if [ -f "$PKG_CACHE/$file" ] && [ -s "$PKG_CACHE/$file" ]; then
        tar xzf "$PKG_CACHE/$file" -C "$ROOTFS_DIR" 2>/dev/null
        rm -f "$ROOTFS_DIR/.PKGINFO" "$ROOTFS_DIR/.SIGN.RSA."* 2>/dev/null || true
        echo "  + $name"
    else
        echo "  ✗ $name (download failed)"
        return 1
    fi
}

for pkg in linux-lts python3 py3-pip ncurses-libs ncurses-terminfo readline sqlite-libs openssl ca-certificates eudev-libs dhcpcd tzdata htop doas syslinux; do
    install_pkg "$pkg" || true
done

# Verify kernel
if [ ! -f "$ROOTFS_DIR/boot/vmlinuz-lts" ]; then
    echo "FATAL: Kernel not installed. Check network connectivity."
    exit 1
fi
echo "  Kernel: $(ls -lh "$ROOTFS_DIR/boot/vmlinuz-lts" | awk '{print $5}')"

# Python pip packages (installed on first boot by SID)
echo "  Python deps: auto-install on first boot"

# ---- Step 4: Install SID OS ----
echo "[4/6] Installing SID OS..."
bash "$PROJECT_DIR/build/scripts/make-portable.sh" "$BUILD_DIR/portable" >/dev/null 2>&1
SID_TAR=$(ls "$BUILD_DIR/portable"/sid-*.tar.gz | head -1)
tar xzf "$SID_TAR" -C "$ROOTFS_DIR/opt/"
if [ -d "$ROOTFS_DIR/opt/opt/sid" ]; then
    mv "$ROOTFS_DIR/opt/opt/sid"/* "$ROOTFS_DIR/opt/" 2>/dev/null || true
    rm -rf "$ROOTFS_DIR/opt/opt"
fi
if [ ! -f "$ROOTFS_DIR/opt/sid/src/main.py" ]; then
    mkdir -p "$ROOTFS_DIR/opt/sid"
    find "$ROOTFS_DIR/opt/" -maxdepth 1 -not -name opt -not -name sid -not -name '.' -exec mv {} "$ROOTFS_DIR/opt/sid/" \; 2>/dev/null || true
fi

cat > "$ROOTFS_DIR/usr/local/bin/sid" << 'EOF'
#!/bin/sh
cd /opt/sid
exec /usr/bin/python3 src/main.py "$@"
EOF
chmod +x "$ROOTFS_DIR/usr/local/bin/sid"
mkdir -p "$ROOTFS_DIR/sid/models" "$ROOTFS_DIR/sid/memory" "$ROOTFS_DIR/sid/logs" "$ROOTFS_DIR/etc/sid"

# ---- Step 5: Configure system ----
echo "[5/6] Configuring boot..."
echo "nameserver 1.1.1.1" > "$ROOTFS_DIR/etc/resolv.conf"
echo "127.0.0.1 localhost sid" > "$ROOTFS_DIR/etc/hosts"
echo "sid" > "$ROOTFS_DIR/etc/hostname"
cat > "$ROOTFS_DIR/etc/apk/repositories" << REPOS
$ALPINE_MIRROR/main
$ALPINE_MIRROR/community
REPOS

cat > "$ROOTFS_DIR/etc/inittab" << 'INIT'
::sysinit:/sbin/openrc sysinit
::sysinit:/sbin/openrc boot
::wait:/sbin/openrc default
tty1::respawn:/sbin/getty -L 0 tty1 0 vt100
tty2::respawn:/sbin/getty -L 38400 tty2 vt100
tty3::respawn:/sbin/getty -L 38400 tty3 vt100
::ctrlaltdel:/sbin/reboot
::shutdown:/sbin/openrc shutdown
INIT

cat > "$ROOTFS_DIR/etc/profile.d/sid.sh" << 'PROFILE'
if [ "$(tty)" = "/dev/tty1" ]; then
    clear; echo "SID OS v0.5.2 - Super Intelligent Distro"; sleep 1; sid
fi
PROFILE
chmod +x "$ROOTFS_DIR/etc/profile.d/sid.sh"

mkdir -p "$ROOTFS_DIR/etc/runlevels/default"
ln -sf /etc/init.d/dhcpcd "$ROOTFS_DIR/etc/runlevels/default/" 2>/dev/null || true
ln -sf /etc/init.d/localmount "$ROOTFS_DIR/etc/runlevels/default/" 2>/dev/null || true

# ---- Step 6: Build bootable ISO ----
echo "[6/6] Building bootable ISO..."

# Squashfs
SQUASHFS="$BUILD_DIR/sid.squashfs"
mksquashfs "$ROOTFS_DIR" "$SQUASHFS" -comp xz -b 256K -no-progress -noappend
echo "  Squashfs: $(du -sh "$SQUASHFS" | cut -f1)"

cp "$ROOTFS_DIR/boot/vmlinuz-lts" "$ISO_DIR/boot/vmlinuz-sid"
cp "$SQUASHFS" "$ISO_DIR/boot/sid.squashfs"

# Initramfs
INIT_DIR="$BUILD_DIR/initramfs"
mkdir -p "$INIT_DIR"
cat > "$INIT_DIR/init" << 'INIT'
#!/bin/busybox sh
/bin/busybox --install -s
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
clear
echo "  SID OS v0.5.2 - booting..."
for d in /dev/sr*; do [ -b "$d" ] && mount "$d" /mnt 2>/dev/null && [ -f /mnt/boot/sid.squashfs ] && break; done
[ -f /mnt/boot/sid.squashfs ] || for d in /dev/sd*; do
    [ -b "$d" ] || continue
    mount "$d" /mnt 2>/dev/null || continue
    [ -f /mnt/boot/sid.squashfs ] && break
    umount /mnt 2>/dev/null
done
if [ -f /mnt/boot/sid.squashfs ]; then
    mkdir -p /rootfs
    mount -o loop /mnt/boot/sid.squashfs /rootfs
    umount /mnt 2>/dev/null
else
    mount -t tmpfs tmpfs /rootfs
fi
exec switch_root /rootfs /sbin/init
INIT
chmod +x "$INIT_DIR/init"
cd "$INIT_DIR"
find . | cpio -H newc -o | gzip -9 > "$ISO_DIR/boot/initramfs-sid.gz"
echo "  Initramfs: $(du -sh "$ISO_DIR/boot/initramfs-sid.gz" | cut -f1)"

# GRUB config
cat > "$ISO_DIR/boot/grub/grub.cfg" << 'GRUB'
set timeout=3
set default=0
menuentry "SID OS v0.5.2" {
    linux /boot/vmlinuz-sid console=tty0 quiet loglevel=3
    initrd /boot/initramfs-sid.gz
}
menuentry "SID OS (Safe Mode)" {
    linux /boot/vmlinuz-sid console=tty0 nomodeset loglevel=3
    initrd /boot/initramfs-sid.gz
}
GRUB

# Get isolinux for BIOS boot
if [ -f "$PKG_CACHE/syslinux-"*.apk ]; then
    mkdir -p "$ISO_DIR/isolinux" "$BUILD_DIR/syslinux"
    tar xzf "$PKG_CACHE"/syslinux-*.apk -C "$BUILD_DIR/syslinux" 2>/dev/null || true
    cp "$BUILD_DIR/syslinux"/usr/share/syslinux/isolinux.bin "$ISO_DIR/isolinux/" 2>/dev/null || true
    cp "$BUILD_DIR/syslinux"/usr/share/syslinux/isohdpfx.bin "$ISO_DIR/isolinux/" 2>/dev/null || true
fi

# Create ISO
ISO_NAME="sid-${VERSION}-live-${ARCH}.iso"
if [ -f "$ISO_DIR/isolinux/isolinux.bin" ]; then
    MBR="$ISO_DIR/isolinux/isohdpfx.bin"
    [ -f "$MBR" ] && MBR_ARG="-isohybrid-mbr $MBR" || MBR_ARG=""
    xorriso -as mkisofs -V "SID-OS-$VERSION" $MBR_ARG \
        -b isolinux/isolinux.bin -c isolinux/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -isohybrid-gpt-basdat \
        -o "$OUTPUT_DIR/$ISO_NAME" "$ISO_DIR" 2>&1
else
    xorriso -as mkisofs -V "SID-OS-$VERSION" -o "$OUTPUT_DIR/$ISO_NAME" "$ISO_DIR" 2>&1
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ SID OS Live ISO built!               ║"
echo "║  $OUTPUT_DIR/$ISO_NAME"
echo "║  $(du -h "$OUTPUT_DIR/$ISO_NAME" | cut -f1)"
echo "╚══════════════════════════════════════════╝"

# Cleanup
rm -rf "$BUILD_DIR"
