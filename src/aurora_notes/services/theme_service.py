"""Theme management service."""

import os
from typing import Dict, List
from PySide6.QtCore import QObject, Signal, QFile, QTextStream
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


class ThemeService(QObject):
    """Handles theme loading and switching."""
    
    themeChanged = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = "cozy-parchment"
        self.themes: Dict[str, str] = {}
        self._load_themes()
    
    def _load_themes(self):
        """Load QSS files from assets."""
        # Try to load from files first
        theme_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "assets", "qss"
        )
        
        theme_files = {
            "cozy-parchment": "cozy-parchment.qss",
            "dark": "dark.qss",
            "neon": "neon.qss",
            "hogwarts": "hogwarts.qss",
        }
        
        for theme_name, filename in theme_files.items():
            file_path = os.path.join(theme_dir, filename)
            
            if os.path.exists(file_path):
                # Load from file
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.themes[theme_name] = f.read()
            else:
                # Fall back to embedded themes
                if theme_name == "cozy-parchment":
                    self.themes[theme_name] = self._get_cozy_parchment_qss()
                elif theme_name == "dark":
                    self.themes[theme_name] = self._get_dark_qss()
                elif theme_name == "neon":
                    self.themes[theme_name] = self._get_neon_qss()
                elif theme_name == "hogwarts":
                    self.themes[theme_name] = self._get_hogwarts_qss()
    
    def _get_cozy_parchment_qss(self) -> str:
        """Fallback cozy parchment theme."""
        return """
        QMainWindow {
            background-color: #FFF8E7;
        }
        
        QTextEdit {
            background-color: rgba(255, 248, 231, 0.9);
            border: 2px solid #8B4513;
            border-radius: 8px;
            padding: 10px;
            font-family: "EB Garamond", "Palatino", serif;
            font-size: 14px;
            color: #3E2723;
        }
        
        QPushButton {
            background-color: #D2691E;
            border: 2px solid #8B4513;
            border-radius: 6px;
            padding: 8px 16px;
            color: white;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #CD853F;
        }
        """
    
    def _get_dark_qss(self) -> str:
        """Fallback dark theme."""
        return """
        QMainWindow {
            background-color: #1A1A1A;
            color: #E0E0E0;
        }
        
        QTextEdit {
            background-color: #2D2D2D;
            border: 1px solid #444;
            border-radius: 6px;
            padding: 10px;
            font-family: "Inter", "Segoe UI", sans-serif;
            font-size: 13px;
            color: #E0E0E0;
        }
        
        QPushButton {
            background-color: #0D7377;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            color: white;
        }
        
        QPushButton:hover {
            background-color: #14FFEC;
            color: #1A1A1A;
        }
        """
    
    def _get_neon_qss(self) -> str:
        """Fallback cyberpunk neon theme."""
        return """
        QMainWindow {
            background-color: #0A0A0A;
            color: #00FFFF;
        }
        
        QTextEdit {
            background-color: #1A0033;
            border: 2px solid #FF00FF;
            border-radius: 8px;
            padding: 10px;
            font-family: "JetBrains Mono", "Consolas", monospace;
            font-size: 12px;
            color: #00FFFF;
        }
        
        QPushButton {
            background-color: #FF00FF;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            color: #0A0A0A;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #00FFFF;
        }
        """

    def _get_hogwarts_qss(self) -> str:
        """Fallback Hogwarts parchment theme."""
        return """
        QMainWindow {
            background-color: #F5ECD9;
        }

        QTextEdit {
            background-color: rgba(245, 236, 217, 0.92);
            border: 2px solid #7F461B;
            border-radius: 8px;
            padding: 12px;
            font-family: 'EB Garamond', 'Times New Roman', serif;
            font-size: 14px;
            color: #3D2817;
        }

        QPushButton {
            background-color: #7F461B;
            border: 2px solid #3D2817;
            border-radius: 6px;
            padding: 8px 16px;
            color: white;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #C89131;
        }
        """
    
    def apply_theme(self, theme_name: str):
        """Apply theme to application."""
        if theme_name not in self.themes:
            return
        
        self.current_theme = theme_name
        qss = self.themes[theme_name]
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)
            
            # Update palette for system integration
            palette = app.palette()
            if theme_name == "dark":
                palette.setColor(QPalette.Window, QColor(26, 26, 26))
                palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
            elif theme_name == "neon":
                palette.setColor(QPalette.Window, QColor(10, 10, 10))
                palette.setColor(QPalette.WindowText, QColor(0, 255, 255))
            else:  # parchment-based themes
                palette.setColor(QPalette.Window, QColor(245, 236, 217))
                palette.setColor(QPalette.WindowText, QColor(61, 40, 23))
            
            app.setPalette(palette)
        
        self.themeChanged.emit(theme_name)
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(self.themes.keys())