#!/bin/bash
# SID OS Build Script
# Builds the complete SID operating system from source

set -e
SID_ROOT="/sid"
BUILD_DIR="/tmp/sid-build"
OUTPUT_DIR="/output"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[BUILD]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
header() { echo -e "\n${BLUE}════════════════════════════════════════${NC}"; echo -e "${BLUE}  $1${NC}"; echo -e "${BLUE}════════════════════════════════════════${NC}"; }

# Configuration
SID_VERSION="1.2.0"
ARCH="${ARCH:-x86_64}"
BASE_IMAGE="${BASE_IMAGE:-alpine:3.24}"
KERNEL_VERSION="${KERNEL_VERSION:-6.6.x}"

check_deps() {
    header "Checking Dependencies"
    local deps="wget curl git build-base linux-headers ncurses-dev python3 py3-pip cmake"
    for dep in $deps; do
        if command -v $dep &>/dev/null; then
            log "  ✓ $dep"
        else
            log "  Installing $dep..."
            apk add --no-cache $dep 2>/dev/null || apt-get install -y $dep 2>/dev/null || true
        fi
    done
}

build_kernel() {
    header "Building Minimal Linux Kernel"
    mkdir -p $BUILD_DIR/kernel
    cd $BUILD_DIR/kernel
    
    if [ ! -f "linux-${KERNEL_VERSION}.tar.xz" ]; then
        log "Downloading kernel..."
        wget -q "https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${KERNEL_VERSION}.tar.xz"
    fi
    
    tar xf "linux-${KERNEL_VERSION}.tar.xz"
    cd "linux-${KERNEL_VERSION}"
    
    # Apply SID kernel config (minimal, old hardware optimized)
    cat > .config << 'KCONFIG'
# SID Minimal Kernel Configuration
CONFIG_64BIT=y
CONFIG_X86_64=y
CONFIG_SMP=y
CONFIG_NR_CPUS=8
CONFIG_HZ_100=y
CONFIG_PREEMPT_VOLUNTARY=y
# Minimal drivers
CONFIG_ATA=y
CONFIG_SATA_AHCI=y
CONFIG_EXT4_FS=y
CONFIG_VFAT_FS=y
CONFIG_TMPFS=y
CONFIG_SQUASHFS=y
# Network
CONFIG_INET=y
CONFIG_NETFILTER=y
# Terminal
CONFIG_VT=y
CONFIG_FB=y
CONFIG_FB_SIMPLE=y
# Disable bloat
CONFIG_SOUND=n
CONFIG_DRM=n
CONFIG_USB_SUPPORT=y
CONFIG_USB_STORAGE=y
# AI acceleration (basic)
CONFIG_CRYPTO=y
CONFIG_CRYPTO_AES=y
CONFIG_CRYPTO_SHA256=y
KCONFIG
    
    log "Building kernel (this may take a while)..."
    make -j$(nproc) bzImage 2>&1 | tail -5
    
    cp arch/x86/boot/bzImage $OUTPUT_DIR/vmlinuz-sid
    log "Kernel built: $OUTPUT_DIR/vmlinuz-sid"
}

build_base_system() {
    header "Building Base System"
    
    # Create root filesystem structure
    mkdir -p $BUILD_DIR/rootfs/{bin,sbin,etc,dev,proc,sys,tmp,var,usr/{bin,lib,share},lib,root,home,sid/{models,memory,config,logs}}
    
    log "Installing base packages..."
    if command -v apk &>/dev/null; then
        # Alpine-based
        apk add --no-cache --root=$BUILD_DIR/rootfs \
            busybox musl libcrypto3 libssl3 ncurses-libs \
            bash python3 sqlite-libs 2>&1 | tail -3
    elif command -v apt-get &>/dev/null; then
        # Debian-based (for development)
        log "Using host packages for development build"
        mkdir -p $BUILD_DIR/rootfs/usr/local/lib
    fi
    
    log "Base system structure created"
}

install_python_deps() {
    header "Installing Python Dependencies"
    
    # Core dependencies (minimal for old hardware)
    pip3 install --target=$BUILD_DIR/rootfs/usr/lib/python3/site-packages \
        --no-deps --quiet \
        numpy 2>/dev/null || true
    
    # Optional dependencies (installed when available)
    log "Optional packages will be installed at first boot"
}

build_llama_cpp() {
    header "Building llama.cpp (AI Inference Engine)"
    
    if [ -d "$BUILD_DIR/llama.cpp" ]; then
        cd $BUILD_DIR/llama.cpp
        git pull --ff-only
    else
        git clone --depth 1 https://github.com/ggerganov/llama.cpp $BUILD_DIR/llama.cpp
        cd $BUILD_DIR/llama.cpp
    fi
    
    mkdir -p build && cd build
    
    # Build minimal llama.cpp without GPU support
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DLLAMA_CUDA=OFF \
        -DLLAMA_METAL=OFF \
        -DLLAMA_VULKAN=OFF \
        -DLLAMA_CLBLAST=OFF \
        -DBUILD_SHARED_LIBS=ON \
        -DLLAMA_STATIC=OFF
    
    make -j$(nproc) llama-server 2>&1 | tail -5
    
    cp bin/llama-server $OUTPUT_DIR/
    log "llama.cpp built"
}

build_whisper_cpp() {
    header "Building whisper.cpp (Speech Recognition)"
    
    if [ -d "$BUILD_DIR/whisper.cpp" ]; then
        cd $BUILD_DIR/whisper.cpp
        git pull --ff-only
    else
        git clone --depth 1 https://github.com/ggerganov/whisper.cpp $BUILD_DIR/whisper.cpp
        cd $BUILD_DIR/whisper.cpp
    fi
    
    make -j$(nproc) whisper-cli 2>&1 | tail -3
    
    cp whisper-cli $OUTPUT_DIR/
    log "whisper.cpp built"
}

create_initramfs() {
    header "Creating Initramfs"
    
    mkdir -p $BUILD_DIR/initramfs
    cd $BUILD_DIR/initramfs
    
    # Create init script
    cat > init << 'INIT'
#!/bin/busybox sh

# SID OS Init Script
/bin/busybox --install -s

# Mount essential filesystems
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev

# Create essential device nodes
mknod /dev/null c 1 3
mknod /dev/zero c 1 5
mknod /dev/tty c 5 0

# Mount root filesystem
mount -t squashfs -o loop /sid.squashfs /mnt/root || mount -t ext4 /dev/sda1 /mnt/root

# Switch to root
exec switch_root /mnt/root /sbin/init
INIT
    
    chmod +x init
    
    # Create minimal busybox-based initramfs
    cd $BUILD_DIR/initramfs
    find . | cpio -H newc -o | gzip > $OUTPUT_DIR/initramfs-sid.gz
    log "Initramfs created"
}

build_sid_iso() {
    header "Creating SID Bootable ISO"
    
    mkdir -p $BUILD_DIR/iso/{boot,isolinux,sid}
    
    # Copy kernel and initramfs
    cp $OUTPUT_DIR/vmlinuz-sid $BUILD_DIR/iso/boot/
    cp $OUTPUT_DIR/initramfs-sid.gz $BUILD_DIR/iso/boot/
    
    # Create isolinux config
    cat > $BUILD_DIR/iso/isolinux/isolinux.cfg << 'ISOCFG'
DEFAULT sid
LABEL sid
    LINUX /boot/vmlinuz-sid
    INITRD /boot/initramfs-sid.gz
    APPEND root=/dev/sda1 console=tty0 quiet loglevel=3
ISOCFG
    
    # Copy SID system files
    cp -r $BUILD_DIR/rootfs/* $BUILD_DIR/iso/sid/
    cp -r $SID_ROOT/src/* $BUILD_DIR/iso/sid/usr/lib/sid/
    
    # Create ISO
    cd $BUILD_DIR/iso
    xorriso -as mkisofs \
        -isohybrid-mbr /usr/share/syslinux/isohdpfx.bin \
        -b isolinux/isolinux.bin \
        -c isolinux/boot.cat \
        -boot-load-size 4 \
        -boot-info-table \
        -no-emul-boot \
        -eltorito-alt-boot \
        -e boot/efiboot.img \
        -no-emul-boot \
        -o $OUTPUT_DIR/sid-${SID_VERSION}-${ARCH}.iso \
        .
    
    log "ISO created: $OUTPUT_DIR/sid-${SID_VERSION}-${ARCH}.iso"
}

cleanup() {
    header "Cleaning Up"
    rm -rf $BUILD_DIR
    log "Build directory cleaned"
}

# Main build process
main() {
    echo ""
    echo "╔══════════════════════════════════════╗"
    echo "║   SID OS Build System v${SID_VERSION}   ║"
    echo "╚══════════════════════════════════════╝"
    echo ""
    
    mkdir -p $BUILD_DIR $OUTPUT_DIR
    
    check_deps
    build_base_system
    install_python_deps
    build_llama_cpp
    build_whisper_cpp
    build_kernel
    create_initramfs
    build_sid_iso
    
    header "Build Complete!"
    echo "  Output: $OUTPUT_DIR/sid-${SID_VERSION}-${ARCH}.iso"
    echo "  Size: $(du -sh $OUTPUT_DIR/sid-${SID_VERSION}-${ARCH}.iso 2>/dev/null | cut -f1)"
    
    ls -lh $OUTPUT_DIR/
}

main "$@"
