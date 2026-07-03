"""SID Tools - Complete AI-powered tool suite for the operating system."""
from .code.assistant import CodeAssistant
from .files.manager import FileManager
from .search.engine import SearchEngine
from .system.analyzer import SystemAnalyzer
from .media_player import MediaPlayer
from .offline_storage import OfflineStorage
from .browser_fs import BrowserFileExplorer
from .image_tools import ImageTools
from .offline_cache import OfflineCache
from .benchmark import HardwareBenchmark
from .settings import SettingsManager

class ToolSuite:
    """Complete collection of AI-powered OS tools."""

    def __init__(self, ai_orchestrator=None):
        self.ai = ai_orchestrator
        self.code = CodeAssistant(ai_orchestrator)
        self.files = FileManager(ai_orchestrator)
        self.search = SearchEngine(ai_orchestrator)
        self.system = SystemAnalyzer(ai_orchestrator)
        self.media = MediaPlayer(ai_orchestrator)
        self.storage = OfflineStorage()
        self.browser = BrowserFileExplorer()
        self.image = ImageTools(ai_orchestrator)
        self.cache = OfflineCache()
        self.benchmark = HardwareBenchmark()
        self.settings = SettingsManager()
        
        self.tools = {
            "code": self.code,
            "files": self.files,
            "search": self.search,
            "system": self.system,
            "media": self.media,
            "storage": self.storage,
            "browser": self.browser,
            "image": self.image,
            "cache": self.cache,
            "benchmark": self.benchmark,
            "settings": self.settings,
        }

    def get(self, name: str):
        return self.tools.get(name)

    def list_tools(self) -> list:
        return list(self.tools.keys())

    def get_all(self) -> dict:
        return self.tools
