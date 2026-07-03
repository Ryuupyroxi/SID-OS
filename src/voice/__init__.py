"""SID Voice System - Offline speech-to-text and text-to-speech."""
from .stt.engine import STTEngine
from .tts.engine import TTSEngine
from .vad.detector import VADDetector

class VoiceSystem:
    """Integrated voice control system with offline capability."""

    def __init__(self):
        self.stt = STTEngine()
        self.tts = TTSEngine()
        self.vad = VADDetector()
        self._listening = False

    def start_listening(self):
        """Start continuous voice input."""
        self._listening = True
        return self.stt.start_stream()

    def stop_listening(self):
        """Stop voice input."""
        self._listening = False
        return self.stt.stop_stream()

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        return self.stt.transcribe(audio_path)

    def speak(self, text: str):
        """Convert text to speech."""
        return self.tts.speak(text)

    def is_available(self) -> bool:
        return self.stt.is_available() or self.tts.is_available()
