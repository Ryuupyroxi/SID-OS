# SID OS Live ISO Builder - Builds a complete bootable Alpine + SID OS image
set -eo pipefail

# Auto-detect version from env, git tag, or fallback
[ -z "${VERSION}" ] && [ -n "${GITHUB_REF_NAME}" ] && VERSION="${GITHUB_REF_NAME#v}"
VERSION="${VERSION:-1.6.2}"
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
echo "=========================================="
echo "  SID OS v$VERSION - Live ISO Builder"
echo "=========================================="

# Step 1: Alpine base
echo "[1/6] Alpine minirootfs..."
ALPINE_TAR="alpine-minirootfs-${ALPINE_VERSION}-${ARCH}.tar.gz"
wget -q -O "$PKG_CACHE/$ALPINE_TAR" "$ALPINE_MIRROR/releases/$ARCH/$ALPINE_TAR"
tar xzf "$PKG_CACHE/$ALPINE_TAR" -C "$ROOTFS_DIR"
echo "  Base: $(du -sh "$ROOTFS_DIR" | cut -f1)"

# Step 2: Package indexes
echo "[2/6] Package indexes..."
for repo in main community; do
    wget -q -O "$PKG_CACHE/APKINDEX-${repo}.tar.gz" "$ALPINE_MIRROR/$repo/$ARCH/APKINDEX.tar.gz"
    tar xzf "$PKG_CACHE/APKINDEX-${repo}.tar.gz" -C "$PKG_CACHE/" 2>/dev/null || true
    [ -f "$PKG_CACHE/APKINDEX" ] && mv "$PKG_CACHE/APKINDEX" "$PKG_CACHE/APKINDEX-$repo" 2>/dev/null || true
done

# Step 3: Install packages
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
        echo "  Downloading $name ($ver)..."
        for repo in main community; do
            wget -q -O "$PKG_CACHE/$file" "$ALPINE_MIRROR/$repo/$ARCH/$file" 2>/dev/null && break
        done
    fi
    if [ -f "$PKG_CACHE/$file" ] && [ -s "$PKG_CACHE/$file" ]; then
        tar xzf "$PKG_CACHE/$file" -C "$ROOTFS_DIR" 2>/dev/null
        rm -f "$ROOTFS_DIR/.PKGINFO" "$ROOTFS_DIR/.SIGN.RSA."* 2>/dev/null || true
        echo "  + $name"
    else
        echo "  FAILED: $name"
    fi
}

for pkg in linux-lts linux-firmware python3 py3-pip py3-pillow ncurses-libs ncurses-terminfo readline bash sqlite-libs openssl ca-certificates eudev-libs dhcpcd tzdata doas sudo syslinux openrc alpine-conf e2fsprogs grub-efi dosfstools ntfs-3g fuse3 exfatprogs wpa_supplicant iw wireless-tools htop lm-sensors; do
    install_pkg "$pkg" || true
done

if [ ! -f "$ROOTFS_DIR/boot/vmlinuz-lts" ]; then
    echo "FATAL: Kernel not installed!"
    exit 1
fi
echo "  Kernel: $(ls -lh "$ROOTFS_DIR/boot/vmlinuz-lts" | awk '{print $5}')"

# Step 4: Install SID OS
echo "[4/6] Installing SID OS..."
bash "$PROJECT_DIR/build/scripts/make-portable.sh" "$BUILD_DIR/portable" >/dev/null 2>&1 || echo "  Warning: make-portable.sh had issues"

SID_TAR=$(ls "$BUILD_DIR/portable"/sid-*.tar.gz 2>/dev/null | head -1)
if [ -z "$SID_TAR" ]; then echo "FATAL: no SID tarball produced"; exit 1; fi

# Always extract into opt/sid/ directly
mkdir -p "$ROOTFS_DIR/opt/sid"
tar xzf "$SID_TAR" -C "$ROOTFS_DIR/opt/sid/" 2>/dev/null || true
echo "  SID extracted"

# If tar had sid/ prefix internally, files are at opt/sid/sid/ - fix that
if [ -d "$ROOTFS_DIR/opt/sid/sid" ]; then
    cp -r "$ROOTFS_DIR/opt/sid/sid/"* "$ROOTFS_DIR/opt/sid/" 2>/dev/null || true
    rm -rf "$ROOTFS_DIR/opt/sid/sid"
fi

# If tar extracted flat (src/ at root of tar), src is at opt/sid/src/ - good already
# Check for main.py
if [ ! -f "$ROOTFS_DIR/opt/sid/src/main.py" ]; then
    echo "  SID extraction flat, re-organizing..."
    for item in "$ROOTFS_DIR/opt/sid/"*; do
        name=$(basename "$item")
        [ "$name" = "src" ] && continue
        [ "$name" = "config" ] && continue
        [ "$name" = "AGENTS.md" ] || [ "$name" = "README.md" ] || [ "$name" = "test_sid.py" ] || [ "$name" = "get-sid.py" ] || [ -f "$item" ] && rm -f "$item" 2>/dev/null || true
    done
fi

cat > "$ROOTFS_DIR/usr/local/bin/sid" << 'EOF'
#!/bin/sh
cd /opt/sid
exec /usr/bin/python3 src/main.py "$@"
EOF
chmod +x "$ROOTFS_DIR/usr/local/bin/sid"
mkdir -p "$ROOTFS_DIR/sid/models" "$ROOTFS_DIR/sid/memory" "$ROOTFS_DIR/sid/logs" "$ROOTFS_DIR/etc/sid"

# Step 5: Configure boot
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

# Create easter egg: devmode — a techy hidden utility
cat > "$ROOTFS_DIR/usr/local/bin/devmode" << 'DEVMODE'
#!/bin/sh
# SID OS DevMode — hidden technical easter egg
#           _.-.
#       .,'/  // 
#  ,..-'  /  /_    
#  \       /  /    
#   \_   _/  /___  
#     `--`--'||| `.
#   S.I.D.   |||   
#             |||

echo ""
echo "  ╔═══════════════════════════════════╗"
echo "  ║     SID OS v${VERSION} DEVMODE     ║"
echo "  ║     "The eyes of the world are    ║"
echo "  ║      upon you, and the hopes      ║"
echo "  ║      and the prayers of           ║"
echo "  ║      liberty-loving people        ║"
echo "  ║      everywhere march with you."  ║"
echo "  ╚═══════════════════════════════════╝"
echo ""
echo "  [SYSTEM] Kernel: $(uname -r 2>/dev/null || echo '?')"
echo "  [SYSTEM] Uptime: $(uptime 2>/dev/null | sed 's/.*up //' | sed 's/,.*//' || echo '?')"
echo "  [SYSTEM] Memory: $(free -m 2>/dev/null | grep Mem | awk '{print $3"/"$2" MB"}' || echo '?')"
echo "  [SYSTEM] CPU: $(grep 'model name' /proc/cpuinfo 2>/dev/null | head -1 | sed 's/.*: //' || echo '?')"
echo "  [SYSTEM] Load: $(cat /proc/loadavg 2>/dev/null || echo '?')"
echo "  [FILESYSTEM] Host partitions:"
ls -1 /mnt/host/ 2>/dev/null | while read d; do
    size=$(df -h /mnt/host/$d 2>/dev/null | tail -1 | awk '{print $2}')
    fs=$(blkid -s TYPE -o value /dev/$(echo $d | sed 's/[0-9]*$//') 2>/dev/null | head -1 || echo '?')
    echo "    /mnt/host/$d  ($fs, $size)"
done 2>/dev/null
echo ""
echo "  Type 'deploy' to initiate self-test sequence."
read -r input
if [ "$input" = "deploy" ]; then
    echo ""
    echo "  ╔═══════════════════════════════════════════╗"
    echo "  ║  SID OS v${VERSION} — SELF-TEST SEQUENCE   ║"
    echo "  ║  All systems nominal. Memory integrity: OK ║"
    echo "  ║  AI core: STANDBY. Userspace: READY.      ║"
    echo "  ║  "Failure is not an option."              ║"
    echo "  ╚═══════════════════════════════════════════╝"
    echo ""
else
    echo "  Sequence aborted. Returning to SID shell."
fi
DEVMODE
chmod +x "$ROOTFS_DIR/usr/local/bin/devmode"

cat > "$ROOTFS_DIR/etc/profile.d/sid.sh" << 'PROFILE'
if [ "$(tty)" = "/dev/tty1" ]; then
    clear
    echo "SID OS v${VERSION} - Super Intelligent Distro"
    echo "  Type 'devmode' for system diagnostics"
    sleep 1
    sid
fi
PROFILE
chmod +x "$ROOTFS_DIR/etc/profile.d/sid.sh"

# Create auto-mount service for host filesystem access
cat > "$ROOTFS_DIR/etc/init.d/automount" << 'AUTOMOUNT'
#!/sbin/openrc-run
description="Auto-mount all host filesystems for live access"

depend() {
    need localmount
    after localmount
}

start() {
    ebegin "Mounting host filesystems"
    mkdir -p /mnt/host
    # Scan all block devices and mount them
    for dev in /dev/sd*[0-9] /dev/nvme*[0-9] /dev/mmcblk*p* /dev/vd*[0-9] /dev/hd*[0-9]; do
        [ -b "$dev" ] || continue
        # Get label or use device name
        label=$(blkid -s LABEL -o value "$dev" 2>/dev/null | head -1)
        [ -z "$label" ] && label=$(basename "$dev")
        target="/mnt/host/${label}"
        mkdir -p "$target"
        fstype=$(blkid -s TYPE -o value "$dev" 2>/dev/null | head -1)
        case "$fstype" in
            ntfs)     mount -t ntfs-3g "$dev" "$target" 2>/dev/null || rmdir "$target" 2>/dev/null ;;
            ext4|ext3|ext2|xfs|btrfs)
                      mount "$dev" "$target" 2>/dev/null || rmdir "$target" 2>/dev/null ;;
            vfat|exfat)
                      mount "$dev" "$target" 2>/dev/null || rmdir "$target" 2>/dev/null ;;
            hfsplus)  mount -t hfsplus "$dev" "$target" 2>/dev/null || rmdir "$target" 2>/dev/null ;;
            *)        mount "$dev" "$target" 2>/dev/null || rmdir "$target" 2>/dev/null ;;
        esac
    done
    eend $?
}

stop() {
    ebegin "Unmounting host filesystems"
    for mnt in /mnt/host/*/; do
        [ -d "$mnt" ] && umount "$mnt" 2>/dev/null
    done
    eend $?
}
AUTOMOUNT
chmod +x "$ROOTFS_DIR/etc/init.d/automount"

# Add automount to startup script (runs after boot)
cat > "$ROOTFS_DIR/etc/local.d/automount.start" << 'LOCAL'
#!/bin/sh
/etc/init.d/automount start
LOCAL
chmod +x "$ROOTFS_DIR/etc/local.d/automount.start"

mkdir -p "$ROOTFS_DIR/etc/runlevels/default"
ln -sf /etc/init.d/dhcpcd "$ROOTFS_DIR/etc/runlevels/default/" 2>/dev/null || true
ln -sf /etc/init.d/localmount "$ROOTFS_DIR/etc/runlevels/default/" 2>/dev/null || true
ln -sf /etc/init.d/local "$ROOTFS_DIR/etc/runlevels/default/" 2>/dev/null || true

# Step 6: Build ISO
echo "[6/6] Building bootable ISO..."

SQUASHFS="$BUILD_DIR/sid.squashfs"
mksquashfs "$ROOTFS_DIR" "$SQUASHFS" -comp xz -b 256K -no-progress -noappend
echo "  Squashfs: $(du -sh "$SQUASHFS" | cut -f1)"

cp "$ROOTFS_DIR/boot/vmlinuz-lts" "$ISO_DIR/boot/vmlinuz-sid"
cp "$SQUASHFS" "$ISO_DIR/boot/sid.squashfs"

INIT_DIR="$BUILD_DIR/initramfs"
rm -rf "$INIT_DIR" && mkdir -p "$INIT_DIR/bin" "$INIT_DIR/dev" "$INIT_DIR/proc" "$INIT_DIR/sys" "$INIT_DIR/mnt" "$INIT_DIR/rootfs"
cp "$ROOTFS_DIR/bin/busybox" "$INIT_DIR/bin/"
ln -s busybox "$INIT_DIR/bin/sh"
cat > "$INIT_DIR/init" << 'INIT2'
#!/bin/busybox sh
# SID OS Initramfs — finds squashfs, mounts rootfs, switches
/bin/busybox --install -s

# Mount essentials
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mknod /dev/console c 5 1 2>/dev/null

# Boot splash
clear
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║     SID OS v${VERSION} - Booting...     ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# Rootdelay: wait for slow USB devices (old BIOS needs this)
if grep -q "rootdelay=" /proc/cmdline 2>/dev/null; then
    delay=$(cat /proc/cmdline | tr ' ' '\n' | grep rootdelay= | cut -d= -f2)
    delay=${delay:-5}
elif grep -q "rootwait" /proc/cmdline 2>/dev/null; then
    delay=10
else
    delay=0
fi
if [ "$delay" -gt 0 ] 2>/dev/null; then
    echo "  Waiting ${delay}s for USB devices..."
    sleep "$delay"
fi

# Show detected block devices for debugging
echo "  Scanning for boot devices:"
ls /dev/sd* /dev/sr* /dev/nvme* /dev/mmcblk* /dev/vd* 2>/dev/null | tr '\n' ' ' && echo ""

# Try to find and mount sid.squashfs
FOUND=0
for d in /dev/sr*; do
    [ -b "$d" ] || continue
    mount -t iso9660 -o ro "$d" /mnt 2>/dev/null || mount "$d" /mnt 2>/dev/null || continue
    if [ -f /mnt/boot/sid.squashfs ]; then FOUND=1; break; fi
    umount /mnt 2>/dev/null
done

# Try partitions on all block devices (slowest first = USB)
if [ "$FOUND" -eq 0 ]; then
    for d in /dev/sd* /dev/nvme* /dev/mmcblk* /dev/vd*; do
        [ -b "$d" ] || continue
        # Skip whole devices, only try partitions
        case "$d" in
            *[0-9]) ;;     # has digit = partition
            /dev/nvme*) 
                case "$d" in
                    *p[0-9]*) ;;  # nvme0n1p1 = partition
                    *) continue;;
                esac;;
            /dev/mmcblk*)
                case "$d" in
                    *p[0-9]*) ;;  # mmcblk0p1 = partition
                    *) continue;;
                esac;;
            *) continue;;  # skip whole disk devices like /dev/sda
        esac
        mount "$d" /mnt 2>/dev/null || continue
        if [ -f /mnt/boot/sid.squashfs ]; then FOUND=2; break; fi
        umount /mnt 2>/dev/null
    done
fi

# Also try whole devices (for dd-written ISOs without partition table)
if [ "$FOUND" -eq 0 ]; then
    for d in /dev/sd*; do
        [ -b "$d" ] || continue
        case "$d" in
            *[0-9]) continue;;  # skip partitions, already tried
        esac
        mount "$d" /mnt 2>/dev/null || continue
        if [ -f /mnt/boot/sid.squashfs ]; then FOUND=3; break; fi
        umount /mnt 2>/dev/null
    done
fi

if [ "$FOUND" -gt 0 ]; then
    echo "  Found boot device (method $FOUND)"
    mkdir -p /rootfs
    mount -o loop /mnt/boot/sid.squashfs /rootfs
    umount /mnt 2>/dev/null
    echo "  Root filesystem mounted, switching..."
else
    echo ""
    echo "  ⚠ ERROR: Could not find SID OS boot device!"
    echo "  Expected: /boot/sid.squashfs on USB or CDROM"
    echo "  Devices found:"
    ls -la /dev/sd* /dev/sr* /dev/nvme* /dev/mmcblk* /dev/vd* 2>/dev/null || echo "    (none)"
    echo ""
    echo "  Booting to emergency shell..."
    mount -t tmpfs tmpfs /rootfs
    mkdir -p /rootfs/dev /rootfs/proc /rootfs/sys /rootfs/bin
    cp /bin/busybox /rootfs/bin/
    echo '#!/bin/sh' > /rootfs/init
    echo 'exec /bin/sh' >> /rootfs/init
    chmod +x /rootfs/init
fi

exec switch_root /rootfs /init
INIT2
chmod +x "$INIT_DIR/init"
cd "$INIT_DIR"
find . | cpio -H newc -o | gzip -9 > "$ISO_DIR/boot/initramfs-sid.gz"
echo "  Initramfs: $(du -sh "$ISO_DIR/boot/initramfs-sid.gz" | cut -f1)"

cat > "$ISO_DIR/boot/grub/grub.cfg" << 'GRUB'
set timeout=3
set default=0
menuentry "SID OS v${VERSION}" {
    linux /boot/vmlinuz-sid console=tty0 rootdelay=10 quiet loglevel=3
    initrd /boot/initramfs-sid.gz
}
menuentry "SID OS v${VERSION} (ATI-safe nomodeset)" {
    linux /boot/vmlinuz-sid console=tty0 rootdelay=10 nomodeset radeon.modeset=0 quiet loglevel=3
    initrd /boot/initramfs-sid.gz
}
menuentry "SID OS v${VERSION} (Verbose)" {
    linux /boot/vmlinuz-sid console=tty0 rootdelay=15 loglevel=7
    initrd /boot/initramfs-sid.gz
}
menuentry "SID OS v${VERSION} (Safe Mode)" {
    linux /boot/vmlinuz-sid console=tty0 rootdelay=10 nomodeset acpi=off loglevel=3
    initrd /boot/initramfs-sid.gz
}

GRUB

if ls "$PKG_CACHE"/syslinux-*.apk 1>/dev/null 2>&1; then
    mkdir -p "$ISO_DIR/isolinux" "$BUILD_DIR/syslinux"
    tar xzf "$PKG_CACHE"/syslinux-*.apk -C "$BUILD_DIR/syslinux" 2>/dev/null || true
    # Copy all ISOLINUX modules needed for boot
    SYSLINUX_DIR="$BUILD_DIR/syslinux/usr/share/syslinux"
    for mod in isolinux.bin ldlinux.c32 libutil.c32 libcom32.c32 isohdpfx.bin; do
        cp "$SYSLINUX_DIR/$mod" "$ISO_DIR/isolinux/" 2>/dev/null || echo "  Warning: $mod not found in syslinux package"
    done
    # Create boot message
    cat > "$ISO_DIR/isolinux/boot.msg" << BOOTMSG
╔══════════════════════════════════════╗
║        SID OS v${VERSION}               ║
║  Super Intelligent Distro (Alpine)   ║
╚══════════════════════════════════════╝

Boot options:
  sid           - Normal boot (default, 10s USB delay)
  sid-nomodeset - ATI/nVidia safe mode (no KMS)
  sid-verbose   - Verbose boot (debug)
  sid-safe      - Safe mode (ACPI off, no KMS)

Press TAB to edit, ENTER to boot.
BOOTMSG
    cat > "$ISO_DIR/isolinux/isolinux.cfg" << ISOCFG
DEFAULT sid
TIMEOUT 100
PROMPT 1
DISPLAY boot.msg

LABEL sid
    LINUX /boot/vmlinuz-sid
    INITRD /boot/initramfs-sid.gz
    APPEND console=tty0 rootdelay=10 quiet loglevel=3
LABEL sid-nomodeset
    LINUX /boot/vmlinuz-sid
    INITRD /boot/initramfs-sid.gz
    APPEND console=tty0 rootdelay=10 nomodeset radeon.modeset=0 quiet loglevel=3
LABEL sid-verbose
    LINUX /boot/vmlinuz-sid
    INITRD /boot/initramfs-sid.gz
    APPEND console=tty0 rootdelay=15 loglevel=7
LABEL sid-safe
    LINUX /boot/vmlinuz-sid
    INITRD /boot/initramfs-sid.gz
    APPEND console=tty0 rootdelay=10 nomodeset acpi=off loglevel=3
ISOCFG
fi

# Create UEFI boot image (EFI System Partition)
if [ -f "$ROOTFS_DIR/usr/lib/grub/x86_64-efi/modinfo.sh" ]; then
    echo "  Creating UEFI boot image..."
    EFI_IMG="$ISO_DIR/boot/grub/efi.img"
    dd if=/dev/zero of="$EFI_IMG" bs=1K count=6144 2>/dev/null
    mkfs.vfat "$EFI_IMG" 2>/dev/null
    EFI_MNT="$BUILD_DIR/efi-mnt"
    mkdir -p "$EFI_MNT"
    mount -o loop "$EFI_IMG" "$EFI_MNT" 2>/dev/null || true
    if mountpoint -q "$EFI_MNT"; then
        mkdir -p "$EFI_MNT/EFI/BOOT"
        # Build GRUB EFI core image with required modules
        grub-mkimage -O x86_64-efi -p /boot/grub -o "$EFI_MNT/EFI/BOOT/BOOTx64.EFI"             ext2 fat part_msdos part_gpt normal configfile linux loopback search             search_fs_uuid echo test reboot halt cat ls video font gfxterm             gfxmenu gfxterm_background all_video 2>/dev/null || echo "  Warning: grub-mkimage failed"
        umount "$EFI_MNT"
        echo "  UEFI: $(du -h "$EFI_IMG" | cut -f1)"
    else
        echo "  Warning: Could not mount EFI image (no loop device)"
    fi
    rmdir "$EFI_MNT" 2>/dev/null || true
else
    echo "  Warning: GRUB EFI modules not found, UEFI boot not available"
fi

ISO_NAME="sid-${VERSION}-live-${ARCH}.iso"
if [ -f "$ISO_DIR/isolinux/isolinux.bin" ]; then
    MBR="$ISO_DIR/isolinux/isohdpfx.bin"
    [ -f "$MBR" ] && MBR_ARG="-isohybrid-mbr $MBR" || MBR_ARG=""
    # Add UEFI boot arguments if EFI image exists
    EFI_ARG=""
    [ -f "$ISO_DIR/boot/grub/efi.img" ] && EFI_ARG="-e boot/grub/efi.img -no-emul-boot"
    xorriso -as mkisofs -V "SID-OS-$VERSION" $MBR_ARG         -b isolinux/isolinux.bin -c isolinux/boot.cat         -no-emul-boot -boot-load-size 4 -boot-info-table         -isohybrid-gpt-basdat $EFI_ARG         -o "$OUTPUT_DIR/$ISO_NAME" "$ISO_DIR" 2>&1
else
    # Fallback: data-only ISO (no bootloader)
    EFI_ARG=""
    [ -f "$ISO_DIR/boot/grub/efi.img" ] && EFI_ARG="-e boot/grub/efi.img -no-emul-boot -isohybrid-gpt-basdat"
    xorriso -as mkisofs -V "SID-OS-$VERSION" $EFI_ARG -o "$OUTPUT_DIR/$ISO_NAME" "$ISO_DIR" 2>&1
fi

echo ""
echo "=========================================="
echo "  SID OS ISO built!"
echo "  $OUTPUT_DIR/$ISO_NAME"
echo "  $(du -h "$OUTPUT_DIR/$ISO_NAME" | cut -f1)"
echo "=========================================="
# Generate checksums
cd "$OUTPUT_DIR"
sha256sum "$ISO_NAME" > "${ISO_NAME}.sha256"
echo "  SHA256: $(cat "${ISO_NAME}.sha256")"
echo ""
rm -rf "$BUILD_DIR"
