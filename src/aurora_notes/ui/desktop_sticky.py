"""Desktop sticky note widget - individual floating windows."""

import re
from typing import Optional
from uuid import UUID
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QMenu,
    QGraphicsDropShadowEffect, QSizeGrip
)

from .sticky_widget import StickyHeader
from PySide6.QtGui import (
    QColor,
    QMouseEvent,
    QPalette,
    QTextCursor,
    QAction,
    QFont,
    QTextCharFormat,
    QTextListFormat,
)

from ..models.base import Note


class DesktopStickyNote(QWidget):
    """Individual desktop sticky note window."""
    
    contentChanged = Signal()
    deleteRequested = Signal()
    closed = Signal()
    
    # Available note themes
    NOTE_THEMES = {
        "classic-yellow": "Classic Yellow",
        "modern-flat": "Modern Flat",
        "parchment": "Parchment",
        "neon": "Neon Glow",
        "dark": "Dark Mode",
        "ocean-blue": "Ocean Blue",
        "pastel-pink": "Pastel Pink",
        "forest-green": "Forest Green",
        "high-contrast": "High Contrast",
        "retro-8bit": "Retro 8-bit",
        "harry-potter": "Harry Potter",
    }
    
    def __init__(self, note: Note, content: str, theme_service, parent=None):
        super().__init__(parent)
        self.note = note
        self.theme_service = theme_service
        self._last_content = content
        self._last_title = note.title
        self._moving = False
        self._move_pos = QPoint()
        
        # Note theme (separate from app theme)
        self._note_theme = "classic-yellow"
        
        # Save timer
        self._save_timer = QTimer()
        self._save_timer.timeout.connect(self._save_content)
        self._save_timer.setSingleShot(True)
        
        self._init_ui(content)
        self.update_theme()
    
    def _init_ui(self, content: str):
        """Initialize UI."""
        # Window flags for desktop sticky
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # Prevents taskbar entry
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container
        self.container = QWidget()
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.container)
        
        # Container layout
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        
        # Title bar - store as self.title_bar for dragging
        self.title_bar = QWidget()
        self.title_bar.setMinimumHeight(36)
        self.title_bar.setMaximumHeight(60)  # Allow expansion for long titles
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(8, 4, 8, 4)
        
        # Title edit - now a QTextEdit for multi-line support
        self.title_edit = QTextEdit()
        self.title_edit.setPlainText(self.note.title)
        self.title_edit.setFrameShape(QTextEdit.NoFrame)
        self.title_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.title_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.title_edit.textChanged.connect(self._on_text_changed)
        self.title_edit.setMaximumHeight(40)
        title_layout.addWidget(self.title_edit)
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(3)
        
        # Theme button
        self.theme_button = QPushButton("🎨")
        self.theme_button.setFixedSize(32, 32)
        self.theme_button.clicked.connect(self._show_theme_menu)
        self.theme_button.setToolTip("Change note color")
        button_layout.addWidget(self.theme_button)
        
        # Pin button
        self.pin_button = QPushButton()
        self.pin_button.setFixedSize(32, 32)
        self._update_pin_icon()

        # Connect header buttons
        self.pin_button.clicked.connect(self._toggle_pin)
        self.pin_button.setToolTip("Pin/Unpin to top")
        button_layout.addWidget(self.pin_button)
        
        # Close button
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(32, 32)
        self.close_button.clicked.connect(self.hide)
        self.close_button.setToolTip("Hide note")
        button_layout.addWidget(self.close_button)
        
        title_layout.addWidget(button_container)
        for btn in (self.theme_button, self.pin_button, self.close_button):
            btn.setStyleSheet("padding:0px; margin:0px;")
        
        layout.addWidget(self.title_bar)
        
        # Content editor
        self.editor = QTextEdit()
        self.editor.setHtml(content)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._show_context_menu)
        self.editor.setFrameShape(QTextEdit.NoFrame)
        layout.addWidget(self.editor)
        
        # Size grip for resizing - positioned at bottom right
        grip_container = QWidget()
        grip_layout = QHBoxLayout(grip_container)
        grip_layout.setContentsMargins(0, 4, 4, 4)  # Added 4px top padding
        grip_layout.addStretch()
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(16, 16)
        grip_layout.addWidget(self.size_grip)
        
        layout.addWidget(grip_container)
        
        # Set initial size
        self.resize(280, 320)
        
        # Enable dragging on title bar
        self.title_bar.mousePressEvent = self._start_move
        self.title_bar.mouseMoveEvent = self._do_move
        self.title_bar.mouseReleaseEvent = self._end_move
        
        # Apply shadow
        self._apply_shadow()
    
    def _update_pin_icon(self):
        """Update pin button icon based on pinned state."""
        if self.note.pinned:
            self.pin_button.setText("📌")  # Filled pin for pinned
        else:
            self.pin_button.setText("📍")  # Outlined pin for unpinned
    
    def _apply_shadow(self):
        """Apply default shadow effect."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(2, 2)
        self.container.setGraphicsEffect(shadow)
    
    def update_theme(self, note_theme: Optional[str] = None):
        """Update styling based on selected note theme."""
        if note_theme:
            self._note_theme = note_theme
        
        theme = self._note_theme
        
        if theme == "classic-yellow":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #FFEB3B;
                    border: 1px solid #F9A825;
                    border-radius: 2px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #333333;
                    font-family: "Segoe UI", "Arial", sans-serif;
                }
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.1);
                    border-radius: 3px;
                    color: #333333;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.1);
                }
                QTextEdit#title {
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self._apply_paper_shadow()
            
        elif theme == "modern-flat":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #424242;
                    font-family: "Inter", "Segoe UI", sans-serif;
                }
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                    color: #9E9E9E;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.05);
                    color: #424242;
                }
                QTextEdit#title {
                    font-weight: 600;
                    font-size: 15px;
                    color: #212121;
                }
            """)
            self._apply_flat_shadow()
            
        elif theme == "parchment":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #F4E4C1;
                    background-image: url(assets/images/parchment-texture.png);
                    border: 2px solid #8B6F47;
                    border-radius: 4px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #3E2723;
                    font-family: "EB Garamond", "Georgia", serif;
                }
                QPushButton {
                    background: rgba(139, 111, 71, 0.2);
                    border: 1px solid #8B6F47;
                    border-radius: 3px;
                    color: #5D4037;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: rgba(139, 111, 71, 0.3);
                }
                QTextEdit#title {
                    font-weight: bold;
                    font-size: 16px;
                    font-style: italic;
                }
            """)
            self._apply_paper_shadow()
            
        elif theme == "neon":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #1A0033;
                    border: 2px solid #FF00FF;
                    border-radius: 0px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #00FFFF;
                    font-family: "JetBrains Mono", "Consolas", monospace;
                    text-shadow: 0 0 5px currentColor;
                }
                QPushButton {
                    background: transparent;
                    border: 1px solid #FF00FF;
                    color: #FF00FF;
                    font-size: 14px;
                    font-family: "JetBrains Mono", monospace;
                }
                QPushButton:hover {
                    color: #00FFFF;
                    border-color: #00FFFF;
                    text-shadow: 0 0 10px currentColor;
                }
                QTextEdit#title {
                    font-weight: bold;
                    font-size: 14px;
                    text-transform: uppercase;
                    color: #00FFFF;
                }
            """)
            self._apply_neon_glow()

        elif theme == "ocean-blue":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #E0F7FA;
                    background-image: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E0F7FA, stop:1 #B3E5FC);
                    border: 1px solid #0288D1;
                    border-radius: 6px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #01579B;
                    font-family: "Segoe UI", "Arial", sans-serif;
                }
                QPushButton {
                    background: rgba(2, 136, 209, 0.1);
                    border: 1px solid rgba(2, 136, 209, 0.2);
                    border-radius: 4px;
                    color: #01579B;
                }
                QPushButton:hover {
                    background: rgba(2, 136, 209, 0.2);
                }
                QTextEdit#title {
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self._apply_flat_shadow()

        elif theme == "pastel-pink":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #FFE4E9;
                    border: 1px solid #F8BBD0;
                    border-radius: 6px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #880E4F;
                    font-family: "Segoe UI", "Arial", sans-serif;
                }
                QPushButton {
                    background: rgba(248, 187, 208, 0.3);
                    border: 1px solid rgba(248, 187, 208, 0.5);
                    border-radius: 4px;
                    color: #880E4F;
                }
                QPushButton:hover {
                    background: rgba(248, 187, 208, 0.5);
                }
                QTextEdit#title {
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self._apply_paper_shadow()

        elif theme == "forest-green":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #E8F5E9;
                    border: 1px solid #2E7D32;
                    border-radius: 6px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #1B5E20;
                    font-family: "Georgia", serif;
                }
                QPushButton {
                    background: rgba(46, 125, 50, 0.2);
                    border: 1px solid rgba(46, 125, 50, 0.4);
                    border-radius: 4px;
                    color: #1B5E20;
                }
                QPushButton:hover {
                    background: rgba(46, 125, 50, 0.3);
                }
                QTextEdit#title {
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self._apply_paper_shadow()

        elif theme == "high-contrast":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #FFFFFF;
                    border: 2px solid #000000;
                    border-radius: 0px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #000000;
                    font-family: "Segoe UI", "Arial", sans-serif;
                }
                QPushButton {
                    background: #000000;
                    border: none;
                    border-radius: 2px;
                    color: #FFFFFF;
                }
                QPushButton:hover {
                    background: #333333;
                }
                QTextEdit#title {
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self._apply_flat_shadow()

        elif theme == "retro-8bit":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #F0F0F0;
                    border: 2px solid #000000;
                    border-radius: 0px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #000000;
                    font-family: "Courier New", monospace;
                    font-size: 12px;
                }
                QPushButton {
                    background: #000000;
                    color: #FFFFFF;
                    border: 2px solid #000000;
                    border-radius: 0px;
                    font-family: "Courier New", monospace;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #FFFFFF;
                    color: #000000;
                }
                QTextEdit#title {
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            self._apply_flat_shadow()

        elif theme == "harry-potter":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #F6E5B4;
                    border: 2px solid #7F461B;
                    border-radius: 4px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #3D2817;
                    font-family: "Georgia", serif;
                    font-style: italic;
                }
                QPushButton {
                    background: rgba(127, 70, 27, 0.2);
                    border: 1px solid #7F461B;
                    border-radius: 3px;
                    color: #3D2817;
                }
                QPushButton:hover {
                    background: rgba(127, 70, 27, 0.3);
                }
                QTextEdit#title {
                    font-weight: bold;
                    font-size: 16px;
                    font-style: italic;
                }
            """)
            self._apply_paper_shadow()

        elif theme == "dark":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #212121;
                    border: 1px solid #424242;
                    border-radius: 6px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #E0E0E0;
                    font-family: "Inter", "Segoe UI", sans-serif;
                }
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 3px;
                    color: #B0B0B0;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                    color: #FFFFFF;
                }
                QTextEdit#title {
                    font-weight: 600;
                    font-size: 15px;
                    color: #FFFFFF;
                }
            """)
            self._apply_flat_shadow()
        
        # Set object names for styling
        self.title_edit.setObjectName("title")
    
    def _apply_paper_shadow(self):
        """Apply paper-like shadow effect."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(2, 2)
        self.container.setGraphicsEffect(shadow)
    
    def _apply_flat_shadow(self):
        """Apply modern flat shadow effect."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
    
    def _apply_neon_glow(self):
        """Apply neon glow effect."""
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(255, 0, 255, 128))
        glow.setOffset(0, 0)
        self.container.setGraphicsEffect(glow)
    
    def _show_theme_menu(self):
        """Display menu to switch note theme."""
        menu = QMenu(self)
        for theme_id, theme_name in self.NOTE_THEMES.items():
            action = QAction(theme_name, menu)
            action.setCheckable(True)
            action.setChecked(self._note_theme == theme_id)
            action.triggered.connect(lambda checked, t=theme_id: self.update_theme(t))
            menu.addAction(action)
        # Show menu below the theme button
        menu.exec(self.theme_button.mapToGlobal(QPoint(0, self.theme_button.height())))
    
    def _start_move(self, event: QMouseEvent):
        """Start window drag."""
        if event.button() == Qt.LeftButton:
            self._moving = True
            self._move_pos = event.globalPos() - self.pos()
    
    def _do_move(self, event: QMouseEvent):
        """Handle window drag."""
        if self._moving and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._move_pos)
    
    def _end_move(self, event: QMouseEvent):
        """End window drag."""
        self._moving = False
    
    def _on_text_changed(self):
        """Handle text change with debouncing."""
        self._save_timer.stop()
        self._save_timer.start(1000)
    
    def _save_content(self):
        """Emit signal to save content."""
        current_content = self.editor.toHtml()
        current_title = self.title_edit.toPlainText()
        
        if current_content != self._last_content or current_title != self._last_title:
            self._last_content = current_content
            self._last_title = current_title
            self.note.title = current_title
            self.contentChanged.emit()
    
    def _toggle_pin(self):
        """Toggle pin status."""
        self.note.pinned = not self.note.pinned
        
        # Update button icon
        self._update_pin_icon()
        
        # Update window flags
        flags = self.windowFlags()
        if self.note.pinned:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        self.show()
        self.contentChanged.emit()

    def _toggle_bold(self):
        """Toggle bold formatting for the current selection."""
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        if cursor.charFormat().fontWeight() == QFont.Bold:
            fmt.setFontWeight(QFont.Normal)
        else:
            fmt.setFontWeight(QFont.Bold)
        cursor.mergeCharFormat(fmt)

    def _toggle_italic(self):
        """Toggle italic formatting for the current selection."""
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(fmt)

    def _highlight_selection(self):
        """Highlight or clear highlight on the current selection."""
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        current_bg = cursor.charFormat().background().color()
        if current_bg == QColor("yellow"):
            fmt.clearBackground()
        else:
            fmt.setBackground(QColor("yellow"))
        cursor.mergeCharFormat(fmt)

    def _set_font(self, family: str):
        """Set font family for the current selection."""
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontFamily(family)
        cursor.mergeCharFormat(fmt)

    def _set_font_size(self, size: int):
        """Set font size for the current selection."""
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        cursor.mergeCharFormat(fmt)

    def _insert_bullet_list(self):
        """Insert a bullet list at the current cursor position."""
        cursor = self.editor.textCursor()
        cursor.insertList(QTextListFormat.ListDisc)
    
    def _show_context_menu(self, pos):
        """Show context menu."""
        menu = QMenu(self)

        # Formatting submenu
        format_menu = menu.addMenu("Format")

        bold_action = QAction("Bold", self)
        bold_action.setCheckable(True)
        bold_action.setChecked(self.editor.fontWeight() == QFont.Bold)
        bold_action.triggered.connect(self._toggle_bold)
        format_menu.addAction(bold_action)

        italic_action = QAction("Italic", self)
        italic_action.setCheckable(True)
        italic_action.setChecked(self.editor.fontItalic())
        italic_action.triggered.connect(self._toggle_italic)
        format_menu.addAction(italic_action)

        highlight_action = QAction("Highlight", self)
        highlight_action.triggered.connect(self._highlight_selection)
        format_menu.addAction(highlight_action)

        bullet_action = QAction("Bullet List", self)
        bullet_action.triggered.connect(self._insert_bullet_list)
        format_menu.addAction(bullet_action)

        font_menu = format_menu.addMenu("Font")
        for family in ["Arial", "Times New Roman", "Courier New"]:
            action = QAction(family, self)
            action.triggered.connect(lambda checked, f=family: self._set_font(f))
            font_menu.addAction(action)

        size_menu = format_menu.addMenu("Font Size")
        for size in [10, 12, 14, 16, 18]:
            action = QAction(str(size), self)
            action.triggered.connect(lambda checked, s=size: self._set_font_size(s))
            size_menu.addAction(action)

        menu.addSeparator()
        
        # Note theme submenu
        theme_menu = menu.addMenu("Note Color")
        theme_names = {
            "classic-yellow": "Classic Yellow",
            "modern-flat": "Modern Flat",
            "parchment": "Parchment",
            "neon": "Neon Glow",
            "dark": "Dark Mode",
            "ocean-blue": "Ocean Blue",
            "pastel-pink": "Pastel Pink",
            "forest-green": "Forest Green",
            "high-contrast": "High Contrast",
            "retro-8bit": "Retro 8-bit",
            "harry-potter": "Harry Potter",
        }
        
        for theme_id, theme_name in theme_names.items():
            action = QAction(theme_name, theme_menu)
            action.setCheckable(True)
            action.setChecked(self._note_theme == theme_id)
            action.triggered.connect(lambda checked, t=theme_id: self.update_theme(t))
            theme_menu.addAction(action)
        
        menu.addSeparator()
        
        # Always on top toggle
        pin_action = QAction("Always on Top", self)
        pin_action.setCheckable(True)
        pin_action.setChecked(self.note.pinned)
        pin_action.triggered.connect(self._toggle_pin)
        menu.addAction(pin_action)
        
        menu.addSeparator()
        
        # Delete
        delete_action = QAction("Delete Note", self)
        delete_action.triggered.connect(self.deleteRequested.emit)
        menu.addAction(delete_action)
        
        menu.exec(self.editor.mapToGlobal(pos))
    
    def get_content(self) -> str:
        """Get current content as HTML."""
        return self.editor.toHtml()
    
    def get_title(self) -> str:
        """Get current title."""
        return self.title_edit.toPlainText()
    
    def focus_title(self):
        """Focus and select title for editing."""
        self.title_edit.setFocus()
        self.title_edit.selectAll()
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        self.closed.emit()
    
    def closeEvent(self, event):
        """Handle close event."""
        self.closed.emit()
        super().closeEvent(event)