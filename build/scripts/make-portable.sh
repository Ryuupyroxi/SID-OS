#!/bin/bash
# SID OS Portable Release Builder
# Creates a self-contained portable tarball for any Linux system
# Usage: ./build/scripts/make-portable.sh [output_dir]

set -e
VERSION="0.5.0"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="${1:-$PROJECT_DIR/build/output}"

echo "╔══════════════════════════════════════════╗"
echo "║   SID OS Portable Release Builder        ║"
echo "╚══════════════════════════════════════════╝"
echo "  Project: $PROJECT_DIR"
echo "  Output:  $OUTPUT_DIR"

mkdir -p "$OUTPUT_DIR"
PORTABLE_DIR=$(mktemp -d)
echo "[1/5] Creating portable structure..."

# Copy SID files
cp -r "$PROJECT_DIR/src" "$PORTABLE_DIR/"
cp -r "$PROJECT_DIR/config" "$PORTABLE_DIR/"
cp -r "$PROJECT_DIR/installer" "$PORTABLE_DIR/"
cp "$PROJECT_DIR/AGENTS.md" "$PROJECT_DIR/README.md" "$PROJECT_DIR/test_sid.py" "$PROJECT_DIR/get-sid.py" "$PROJECT_DIR/get-sid.bat" "$PROJECT_DIR/get-sid.ps1" "$PORTABLE_DIR/"
chmod +x "$PORTABLE_DIR/src/main.py"
chmod +x "$PORTABLE_DIR/installer/scripts/install.py"
chmod +x "$PORTABLE_DIR/get-sid.py"
chmod +x "$PORTABLE_DIR/get-sid.bat"

# Create launcher scripts
cat > "$PORTABLE_DIR/sid" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
python3 src/main.py "$@"
LAUNCHER
chmod +x "$PORTABLE_DIR/sid"

cat > "$PORTABLE_DIR/sid-install" << 'INSTALL'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
python3 installer/scripts/install.py "$@"
INSTALL
chmod +x "$PORTABLE_DIR/sid-install"

cat > "$PORTABLE_DIR/sid-test" << 'TEST'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
python3 test_sid.py "$@"
TEST
chmod +x "$PORTABLE_DIR/sid-test"

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
sid-test.bat --verbose
sid-install.bat
```

## Requirements
- Python 3.8+
- 4GB RAM recommended
- No GPU required
- Windows: Python must be in PATH (get it at python.org)
- Linux: bash + python3

## Troubleshooting
| Problem | Fix |
|---------|-----|
| `python3` not found (Linux) | Try `python` instead |
| `python` not found (Windows) | Install Python from python.org, check "Add to PATH" |
| "No module named..." | Run from the extracted directory |
| Black screen | Use `--theme terminal` |
HELP

echo "[2/5] Creating portable tarball..."
cd "$PORTABLE_DIR"
tar czf "$OUTPUT_DIR/sid-${VERSION}-portable.tar.gz" \
    --owner=0 --group=0 \
    .

echo "[3/5] Creating checksums..."
cd "$OUTPUT_DIR"
sha256sum "sid-${VERSION}-portable.tar.gz" > "sid-${VERSION}-portable.tar.gz.sha256"
md5sum "sid-${VERSION}-portable.tar.gz" > "sid-${VERSION}-portable.tar.gz.md5"

echo "[4/5] Cleaning up..."
rm -rf "$PORTABLE_DIR"

echo "[5/5] Done!"
echo ""
ls -lh "$OUTPUT_DIR"/sid-${VERSION}-portable*
echo ""
echo "Use: tar xzf sid-${VERSION}-portable.tar.gz && cd sid-${VERSION}-portable && ./sid"
