"""Text-to-Speech engine supporting multiple backends."""
import os
import subprocess
from typing import Optional

class TTSEngine:
    """Offline Text-to-Speech with multiple backends."""

    def __init__(self):
        self.backend = self._detect_backend()

    def _detect_backend(self) -> str:
        if self._find_binary("piper"):
            return "piper"
        if self._find_binary("espeak") or self._find_binary("espeak-ng"):
            return "espeak"
        try:
            import pyttsx3
            return "pyttsx3"
        except ImportError:
            pass
        return "none"

    def _find_binary(self, name: str) -> Optional[str]:
        candidates = [
            f"/usr/bin/{name}",
            f"/usr/local/bin/{name}",
            os.path.expanduser(f"~/.local/bin/{name}"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def speak(self, text: str) -> bool:
        """Speak text using available backend."""
        if self.backend == "piper":
            return self._speak_piper(text)
        elif self.backend == "espeak":
            return self._speak_espeak(text)
        elif self.backend == "pyttsx3":
            return self._speak_pyttsx3(text)
        else:
            # Fallback: print to terminal
            print(f"🔊 {text}")
            return False

    def _speak_piper(self, text: str) -> bool:
        try:
            voice_model = "/usr/share/sid/voices/en_US-lessac-medium.onnx"
            subprocess.run(
                ["piper", "--model", voice_model, "--output-raw"],
                input=text.encode(),
                capture_output=True,
                timeout=30
            )
            return True
        except Exception as e:
            print(f"[TTS] Piper error: {e}")
            return False

    def _speak_espeak(self, text: str) -> bool:
        try:
            subprocess.run(
                ["espeak-ng", "-v", "en-us", "-s", "150", text],
                capture_output=True, timeout=30
            )
            return True
        except Exception as e:
            print(f"[TTS] espeak error: {e}")
            return False

    def _speak_pyttsx3(self, text: str) -> bool:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception as e:
            print(f"[TTS] pyttsx3 error: {e}")
            return False

    def is_available(self) -> bool:
        return self.backend != "none"
