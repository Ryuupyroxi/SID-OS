"""SID OS Profile — export/import your AI assistant.
Package settings, soul, memories, skills, and characters into a .sidprofile file.
Share your assistant's personality and knowledge with others."""

import os
import sys
import json
import tarfile
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── Data Paths ────────────────────────────────────────────────
# Where SID stores user data (configurable at runtime)

DATA_PATHS = {
    "config_ai":      "/etc/sid/ai.json",
    "config_soul":    "/etc/sid/soul.json",
    "config_settings":"/etc/sid/settings.json",
    "config_hardware":"/etc/sid/hardware.json",
    "config_context": "/etc/sid/sid_context.md",
    "memory_dir":     "/var/lib/sid/memory",
    "characters_dir": "/etc/sid/characters",
    "skills_dir":     os.path.expanduser("~/.sid/skills"),
    "history_file":   os.path.expanduser("~/.sid_history"),
}

PROFILE_EXT = ".sidprofile"
PROFILE_VERSION = "1.0"

# ── Export ────────────────────────────────────────────────────

def export_profile(output_path: str = "sid-profile.sidprofile",
                   include_memory: bool = True,
                   include_skills: bool = True,
                   include_characters: bool = True,
                   description: str = "") -> str:
    """Export SID OS user data into a portable .sidprofile archive.
    
    Returns the path to the created file.
    
    Example:
        export_profile("my-sid.sidprofile")
        export_profile("backup.sidprofile", include_memory=False)
    """
    output_path = output_path if output_path.endswith(PROFILE_EXT) else output_path + PROFILE_EXT
    output_path = os.path.abspath(output_path)
    
    tmpdir = tempfile.mkdtemp(prefix="sid-profile-")
    try:
        _write_metadata(tmpdir, description)
        _copy_if_exists(DATA_PATHS["config_ai"],       os.path.join(tmpdir, "config", "ai.json"))
        _copy_if_exists(DATA_PATHS["config_soul"],     os.path.join(tmpdir, "config", "soul.json"))
        _copy_if_exists(DATA_PATHS["config_settings"], os.path.join(tmpdir, "config", "settings.json"))
        _copy_if_exists(DATA_PATHS["config_hardware"], os.path.join(tmpdir, "config", "hardware.json"))
        _copy_if_exists(DATA_PATHS["config_context"],  os.path.join(tmpdir, "config", "sid_context.md"))
        
        if include_memory:
            _copy_dir_if_exists(DATA_PATHS["memory_dir"], os.path.join(tmpdir, "memory"))
        
        if include_skills:
            _copy_dir_if_exists(DATA_PATHS["skills_dir"], os.path.join(tmpdir, "skills"))
        
        if include_characters:
            _copy_dir_if_exists(DATA_PATHS["characters_dir"], os.path.join(tmpdir, "characters"))
        
        _copy_if_exists(DATA_PATHS["history_file"], os.path.join(tmpdir, "history.txt"))
        
        # Archive it
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(tmpdir, arcname=os.path.splitext(os.path.basename(output_path))[0])
    
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    size = os.path.getsize(output_path)
    print(f"  📦 Profile exported: {output_path}")
    print(f"     Size: {_format_size(size)}")
    return output_path


# ── Import ────────────────────────────────────────────────────

def import_profile(profile_path: str, dry_run: bool = False) -> dict:
    """Import a .sidprofile into the current SID OS installation.
    
    dry_run=True: show what would be imported without writing.
    Returns summary dict with counts of imported items.
    
    Example:
        import_profile("my-friend.sidprofile")
        import_profile("backup.sidprofile", dry_run=True)
    """
    profile_path = os.path.abspath(profile_path)
    if not os.path.isfile(profile_path):
        raise FileNotFoundError(f"Profile not found: {profile_path}")
    
    summary = {"config": 0, "memory": 0, "skills": 0, "characters": 0, "history": False}
    
    tmpdir = tempfile.mkdtemp(prefix="sid-import-")
    try:
        with tarfile.open(profile_path, "r:gz") as tar:
            tar.extractall(tmpdir)
        
        # Find the extracted root
        entries = os.listdir(tmpdir)
        root = tmpdir
        if len(entries) == 1 and os.path.isdir(os.path.join(tmpdir, entries[0])):
            root = os.path.join(tmpdir, entries[0])
        
        # Read metadata
        meta_path = os.path.join(root, "metadata.json")
        meta = {}
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            print(f"  Profile: {meta.get('name','?')} v{meta.get('version','?')}")
            print(f"  Date: {meta.get('date','?')}")
            if meta.get('description'):
                print(f"  Description: {meta['description']}")
        
        # Import config files
        config_src = os.path.join(root, "config")
        if os.path.isdir(config_src):
            for fname in os.listdir(config_src):
                src = os.path.join(config_src, fname)
                if os.path.isfile(src):
                    dst = _data_path_for(fname)
                    if dry_run:
                        print(f"  [DRY RUN] Would copy config/{fname} → {dst}")
                    else:
                        Path(dst).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                        print(f"  ✅ config/{fname}")
                    summary["config"] += 1
        
        # Import memory
        memory_src = os.path.join(root, "memory")
        if os.path.isdir(memory_src):
            dst = DATA_PATHS.get("memory_dir", "/var/lib/sid/memory")
            for fname in os.listdir(memory_src):
                src = os.path.join(memory_src, fname)
                if os.path.isfile(src):
                    if dry_run:
                        print(f"  [DRY RUN] Would copy memory/{fname}")
                    else:
                        Path(dst).mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, os.path.join(dst, fname))
                        print(f"  ✅ memory/{fname}")
                    summary["memory"] += 1
        
        # Import skills
        skills_src = os.path.join(root, "skills")
        if os.path.isdir(skills_src):
            dst = DATA_PATHS.get("skills_dir", os.path.expanduser("~/.sid/skills"))
            for fname in os.listdir(skills_src):
                src = os.path.join(skills_src, fname)
                if os.path.isdir(src):
                    if dry_run:
                        print(f"  [DRY RUN] Would copy skills/{fname}")
                    else:
                        shutil.copytree(src, os.path.join(dst, fname), dirs_exist_ok=True)
                        print(f"  ✅ skills/{fname}")
                    summary["skills"] += 1
        
        # Import characters
        chars_src = os.path.join(root, "characters")
        if os.path.isdir(chars_src):
            dst = DATA_PATHS.get("characters_dir", "/etc/sid/characters")
            for fname in os.listdir(chars_src):
                src = os.path.join(chars_src, fname)
                if os.path.isfile(src) or os.path.isdir(src):
                    if dry_run:
                        print(f"  [DRY RUN] Would copy characters/{fname}")
                    else:
                        Path(dst).mkdir(parents=True, exist_ok=True)
                        if os.path.isdir(src):
                            shutil.copytree(src, os.path.join(dst, fname), dirs_exist_ok=True)
                        else:
                            shutil.copy2(src, os.path.join(dst, fname))
                        print(f"  ✅ characters/{fname}")
                    summary["characters"] += 1
        
        # Import history
        history_src = os.path.join(root, "history.txt")
        if os.path.isfile(history_src):
            dst = DATA_PATHS.get("history_file", os.path.expanduser("~/.sid_history"))
            if dry_run:
                print(f"  [DRY RUN] Would copy history.txt")
            else:
                shutil.copy2(history_src, dst)
                print(f"  ✅ history.txt")
            summary["history"] = True
    
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    return summary


# ── Character Export/Import (standalone) ──────────────────────

def export_character(character_name: str, output_path: Optional[str] = None) -> str:
    """Export a single character template as a shareable .sidchar file.
    
    Example:
        export_character("sid-bot")
        export_character("my-custom-char", "awesome-char.sidchar")
    """
    if not output_path:
        output_path = f"{character_name}.sidchar"
    output_path = output_path if output_path.endswith(".sidchar") else output_path + ".sidchar"
    
    # Find the character data
    char_data = _find_character(character_name)
    if not char_data:
        raise ValueError(f"Character '{character_name}' not found in registry or /etc/sid/characters/")
    
    tmpdir = tempfile.mkdtemp(prefix="sid-char-")
    try:
        # Write metadata
        meta = {
            "type": "sid-character",
            "name": character_name,
            "version": "1.0",
            "date": datetime.now().isoformat(),
        }
        with open(os.path.join(tmpdir, "metadata.json"), "w") as f:
            json.dump(meta, f, indent=2)
        
        if char_data.get("type") == "ascii":
            # Export as JSON
            with open(os.path.join(tmpdir, "character.json"), "w") as f:
                json.dump(char_data, f, indent=2)
        elif char_data.get("type") == "spritesheet":
            # Export spritesheet PNG + metadata
            src = char_data.get("source", "")
            if src and os.path.isfile(src):
                shutil.copy2(src, os.path.join(tmpdir, "spritesheet.png"))
            with open(os.path.join(tmpdir, "character.json"), "w") as f:
                # Strip source path, use relative reference
                export_data = dict(char_data)
                export_data["source"] = "spritesheet.png"
                json.dump(export_data, f, indent=2)
        
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(tmpdir, arcname=character_name)
    
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    print(f"  🎭 Character exported: {output_path}")
    return output_path


def import_character(char_path: str) -> str:
    """Import a .sidchar file into the character registry.
    
    Example:
        import_character("awesome-char.sidchar")
    """
    char_path = os.path.abspath(char_path)
    if not os.path.isfile(char_path):
        raise FileNotFoundError(f"Character file not found: {char_path}")
    
    tmpdir = tempfile.mkdtemp(prefix="sid-char-import-")
    try:
        with tarfile.open(char_path, "r:gz") as tar:
            tar.extractall(tmpdir)
        
        # Find the character name
        entries = os.listdir(tmpdir)
        char_name = entries[0] if entries else "imported"
        char_dir = os.path.join(tmpdir, char_name)
        
        meta_path = os.path.join(char_dir, "metadata.json")
        char_json_path = os.path.join(char_dir, "character.json")
        sprite_path = os.path.join(char_dir, "spritesheet.png")
        
        if not os.path.isfile(char_json_path):
            raise ValueError("Invalid character file: no character.json")
        
        with open(char_json_path) as f:
            char_data = json.load(f)
        
        name = char_data.get("name", char_name)
        chars_dir = DATA_PATHS.get("characters_dir", "/etc/sid/characters")
        Path(chars_dir).mkdir(parents=True, exist_ok=True)
        
        if char_data.get("type") == "spritesheet" and os.path.isfile(sprite_path):
            # Copy spritesheet, fix source path
            sprite_dst = os.path.join(chars_dir, f"{name}.png")
            shutil.copy2(sprite_path, sprite_dst)
            char_data["source"] = sprite_dst
            with open(os.path.join(chars_dir, f"{name}.json"), "w") as f:
                json.dump(char_data, f, indent=2)
            print(f"  ✅ Character '{name}' installed (spritesheet)")
        else:
            # ASCII character — save JSON
            with open(os.path.join(chars_dir, f"{name}.json"), "w") as f:
                json.dump(char_data, f, indent=2)
            print(f"  ✅ Character '{name}' installed (ASCII template)")
        
        return name
    
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Helpers ───────────────────────────────────────────────────

def _write_metadata(tmpdir: str, description: str = ""):
    meta = {
        "type": "sid-profile",
        "version": PROFILE_VERSION,
        "date": datetime.now().isoformat(),
        "os": f"SID OS v{getattr(sys, 'sid_version', '?')}",
        "description": description,
    }
    Path(tmpdir, "metadata.json").parent.mkdir(parents=True, exist_ok=True)
    with open(os.path.join(tmpdir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)


def _copy_if_exists(src: str, dst: str):
    if os.path.isfile(src):
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _copy_dir_if_exists(src: str, dst: str):
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)


def _data_path_for(filename: str) -> str:
    """Map config filename back to its system path."""
    mapping = {
        "ai.json": DATA_PATHS["config_ai"],
        "soul.json": DATA_PATHS["config_soul"],
        "settings.json": DATA_PATHS["config_settings"],
        "hardware.json": DATA_PATHS["config_hardware"],
        "sid_context.md": DATA_PATHS["config_context"],
    }
    return mapping.get(filename, os.path.join("/etc/sid", filename))


def _find_character(name: str) -> Optional[dict]:
    """Find a character by name in registry or filesystem."""
    # Check runtime registry
    try:
        from src.terminal.assistant.character import CHARACTERS
        if name in CHARACTERS:
            return CHARACTERS[name]
    except ImportError:
        pass
    
    # Check filesystem
    chars_dir = DATA_PATHS.get("characters_dir", "/etc/sid/characters")
    json_path = os.path.join(chars_dir, f"{name}.json")
    if os.path.isfile(json_path):
        with open(json_path) as f:
            return json.load(f)
    
    return None


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/1024**2:.1f} MB"


# ── CLI ───────────────────────────────────────────────────────

def main():
    """Command-line entry point for profile operations."""
    if len(sys.argv) < 2:
        print("Usage: profile <export|import|char-export|char-import> [options]")
        print("  profile export [output.sidprofile]")
        print("  profile import <file.sidprofile>")
        print("  profile char-export <char-name> [output.sidchar]")
        print("  profile char-import <file.sidchar>")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "export":
        path = sys.argv[2] if len(sys.argv) > 2 else "sid-profile.sidprofile"
        export_profile(path)
    elif cmd == "import":
        if len(sys.argv) < 3:
            print("Usage: profile import <file.sidprofile>")
            return
        import_profile(sys.argv[2])
    elif cmd == "char-export":
        if len(sys.argv) < 3:
            print("Usage: profile char-export <char-name> [output.sidchar]")
            return
        out = sys.argv[3] if len(sys.argv) > 3 else None
        export_character(sys.argv[2], out)
    elif cmd == "char-import":
        if len(sys.argv) < 3:
            print("Usage: profile char-import <file.sidchar>")
            return
        import_character(sys.argv[2])
    elif cmd == "dry-run":
        if len(sys.argv) < 3:
            print("Usage: profile dry-run <file.sidprofile>")
            return
        import_profile(sys.argv[2], dry_run=True)
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
