"""SID Cross-Platform Compatibility Layer.
Handles differences between Linux, macOS, and Windows so the
rest of the codebase doesn't need to think about it."""
import os
import sys
import platform as _platform
from pathlib import Path
from typing import Dict, Optional

SYSTEM = _platform.system().lower()  # 'linux', 'darwin', 'windows'
IS_WINDOWS = SYSTEM == 'windows'
IS_LINUX = SYSTEM == 'linux'
IS_MAC = SYSTEM == 'darwin'

def get_data_dir() -> str:
    """Get platform-appropriate data directory."""
    if IS_WINDOWS:
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return str(Path(base) / 'sid')
    else:
        return '/var/lib/sid'

def get_config_dir() -> str:
    """Get platform-appropriate config directory."""
    if IS_WINDOWS:
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return str(Path(base) / 'sid' / 'config')
    else:
        return '/etc/sid'

def get_cache_dir() -> str:
    """Get platform-appropriate cache directory."""
    if IS_WINDOWS:
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        return str(Path(base) / 'sid' / 'cache')
    else:
        return '/var/lib/sid/cache'

def get_models_dir() -> str:
    """Get platform-appropriate models directory."""
    if IS_WINDOWS:
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        return str(Path(base) / 'sid' / 'models')
    else:
        return '/sid/models'

def get_soul_path() -> str:
    """Get platform-appropriate soul file path."""
    return str(Path(get_config_dir()) / 'soul.json')

def get_ai_config_path() -> str:
    """Get platform-appropriate AI config path."""
    return str(Path(get_config_dir()) / 'ai.json')

def get_settings_path() -> str:
    """Get platform-appropriate settings path."""
    return str(Path(get_config_dir()) / 'settings.json')

def get_hardware_config_path() -> str:
    """Get platform-appropriate hardware config path."""
    return str(Path(get_config_dir()) / 'hardware.json')

def get_sid_root() -> Path:
    """Get the SID OS installation root directory."""
    # Check common locations
    candidates = [
        Path(__file__).parent.parent,  # Development: src/../SID-OS/
        Path(os.path.expanduser('~')) / 'SID-OS',
        Path('/opt/sid'),
        Path('/usr/share/sid'),
    ]
    for p in candidates:
        if (p / 'src' / 'main.py').exists():
            return p
    return Path(__file__).parent.parent

def get_launcher_script() -> str:
    """Get the platform-appropriate launcher script name."""
    return 'sid.bat' if IS_WINDOWS else 'sid'

def get_test_script() -> str:
    """Get the platform-appropriate test script name."""
    return 'sid-test.bat' if IS_WINDOWS else 'sid-test'

def get_install_script() -> str:
    """Get the platform-appropriate install script name."""
    return 'sid-install.bat' if IS_WINDOWS else 'sid-install'

def get_default_shell() -> str:
    """Get the default shell for the platform."""
    if IS_WINDOWS:
        return os.environ.get('COMSPEC', 'cmd.exe')
    return os.environ.get('SHELL', '/bin/bash')

def has_signal_handling() -> bool:
    """Check if signal handling is available."""
    return not IS_WINDOWS

def is_admin() -> bool:
    """Check if running with admin/root privileges."""
    if IS_WINDOWS:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    return os.geteuid() == 0

def home_dir() -> str:
    """Get the user's home directory."""
    return os.path.expanduser('~')

def get_platform_info() -> Dict:
    """Get comprehensive platform information."""
    return {
        'system': SYSTEM,
        'is_windows': IS_WINDOWS,
        'is_linux': IS_LINUX,
        'is_mac': IS_MAC,
        'python': sys.version,
        'machine': _platform.machine(),
        'processor': _platform.processor(),
        'data_dir': get_data_dir(),
        'config_dir': get_config_dir(),
        'cache_dir': get_cache_dir(),
        'soul_path': get_soul_path(),
        'launcher': get_launcher_script(),
        'has_admin': is_admin(),
        'home': home_dir(),
    }
