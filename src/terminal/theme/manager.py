"""SID Theme Manager - Iconic CLI computer themes.
Each theme recreates the look and feel of a legendary computer terminal."""
from typing import Dict, Tuple, Optional, List
import shutil

class Theme:
    """Computer terminal theme definition."""
    def __init__(self, name: str, computer: str, year: str,
                 fg: str, bg: str, accent: str, dim: str, prompt: str,
                 font: str = "monospace", cursor: str = "block",
                 description: str = ""):
        self.name = name
        self.computer = computer
        self.year = year
        self.fg = fg
        self.bg = bg
        self.accent = accent
        self.dim = dim
        self.prompt = prompt
        self.font = font
        self.cursor = cursor
        self.description = description or f"{computer} ({year})"

    def to_curses(self):
        return {'fg': self.fg, 'bg': self.bg, 'accent': self.accent, 
                'dim': self.dim, 'prompt': self.prompt}

class ThemeManager:
    """Manages retro computer terminal themes."""

    THEMES = {
        # ===== LEGENDARY CLI COMPUTERS =====
        "vt100": Theme(
            "VT100", "DEC VT100", "1978",
            "#CCCCCC", "#000000", "#FFFFFF", "#666666", "#00FF00",
            description="The terminal that defined modern terminal emulation"
        ),
        "ibm3270": Theme(
            "IBM 3270", "IBM 3270", "1971",
            "#00FF00", "#000000", "#FFFF00", "#006600", "#00CC00",
            description="IBM's legendary mainframe terminal - green screen"
        ),
        "apple2": Theme(
            "Apple II", "Apple II", "1977",
            "#40FF40", "#000000", "#FFFF40", "#004000", "#80FF80",
            description="Wozniak's masterpiece - green phosphor on black"
        ),
        "c64": Theme(
            "Commodore 64", "Commodore 64", "1982",
            "#6A5ACD", "#000022", "#E0E0FF", "#2A1A5D", "#8A7ADD",
            description="Best-selling computer - light blue on dark blue"
        ),
        "trs80": Theme(
            "TRS-80", "TRS-80 Model I", "1977",
            "#00FF00", "#000800", "#FFFF00", "#005500", "#00CC00",
            description="Radio Shack's 'Trash 80' - iconic green screen"
        ),
        "altair": Theme(
            "Altair 8800", "MITS Altair 8800", "1975",
            "#FF6600", "#000000", "#FFAA00", "#552200", "#FF8800",
            description="Birth of the personal computer - amber front panel"
        ),
        "xerox_alto": Theme(
            "Xerox Alto", "Xerox Alto", "1973",
            "#FFFFFF", "#000000", "#8888FF", "#555555", "#FFFFFF",
            description="The first GUI computer (portrait monitor)"
        ),
        "sgi_iris": Theme(
            "SGI Iris", "SGI Iris 4D", "1986",
            "#00CCCC", "#000808", "#FF6600", "#004444", "#00FFFF",
            description="SGI's IRIS console - teal on black"
        ),
        "sun_micro": Theme(
            "SunOS", "Sun Microsystems", "1982",
            "#FFCC00", "#000000", "#FFFFFF", "#665500", "#FFFF00",
            description="SunOS console - amber on black"
        ),
        "nextstep": Theme(
            "NeXTSTEP", "NeXT Computer", "1988",
            "#CCCCCC", "#000000", "#00FF00", "#555555", "#666666",
            description="Jobs' NeXT - the machine that inspired the web"
        ),
        "ibm_pc": Theme(
            "IBM PC-DOS", "IBM 5150", "1981",
            "#FFFFFF", "#000000", "#FF0000", "#555555", "#CCCCCC",
            description="The original IBM PC - white on black"
        ),
        "amiga": Theme(
            "Amiga Workbench", "Commodore Amiga 1000", "1985",
            "#8888FF", "#000044", "#00FF88", "#333377", "#AAAAFF",
            description="The Amiga CLI - years ahead of its time"
        ),
        "teletype": Theme(
            "TeleType", "ASR-33 Teletype", "1963",
            "#222222", "#FFFFCC", "#000000", "#888866", "#333333",
            description="The original computing interface - paper terminal"
        ),
        "dragon32": Theme(
            "Dragon 32", "Dragon 32", "1982",
            "#00AA00", "#000000", "#00FF00", "#004400", "#00CC00",
            description="The Dragon 32 - green on black"
        ),
        "zx_spectrum": Theme(
            "ZX Spectrum", "Sinclair ZX Spectrum", "1982",
            "#FF00FF", "#000000", "#FFFF00", "#660066", "#FF44FF",
            description="The Spectrum's iconic magenta on black"
        ),
        "acorn": Theme(
            "Acorn BBC", "BBC Micro", "1981",
            "#66FF66", "#000000", "#FFFF66", "#226622", "#99FF99",
            description="The BBC Micro - green screen, British computing icon"
        ),
        "macintosh": Theme(
            "Macintosh", "Macintosh 128K", "1984",
            "#FFFFFF", "#000000", "#888888", "#444444", "#BBBBBB",
            description="The Mac's black & white CLI"
        ),
        "cp_m": Theme(
            "CP/M", "Osborne 1", "1981",
            "#00FF00", "#001000", "#AAFFAA", "#004400", "#00DD00",
            description="The original portable computer's OS"
        ),
    }

    def __init__(self):
        self.current = "vt100"
        self.terminal_width = shutil.get_terminal_size().columns

    def get_theme(self, name: Optional[str] = None) -> Theme:
        return self.THEMES.get(name or self.current, self.THEMES["vt100"])

    def set_theme(self, name: str) -> bool:
        if name in self.THEMES:
            self.current = name
            return True
        # Try partial match
        matches = [k for k in self.THEMES if name.lower() in k.lower()]
        if matches:
            self.current = matches[0]
            return True
        return False

    def list_themes(self) -> List[Dict]:
        """List all themes with descriptions."""
        return [
            {"id": k, "name": v.computer, "year": v.year, "desc": v.description}
            for k, v in self.THEMES.items()
        ]

    def get_era(self, year: str) -> List[str]:
        """Get themes from a specific era."""
        decade = year[:3] + "0"
        return [k for k, v in self.THEMES.items() if v.year.startswith(decade)]

    def get_ansi(self, theme_name: Optional[str] = None) -> Dict:
        """Get ANSI escape codes for current theme."""
        theme = self.get_theme(theme_name)
        return {
            "HEADER": f"\033[38;2;{self._hex_to_rgb(theme.accent)}m",
            "OKBLUE": f"\033[38;2;{self._hex_to_rgb(theme.fg)}m",
            "OKGREEN": f"\033[38;2;{self._hex_to_rgb(theme.prompt)}m",
            "WARNING": f"\033[38;2;{self._hex_to_rgb(theme.accent)}m",
            "FAIL": "\033[91m",
            "ENDC": "\033[0m",
            "BOLD": "\033[1m",
            "DIM": f"\033[38;2;{self._hex_to_rgb(theme.dim)}m",
        }

    def _hex_to_rgb(self, hex_color: str) -> str:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r};{g};{b}"

    def colorize(self, text: str, style: str = "fg", theme_name: Optional[str] = None) -> str:
        """Apply theme color to text."""
        theme = self.get_theme(theme_name)
        ansi = self.get_ansi(theme_name)
        color_map = {
            "fg": ansi["OKBLUE"], "accent": ansi["HEADER"],
            "prompt": ansi["OKGREEN"], "dim": ansi["DIM"], "error": ansi["FAIL"],
        }
        c = color_map.get(style, ansi["OKBLUE"])
        return f"{c}{text}{ansi['ENDC']}"

    def boot_screen(self, theme_name: Optional[str] = None) -> str:
        """Generate retro boot screen for the current theme."""
        theme = self.get_theme(theme_name)
        a = self.get_ansi(theme_name)
        
        art = f"""
{a['HEADER']}╔══════════════════════════════════════════════════╗
{a['HEADER']}║{a['BOLD']}          SID v0.0.4 - SUPER INTELLIGENT DISTRO        {a['HEADER']}║
{a['HEADER']}║{a['DIM']}       {theme.description:<42} {a['HEADER']}║
{a['HEADER']}║{a['BOLD']}          ███████╗██╗██████╗                        {a['HEADER']}║
{a['HEADER']}║{a['BOLD']}          ██╔════╝██║██╔══██╗                       {a['HEADER']}║
{a['HEADER']}║{a['BOLD']}          ███████╗██║██║  ██║                       {a['HEADER']}║
{a['HEADER']}║{a['BOLD']}          ╚════██║██║██║  ██║                       {a['HEADER']}║
{a['HEADER']}║{a['BOLD']}          ███████║██║██████╔╝                       {a['HEADER']}║
{a['HEADER']}║{a['BOLD']}          ╚══════╝╚═╝╚═════╝                        {a['HEADER']}║
{a['HEADER']}╠══════════════════════════════════════════════════╣
{a['HEADER']}║{a['OKGREEN']}     {theme.name:<12}  |  AI CORE: ACTIVE  |  MEM: OPTIMIZED  {a['HEADER']}║
{a['HEADER']}║{a['DIM']}     {theme.computer} ({theme.year})                 {a['HEADER']}║
{a['HEADER']}╚══════════════════════════════════════════════════╝{a['ENDC']}"""
        return art
