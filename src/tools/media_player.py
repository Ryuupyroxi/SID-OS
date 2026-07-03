"""SID Media Player - CLI media playback with AI control."""
import os
import subprocess
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Callable

class MediaPlayer:
    """CLI media player supporting audio, video (audio-only on TTY), and playlists."""

    SUPPORTED_AUDIO = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma', '.opus']
    SUPPORTED_VIDEO = ['.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv']
    PLAYLIST_FILES = ['.m3u', '.m3u8', '.pls']

    def __init__(self, ai=None):
        self.ai = ai
        self.current = None
        self.queue = []
        self.history = []
        self._playing = False
        self._paused = False
        self._volume = 80
        self._process = None
        self.backend = self._detect_backend()

    def _detect_backend(self) -> str:
        """Detect available media backend."""
        for cmd in ['mpv', 'ffplay', 'mplayer', 'aplay', 'paplay', 'sox']:
            if self._find_binary(cmd):
                return cmd
        return "none"

    def _find_binary(self, name: str) -> Optional[str]:
        import shutil
        return shutil.which(name)

    def play(self, path: str) -> Dict:
        """Play a media file."""
        p = Path(path).expanduser()
        if not p.exists():
            return {"error": f"File not found: {path}"}

        ext = p.suffix.lower()
        if ext not in self.SUPPORTED_AUDIO + self.SUPPORTED_VIDEO:
            return {"error": f"Unsupported format: {ext}"}

        # Stop current playback
        self.stop()

        self.current = str(p)
        self._playing = True
        self._paused = False
        self.history.append(str(p))

        try:
            if self.backend == 'mpv':
                self._process = subprocess.Popen(
                    ['mpv', '--vo=null', '--no-video' if ext in self.SUPPORTED_AUDIO else '',
                     f'--volume={self._volume}', '--quiet', str(p)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            elif self.backend == 'ffplay':
                self._process = subprocess.Popen(
                    ['ffplay', '-nodisp', '-autoexit', '-volume', str(self._volume),
                     '-loglevel', 'quiet', str(p)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            elif self.backend == 'mplayer':
                self._process = subprocess.Popen(
                    ['mplayer', '-really-quiet', '-novideo', 
                     f'-volume={self._volume}', str(p)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            else:
                return {"error": "No media backend found. Install mpv, ffplay, or mplayer."}

            return {"status": "playing", "file": str(p), "backend": self.backend}
        except Exception as e:
            self._playing = False
            return {"error": str(e)}

    def play_url(self, url: str) -> Dict:
        """Stream media from URL."""
        if self.backend == 'none':
            return {"error": "No media backend"}
        
        self.stop()
        self._playing = True
        
        try:
            if self.backend == 'mpv':
                self._process = subprocess.Popen(
                    ['mpv', '--vo=null', f'--volume={self._volume}', '--quiet', url],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            else:
                return {"error": f"{self.backend} doesn't support URL streaming reliably"}
            
            return {"status": "streaming", "url": url}
        except Exception as e:
            return {"error": str(e)}

    def stop(self):
        """Stop playback."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=3)
            except:
                self._process.kill()
            self._process = None
        self._playing = False
        self._paused = False

    def pause(self):
        """Toggle pause."""
        if not self._process:
            return
        if self._paused:
            if self.backend == 'mpv':
                subprocess.run(['pkill', '-STOP', 'mpv'], capture_output=True)
            self._paused = False
        else:
            if self.backend == 'mpv':
                subprocess.run(['pkill', '-CONT', 'mpv'], capture_output=True)
            self._paused = True

    def volume(self, level: Optional[int] = None) -> int:
        """Get/set volume (0-100)."""
        if level is not None:
            self._volume = max(0, min(100, level))
            if self.backend == 'mpv' and self._process:
                subprocess.run(['mpv', '--volume='+str(self._volume)], capture_output=True)
        return self._volume

    def queue_add(self, path: str):
        """Add file to playback queue."""
        self.queue.append(path)

    def queue_clear(self):
        self.queue.clear()

    def queue_next(self):
        """Play next in queue."""
        if self.queue:
            next_file = self.queue.pop(0)
            return self.play(next_file)
        return {"status": "queue_empty"}

    def playlist_load(self, path: str) -> List[str]:
        """Load a playlist file."""
        p = Path(path).expanduser()
        if not p.exists():
            return []
        
        files = []
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                files.append(line)
        
        self.queue = files
        return files

    def scan_directory(self, path: str = ".") -> List[Dict]:
        """Scan directory for media files."""
        media = []
        p = Path(path).expanduser()
        for f in p.iterdir():
            if f.suffix.lower() in self.SUPPORTED_AUDIO + self.SUPPORTED_VIDEO:
                media.append({
                    "name": f.name,
                    "path": str(f),
                    "type": "audio" if f.suffix.lower() in self.SUPPORTED_AUDIO else "video",
                    "size": f.stat().st_size,
                })
        return sorted(media, key=lambda x: x['name'])

    def status(self) -> Dict:
        """Get current playback status."""
        return {
            "playing": self._playing,
            "paused": self._paused,
            "current": self.current,
            "queue_length": len(self.queue),
            "volume": self._volume,
            "backend": self.backend,
            "recent": self.history[-5:] if self.history else []
        }

    def ai_control(self, command: str) -> str:
        """Control media player via AI natural language."""
        if not self.ai:
            return "[SID] AI not available for media control"
        
        prompt = (
            f"Media player command: '{command}'\n"
            f"Current state: {json.dumps(self.status())}\n"
            f"Convert this to a media action. Return ONLY one of: "
            f"play:<file>, play_url:<url>, pause, stop, volume:<0-100>, "
            f"queue:<file>, next, list:<dir>, scan:<dir>"
        )
        result = self.ai.process(prompt)
        action = result.get("response", "").strip()
        
        if action.startswith("play:"):
            return str(self.play(action[5:]))
        elif action == "pause":
            self.pause()
            return "Toggled pause"
        elif action == "stop":
            self.stop()
            return "Stopped"
        elif action.startswith("volume:"):
            return f"Volume: {self.volume(int(action[7:]))}"
        elif action.startswith("scan:"):
            files = self.scan_directory(action[5:])
            return f"Found {len(files)} media files"
        else:
            return f"Command interpreted as: {action}"
