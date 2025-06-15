"""Application dialogs."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QKeySequenceEdit, QDialogButtonBox
)

from ..services.hotkey_service import HotkeyService
from ..services.theme_service import ThemeService


class HotkeyDialog(QDialog):
    """Hotkey configuration dialog."""
    
    def __init__(self, hotkey_service: HotkeyService, parent=None):
        super().__init__(parent)
        self.hotkey_service = hotkey_service
        
        self.setWindowTitle("Configure Hotkey")
        self.setModal(True)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Instructions
        label = QLabel("Press the key combination for global new note:")
        layout.addWidget(label)
        
        # Key sequence editor
        self.key_edit = QKeySequenceEdit()
        self.key_edit.setKeySequence("Ctrl+Alt+Shift+N")
        layout.addWidget(self.key_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save_hotkey)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _save_hotkey(self):
        """Save hotkey configuration."""
        sequence = self.key_edit.keySequence().toString()
        if sequence:
            # Convert to format expected by hotkey service
            hotkey = sequence.lower().replace(" ", "")
            self.hotkey_service.register_hotkey(
                hotkey,
                lambda: None  # Callback handled by signal
            )
        
        self.accept()


class ThemeDialog(QDialog):
    """Theme selection dialog."""
    
    def __init__(self, theme_service: ThemeService, parent=None):
        super().__init__(parent)
        self.theme_service = theme_service
        
        self.setWindowTitle("Select Theme")
        self.setModal(True)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Theme selector
        label = QLabel("Choose a theme:")
        layout.addWidget(label)
        
        self.theme_combo = QComboBox()
        themes = self.theme_service.get_available_themes()
        for theme in themes:
            self.theme_combo.addItem(theme.replace("-", " ").title(), theme)
        
        # Set current theme
        current_index = self.theme_combo.findData(self.theme_service.current_theme)
        if current_index >= 0:
            self.theme_combo.setCurrentIndex(current_index)
        
        self.theme_combo.currentIndexChanged.connect(self._preview_theme)
        layout.addWidget(self.theme_combo)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self._restore_theme)
        layout.addWidget(buttons)
        
        self._original_theme = self.theme_service.current_theme
    
    def _preview_theme(self, index):
        """Preview selected theme."""
        theme = self.theme_combo.itemData(index)
        if theme:
            self.theme_service.apply_theme(theme)
    
    def _restore_theme(self):
        """Restore original theme on cancel."""
        self.theme_service.apply_theme(self._original_theme)
        self.reject()