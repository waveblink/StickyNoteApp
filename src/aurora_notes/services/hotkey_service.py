"""Global hotkey service with cross-platform support."""

import platform
import threading
from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal

if platform.system() == "Windows":
    import keyboard
else:
    from pynput import keyboard as pynput_keyboard


class HotkeyService(QObject):
    """Cross-platform global hotkey handler."""
    
    hotkeyPressed = Signal()
    
    def __init__(self):
        super().__init__()
        self.hotkey: Optional[str] = None
        self.listener_thread: Optional[threading.Thread] = None
        self.running = False
        self._callback: Optional[Callable] = None
    
    def register_hotkey(self, hotkey: str, callback: Callable):
        """Register global hotkey (e.g., 'ctrl+alt+shift+n')."""
        self.stop_listening()
        
        self.hotkey = hotkey
        self._callback = callback
        self.running = True
        
        self.listener_thread = threading.Thread(
            target=self._run_listener,
            daemon=True
        )
        self.listener_thread.start()
    
    def _run_listener(self):
        """Run hotkey listener in background thread."""
        if platform.system() == "Windows":
            self._run_windows_listener()
        else:
            self._run_pynput_listener()
    
    def _run_windows_listener(self):
        """Windows-specific hotkey listener."""
        try:
            keyboard.add_hotkey(self.hotkey, self._on_hotkey_pressed)
            keyboard.wait()
        except Exception as e:
            print(f"Hotkey error: {e}")
    
    def _run_pynput_listener(self):
        """macOS/Linux hotkey listener using pynput."""
        # Convert hotkey format for pynput
        parts = self.hotkey.lower().split('+')
        
        # Build key combination
        combo = set()
        for part in parts:
            if part == 'ctrl':
                combo.add(pynput_keyboard.Key.ctrl)
            elif part == 'alt':
                combo.add(pynput_keyboard.Key.alt)
            elif part == 'shift':
                combo.add(pynput_keyboard.Key.shift)
            elif part == 'cmd':
                combo.add(pynput_keyboard.Key.cmd)
            else:
                # Regular key
                combo.add(part)
        
        current_keys = set()
        
        def on_press(key):
            if self.running:
                try:
                    if hasattr(key, 'char') and key.char:
                        current_keys.add(key.char.lower())
                    else:
                        current_keys.add(key)
                    
                    if combo.issubset(current_keys):
                        self._on_hotkey_pressed()
                except AttributeError:
                    pass
        
        def on_release(key):
            try:
                if hasattr(key, 'char') and key.char:
                    current_keys.discard(key.char.lower())
                else:
                    current_keys.discard(key)
            except:
                pass
        
        with pynput_keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        ) as listener:
            listener.join()
    
    def _on_hotkey_pressed(self):
        """Handle hotkey press."""
        if self._callback:
            # Emit signal for Qt thread safety
            self.hotkeyPressed.emit()
    
    def stop_listening(self):
        """Stop hotkey listener."""
        self.running = False
        
        if platform.system() == "Windows" and self.hotkey:
            try:
                keyboard.remove_hotkey(self.hotkey)
            except:
                pass