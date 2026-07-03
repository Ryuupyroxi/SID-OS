"""SID Theme Manager - Themes based on iconic CLI computers from computing history.
Each theme matches the actual color palette, phosphor, and character of a real machine."""
from typing import Dict, Tuple, Optional, List

class Theme:
    """Color theme based on a real iconic computer."""
    def __init__(self, name: str, fg: str, bg: str, accent: str, 
                 dim: str, prompt: str, year: int = 1980,
                 computer: str = "Generic Terminal", font: str = "monospace",
                 description: str = ""):
        self.name = name
        self.fg = fg
        self.bg = bg
        self.accent = accent
        self.dim = dim
        self.prompt = prompt
        self.year = year
        self.computer = computer
        self.font = font
        self.description = description

class ThemeManager:
    """Manages themes based on iconic CLI computers."""

    THEMES = {
        # === ICONIC MAINFRAMES & MINICOMPUTERS ===
        "pdp11": Theme(
            "PDP-11", "#FFFF00", "#001800", "#FFFF66",
            "#555500", "#FFFF00", 1970,
            "DEC PDP-11/70", "monospace",
            "DEC's legendary minicomputer - amber-on-green VT100 feel"
        ),
        "vt100": Theme(
            "VT100", "#FFB000", "#1A0E00", "#FFD700",
            "#664400", "#FFA500", 1978,
            "DEC VT100 Terminal", "monospace",
            "The definitive terminal - amber phosphor on dark background"
        ),
        "ibm3270": Theme(
            "IBM 3270", "#00FF00", "#000800", "#33FF33",
            "#005500", "#00CC00", 1972,
            "IBM 3270 Terminal", "monospace",
            "IBM's mainframe terminal - bright green on near-black"
        ),
        "ibmpc": Theme(
            "IBM PC-DOS", "#CCCCCC", "#000000", "#FFFFFF",
            "#666666", "#00FF00", 1981,
            "IBM PC 5150 / MS-DOS", "monospace",
            "The original IBM PC - white text, amber/green prompt"
        ),
        "apple2": Theme(
            "Apple II", "#00FF00", "#000800", "#80FF80",
            "#004400", "#FFFF00", 1977,
            "Apple II / ProDOS", "monospace",
            "Woz's masterpiece - green phosphor with yellow prompt"
        ),
        "commodore": Theme(
            "Commodore 64", "#4488FF", "#000828", "#66AAFF",
            "#223366", "#FFFFFF", 1982,
            "Commodore 64 / BASIC", "monospace",
            "The best-selling computer - blue screen with white text"
        ),
        "tandy": Theme(
            "Tandy TRS-80", "#00FF00", "#001000", "#33FF33",
            "#005500", "#00FF00", 1977,
            "Tandy TRS-80 Model I", "monospace",
            "The 'Trash-80' - iconic green display, black background"
        ),
        "atari": Theme(
            "Atari 800", "#FF8800", "#001000", "#FFAA44",
            "#553300", "#FF8800", 1979,
            "Atari 800 / XL", "monospace",
            "Atari's 8-bit line - warm amber tones"
        ),
        
        # === UNIX WORKSTATIONS ===
        "sun": Theme(
            "Sun SPARC", "#FFFF00", "#000800", "#FFFF33",
            "#555500", "#FFCC00", 1987,
            "Sun SPARCstation / SunOS", "monospace",
            "Sun Microsystems - the original 'yellow on dark green' UNIX feel"
        ),
        "sgi": Theme(
            "SGI IRIX", "#00CCCC", "#000808", "#66FFFF",
            "#005555", "#00FF00", 1988,
            "SGI Indigo / IRIX", "monospace",
            "Silicon Graphics - cyan/teal aesthetic of the 90s UNIX desktop"
        ),
        "next": Theme(
            "NeXTSTEP", "#FFFFFF", "#000000", "#8888FF",
            "#555555", "#FF0000", 1988,
            "NeXTcube / NeXTSTEP", "monospace",
            "Jobs' NeXT - crisp white on black with red prompt"
        ),
        
        # === RETRO SOFTWARE ===
        "dos": Theme(
            "MS-DOS 6.22", "#CCCCCC", "#000000", "#FFFFFF",
            "#666666", "#AAAAAA", 1993,
            "MS-DOS 6.22", "monospace",
            "Classic DOS - light gray text, C:\> prompt"
        ),
        "norton": Theme(
            "Norton Commander", "#88FFFF", "#000088", "#FFFFFF",
            "#4444AA", "#FFFF00", 1986,
            "Norton Commander", "monospace",
            "The file manager we all used - cyan on blue with yellow accents"
        ),
        "turbo": Theme(
            "Turbo C IDE", "#FFFF00", "#000088", "#FFFFFF",
            "#888800", "#FFFF00", 1987,
            "Turbo C / Turbo Pascal IDE", "monospace",
            "Borland's iconic IDE - yellow on blue, the development environment"
        ),
        
        # === MODERN RETRO ===
        "matrix": Theme(
            "Matrix Rain", "#00FF41", "#000800", "#80FF80",
            "#005500", "#00FF00", 1999,
            "The Matrix (green rain)", "monospace",
            "Matrix digital rain green - iconic dark green"
        ),
        "fallout": Theme(
            "Fallout Terminal", "#00FF00", "#001000", "#33FF33",
            "#005500", "#FFFF00", 1997,
            "Fallout Pip-Boy 2000", "monospace",
            "Post-apocalyptic green display - like the Pip-Boy"
        ),
        "cyberpunk": Theme(
            "Cyberpunk 2077", "#FFFF00", "#0A0020", "#FF00FF",
            "#550055", "#00FFFF", 2077,
            "Cyberpunk Terminal", "monospace",
            "Neon yellow on dark purple - the future of retro"
        ),
    }

    def __init__(self):
        self.current = "vt100"  # Default: DEC VT100 - the terminal
        self.custom_bg_char = " "

    def get_theme(self, name: Optional[str] = None) -> Theme:
        return self.THEMES.get(name or self.current, self.THEMES["vt100"])

    def set_theme(self, name: str) -> bool:
        if name in self.THEMES:
            self.current = name
            return True
        return False

    def list_themes(self) -> List[str]:
        return list(self.THEMES.keys())

    def list_with_details(self) -> List[Dict]:
        """List themes with their computer names and descriptions."""
        return [
            {
                "id": tid,
                "name": t.name,
                "computer": t.computer,
                "year": t.year,
                "description": t.description,
                "active": tid == self.current
            }
            for tid, t in self.THEMES.items()
        ]

    def get_ansi_theme(self) -> Dict:
        """Get ANSI escape codes for the current theme."""
        theme = self.get_theme()
        return {
            "HEADER": f"\033[38;2;{self._hex_to_rgb(theme.accent)}m",
            "OKBLUE": f"\033[38;2;{self._hex_to_rgb(theme.fg)}m",
            "OKGREEN": f"\033[38;2;{self._hex_to_rgb(theme.prompt)}m",
            "WARNING": f"\033[38;2;{self._hex_to_rgb(theme.accent)}m",
            "FAIL": "\033[91m",
            "ENDC": "\033[0m",
            "BOLD": "\033[1m",
            "DIM": f"\033[38;2;{self._hex_to_rgb(theme.dim)}m",
            "BG": f"\033[48;2;{self._hex_to_rgb(theme.bg)}m" if theme.bg != "#000000" else "",
        }

    def _hex_to_rgb(self, hex_color: str) -> str:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r};{g};{b}"

    def apply_to_text(self, text: str, style: str = "fg") -> str:
        """Apply theme color to text."""
        theme = self.get_theme()
        ansi = self.get_ansi_theme()
        color_map = {
            "fg": ansi["OKBLUE"], "accent": ansi["HEADER"],
            "prompt": ansi["OKGREEN"], "dim": ansi["DIM"], "error": ansi["FAIL"],
        }
        c = color_map.get(style, ansi["OKBLUE"])
        return f"{c}{text}{ansi['ENDC']}"

    def get_theme_info(self) -> str:
        """Get current theme info string."""
        t = self.get_theme()
        return f"{t.name} ({t.computer}, {t.year})"

    def boot_screen(self) -> str:
        """Generate retro boot screen based on themed computer."""
        theme = self.get_theme()
        a = self.get_ansi_theme()
        
        # Different ASCII art based on the computer
        logomap = {
            "pdp11": "☐ DEC PDP-11/70",
            "vt100": "☐ VT100 TERMINAL",
            "ibm3270": "☐ IBM 3270",
            "ibmpc": "☐ IBM PC 5150",
            "apple2": "☐ Apple ][",
            "commodore": "☐ COMMODORE 64",
            "tandy": "☐ TRS-80 Model I",
            "atari": "☐ ATARI 800XL",
            "sun": "☐ SUN SPARCstation",
            "sgi": "☐ SGI INDY",
            "next": "☐ NeXTcube",
            "dos": "☐ MS-DOS 6.22",
            "norton": "☐ NORTON COMMANDER",
            "turbo": "☐ TURBO C IDE",
            "matrix": "☐ THE MATRIX",
            "fallout": "☐ PIP-BOY 3000",
            "cyberpunk": "☐ CYBERPUNK TERMINAL",
        }
        logo = logomap.get(self.current, "☐ SID TERMINAL")

        art = f"""
{a['HEADER']}╔══════════════════════════════════════════════════╗
{a['HEADER']}║{a['BOLD']}     SID v1.0 - SUPER INTELLIGENT DISTRO       {a['HEADER']}║
{a['HEADER']}║{a['DIM']}     ════════════════════════════════════════     {a['HEADER']}║
{a['HEADER']}║{a['BOLD']}     {logo:<39} {a['HEADER']}║
{a['HEADER']}║{a['DIM']}     {theme.description:<39} {a['HEADER']}║
{a['HEADER']}╠══════════════════════════════════════════════════╣
{a['HEADER']}║{a['OKGREEN']}     System: {theme.computer:<30} {a['HEADER']}║
{a['HEADER']}║{a['DIM']}     Theme Year: {theme.year} | RAM Tier: auto   {a['HEADER']}║
{a['HEADER']}╚══════════════════════════════════════════════════╝{a['ENDC']}"""
        return art
