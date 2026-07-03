"""Speech-to-Text engine supporting multiple backends."""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

class STTEngine:
    """Offline Speech-to-Text using whisper.cpp or Python fallback."""

    def __init__(self):
        self.backend = self._detect_backend()
        self._stream_active = False
        self._audio_buffer = []

    def _detect_backend(self) -> str:
        """Detect available STT backend."""
        # Check for whisper.cpp
        if self._find_binary("whisper-cli"):
            return "whisper_cpp"
        # Check for whisper Python
        try:
            import whisper
            return "whisper_py"
        except ImportError:
            pass
        # Check for speechrecognition
        try:
            import speech_recognition
            return "speech_recognition"
        except ImportError:
            pass
        return "none"

    def _find_binary(self, name: str) -> Optional[str]:
        candidates = [
            f"/usr/bin/{name}",
            f"/usr/local/bin/{name}",
            f"{os.path.expanduser('~')}/.local/bin/{name}",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        if self.backend == "whisper_cpp":
            return self._transcribe_whisper_cpp(audio_path)
        elif self.backend == "whisper_py":
            return self._transcribe_whisper_py(audio_path)
        elif self.backend == "speech_recognition":
            return self._transcribe_speech_recognition(audio_path)
        return "[STT unavailable - install whisper.cpp]"

    def _transcribe_whisper_cpp(self, audio_path: str) -> str:
        try:
            model_path = "/usr/share/sid/models/ggml-tiny.bin"
            if not os.path.exists(model_path):
                # Download tiny model
                self._download_tiny_model(model_path)

            result = subprocess.run(
                ["whisper-cli", "-m", model_path, "-f", audio_path],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip() or result.stderr.strip()
        except Exception as e:
            return f"[STT error: {e}]"

    def _transcribe_whisper_py(self, audio_path: str) -> str:
        try:
            import whisper
            model = whisper.load_model("tiny")
            result = model.transcribe(audio_path)
            return result["text"].strip()
        except Exception as e:
            return f"[STT error: {e}]"

    def _transcribe_speech_recognition(self, audio_path: str) -> str:
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
            return recognizer.recognize_sphinx(audio)
        except Exception as e:
            return f"[STT error: {e}]"

    def _download_tiny_model(self, path: str):
        import urllib.request
        url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print(f"[SID] Downloading whisper tiny model...")
        urllib.request.urlretrieve(url, path)

    def start_stream(self) -> bool:
        """Start voice stream for real-time STT."""
        try:
            import pyaudio
            self._stream_active = True
            self._audio_buffer = []
            return True
        except ImportError:
            print("[SID] pyaudio not available for streaming")
            return False

    def stop_stream(self):
        self._stream_active = False

    def is_available(self) -> bool:
        return self.backend != "none"
