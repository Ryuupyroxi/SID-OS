"""Voice Activity Detection for push-to-talk and wake word."""
import os
import struct
from typing import Optional

class VADDetector:
    """Simple Voice Activity Detection."""

    def __init__(self):
        self.backend = self._detect_backend()
        self._is_speaking = False

    def _detect_backend(self) -> str:
        try:
            import webrtcvad
            return "webrtc"
        except ImportError:
            pass
        return "energy"  # Simple energy-based fallback

    def is_speech(self, audio_frame: bytes) -> bool:
        """Detect if audio frame contains speech."""
        if self.backend == "webrtc":
            return self._detect_webrtc(audio_frame)
        return self._detect_energy(audio_frame)

    def _detect_webrtc(self, frame: bytes) -> bool:
        try:
            import webrtcvad
            vad = webrtcvad.Vad(2)  # Aggressiveness 0-3
            return vad.is_speech(frame, 16000)
except Exception:
            return self._detect_energy(frame)

    def _detect_energy(self, frame: bytes) -> bool:
        """Simple energy-based speech detection."""
        if len(frame) < 2:
            return False
        # Calculate RMS energy
        samples = struct.unpack_from(f"<{len(frame)//2}h", frame)
        energy = sum(abs(s) for s in samples) / len(samples)
        return energy > 500  # Threshold

    def process_stream(self, audio_stream, callback):
        """Process audio stream and call callback on speech detection."""
        while True:
            frame = audio_stream.read(320)  # 20ms @ 16kHz
            if self.is_speech(frame):
                if not self._is_speaking:
                    self._is_speaking = True
                    callback("speech_start")
            else:
                if self._is_speaking:
                    self._is_speaking = False
                    callback("speech_end")
