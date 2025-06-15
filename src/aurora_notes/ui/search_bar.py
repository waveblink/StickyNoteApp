"""Search bar widget with debouncing."""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QLineEdit


class SearchBar(QLineEdit):
    """Search input with debounced signal."""
    
    searchRequested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setPlaceholderText("Search notes...")
        self.setClearButtonEnabled(True)
        
        # Debounce timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._emit_search)
        self._timer.setSingleShot(True)
        
        # Connect text change
        self.textChanged.connect(self._on_text_changed)
    
    def _on_text_changed(self, text: str):
        """Handle text change with debouncing."""
        self._timer.stop()
        if text:
            self._timer.start(300)  # 300ms debounce
        else:
            self.searchRequested.emit("")  # Clear search immediately
    
    def _emit_search(self):
        """Emit search signal."""
        self.searchRequested.emit(self.text())