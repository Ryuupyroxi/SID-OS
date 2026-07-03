"""SID Voice Button - Small floating button for voice input."""
import os
import sys
import json
import threading
import subprocess
from pathlib import Path
from typing import Optional, Callable

class VoiceButton:
    """Floating voice input button in bottom-right corner."""

    def __init__(self, on_text: Optional[Callable] = None, config_path: str = "/etc/sid/ai.json"):
        self.on_text = on_text or self._default_handler
        self.config_path = Path(config_path)
        self._listening = False
        self._process = None

    def show(self):
        """Display voice button."""
        if self._has_display():
            self._show_tk()
        else:
            self._show_terminal()

    def _has_display(self) -> bool:
        return bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))

    def _show_tk(self):
        """Tkinter floating button."""
        try:
            import tkinter as tk
            
            self.root = tk.Tk()
            self.root.title("")
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            self.root.attributes('-alpha', 0.85)
            
            # Position bottom-right
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"44x44+{sw-60}+{sh-80}")
            self.root.configure(bg='#0a0a0a')

            def toggle():
                if self._listening:
                    self._stop()
                else:
                    self._start()

            self.btn = tk.Label(
                self.root, text='🎤', font=('Segoe UI', 18),
                bg='#1a1a1a', fg='#555', cursor='hand2'
            )
            self.btn.pack(fill='both', expand=True, padx=2, pady=2)
            self.btn.bind('<Button-1>', lambda e: toggle())
            
            # Hover effects
            self.btn.bind('<Enter>', lambda e: self.btn.configure(bg='#333', fg='#0f0'))
            self.btn.bind('<Leave>', lambda e: self.btn.configure(bg='#1a1a1a', 
                fg='#f55' if self._listening else '#555'))

            self.root.mainloop()
        except Exception as e:
            print(f"[VoiceBtn] Error: {e}")

    def _start(self):
        self._listening = True
        if self.btn:
            self.root.after(0, lambda: self.btn.configure(text='🔴', fg='#f55'))
        
        thread = threading.Thread(target=self._record_and_transcribe, daemon=True)
        thread.start()

    def _stop(self):
        self._listening = False
        if self.btn:
            self.root.after(0, lambda: self.btn.configure(text='🎤', fg='#555'))

    def _record_and_transcribe(self):
        """Record audio and transcribe."""
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        tmp.close()
        
        try:
            # Record using arecord (ALSA)
            subprocess.run([
                'arecord', '-f', 'S16_LE', '-r', '16000', '-c', '1',
                '-d', '5', tmp.name
            ], capture_output=True, timeout=10)
            
            # Transcribe using whisper
            result = subprocess.run(
                ['whisper-cli', '-m', '/usr/share/sid/models/ggml-tiny.bin',
                 '-f', tmp.name],
                capture_output=True, text=True, timeout=30
            )
            text = result.stdout.strip()
            
            if text and self.on_text:
                self.on_text(text)
        except:
            pass
        finally:
            os.unlink(tmp.name)
            self._stop()

    def _show_terminal(self):
        """Terminal-based voice prompt."""
        print("\033[33m[SID Voice] Press Enter to record 5 seconds of voice...\033[0m")
        input()
        self._record_and_transcribe()

    def _default_handler(self, text: str):
        print(f"\n\033[32m[You]:\033[0m {text}")
        return text

    def hide(self):
        if hasattr(self, 'root'):
            self.root.quit()
