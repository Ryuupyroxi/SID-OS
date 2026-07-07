#!/bin/bash
# SID OS Portable Release Builder
# Creates a self-contained portable tarball for any Linux system
set -eo pipefail

VERSION="0.5.2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="${1:-$PROJECT_DIR/build/output}"

echo "╔══════════════════════════════════════════╗"
echo "║   SID OS Portable Release Builder        ║"
echo "╚══════════════════════════════════════════╝"

# Resolve OUTPUT_DIR to absolute path
case "$OUTPUT_DIR" in
  /*) ;;
  *) OUTPUT_DIR="$PWD/$OUTPUT_DIR" ;;
esac

echo "  Project: $PROJECT_DIR"
echo "  Output:  $OUTPUT_DIR"

mkdir -p "$OUTPUT_DIR" || { echo "ERROR: Cannot create $OUTPUT_DIR"; exit 1; }
PORTABLE_DIR=$(mktemp -d) || { echo "ERROR: Cannot create temp dir"; exit 1; }
echo "[1/5] Creating portable structure..."

# Copy SID files - handle each file individually to avoid failures
cp -r "$PROJECT_DIR/src" "$PORTABLE_DIR/" 2>&1
cp -r "$PROJECT_DIR/config" "$PORTABLE_DIR/" 2>&1
cp -r "$PROJECT_DIR/installer" "$PORTABLE_DIR/" 2>&1
for f in AGENTS.md README.md test_sid.py get-sid.py get-sid.bat get-sid.ps1; do
  cp "$PROJECT_DIR/$f" "$PORTABLE_DIR/" 2>&1 || echo "  Warning: $f not found"
done

# Make scripts executable
chmod +x "$PORTABLE_DIR/src/main.py" 2>/dev/null || true
chmod +x "$PORTABLE_DIR/installer/scripts/install.py" 2>/dev/null || true
chmod +x "$PORTABLE_DIR/get-sid.py" 2>/dev/null || true
chmod +x "$PORTABLE_DIR/get-sid.bat" 2>/dev/null || true

# Create launcher scripts
cat > "$PORTABLE_DIR/sid" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec python3 src/main.py "$@"
LAUNCHER

cat > "$PORTABLE_DIR/sid-install" << 'INSTALL'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec python3 installer/scripts/install.py "$@"
INSTALL

cat > "$PORTABLE_DIR/sid-test" << 'TEST'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec python3 test_sid.py "$@"
TEST

chmod +x "$PORTABLE_DIR/sid" "$PORTABLE_DIR/sid-install" "$PORTABLE_DIR/sid-test"

cat > "$PORTABLE_DIR/BOOT_HELPER.md" << 'HELP'
# SID OS Portable — Quick Start

## Linux / macOS
```bash
./sid --theme vt100
./sid-test --verbose
sudo ./sid-install
```

## Windows (cmd.exe or PowerShell)
```batch
sid.bat --theme vt100
get-sid.bat
```

## Requirements
- Python 3.8+
- 4GB RAM recommended
- No GPU required
HELP

echo "[2/5] Creating portable tarball..."
cd "$PORTABLE_DIR"
tar czf "$OUTPUT_DIR/sid-${VERSION}-portable.tar.gz" \
    --owner=0 --group=0 \
    . 2>&1 || { echo "ERROR: tar failed"; exit 1; }

echo "[3/5] Creating checksums..."
cd "$OUTPUT_DIR"
sha256sum "sid-${VERSION}-portable.tar.gz" > "sid-${VERSION}-portable.tar.gz.sha256" 2>/dev/null || true
md5sum "sid-${VERSION}-portable.tar.gz" > "sid-${VERSION}-portable.tar.gz.md5" 2>/dev/null || true

echo "[4/5] Cleaning up..."
rm -rf "$PORTABLE_DIR"

echo "[5/5] Done!"
echo ""
ls -lh "$OUTPUT_DIR"/sid-${VERSION}-portable* 2>/dev/null || echo "  Check: $OUTPUT_DIR"
echo ""
