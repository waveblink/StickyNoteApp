"""Sticky note window widget."""

import re
from typing import Optional
from uuid import UUID
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QTextEdit, QMenu, QVBoxLayout,
    QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtGui import (
    QAction,
    QTextCursor,
    QTextListFormat,
    QColor,
    QFont,
    QTextCharFormat,
)

from ..models.base import Note
from ..services.reminder_service import ReminderService


class StickyWindow(QWidget):
    """Individual sticky note window."""
    
    contentChanged = Signal()
    deleteRequested = Signal()
    reminderRequested = Signal(str)
    
    def __init__(self, note: Note, content: str, parent=None):
        super().__init__(parent)
        self.note = note
        self._last_content = content
        self._save_timer = QTimer()
        self._save_timer.timeout.connect(self._save_content)
        self._save_timer.setSingleShot(True)
        
        self._init_ui(content)
    
    def _init_ui(self, content: str):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Text editor
        self.editor = QTextEdit()
        self.editor.setHtml(content)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._show_context_menu)
        
        # Enable checkbox parsing
        self.editor.textChanged.connect(self._parse_checkboxes)
        
        layout.addWidget(self.editor)
        
        # Window settings
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Apply shadow effect for neon theme
        self._apply_shadow()
        
        # Set initial size
        self.resize(300, 400)
    
    def _apply_shadow(self):
        """Apply drop shadow effect."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(5, 5)
        self.setGraphicsEffect(shadow)
    
    def _on_text_changed(self):
        """Handle text change with debouncing."""
        self._save_timer.stop()
        self._save_timer.start(1000)  # Save after 1 second of inactivity
    
    def _save_content(self):
        """Emit signal to save content."""
        current_content = self.editor.toHtml()
        if current_content != self._last_content:
            self._last_content = current_content
            self.contentChanged.emit()
    
    def _parse_checkboxes(self):
        """Parse markdown checkboxes and convert to widgets."""
        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        
        # Find checkbox patterns
        checkbox_pattern = re.compile(r'^(\s*)(- \[([ xX])\])\s*(.*)$', re.MULTILINE)
        
        for match in checkbox_pattern.finditer(text):
            indent = match.group(1)
            checked = match.group(3).lower() == 'x'
            content = match.group(4)
            
            # Move cursor to match position
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
            
            # Create list format
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.ListSquare)
            list_format.setIndent(len(indent) // 4 + 1)
            
            # Apply format
            cursor.createList(list_format)
    
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
        
        # Pin/Unpin
        pin_action = QAction("Unpin" if self.note.pinned else "Pin", self)
        pin_action.triggered.connect(self._toggle_pin)
        menu.addAction(pin_action)
        
        # Set reminder
        reminder_action = QAction("Set Reminder...", self)
        reminder_action.triggered.connect(self._set_reminder)
        menu.addAction(reminder_action)
        
        menu.addSeparator()
        
        # Delete
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.deleteRequested.emit)
        menu.addAction(delete_action)
        
        menu.exec(self.editor.mapToGlobal(pos))
    
    def _toggle_pin(self):
        """Toggle pin status."""
        self.note.pinned = not self.note.pinned
        
        # Update window flags
        flags = self.windowFlags()
        if self.note.pinned:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        self.show()
        self.contentChanged.emit()
    
    def _set_reminder(self):
        """Set reminder for note."""
        # In real implementation, show dialog to get reminder time
        # For now, emit signal
        self.reminderRequested.emit(self.note.id)

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
    
    def get_content(self) -> str:
        """Get current content as HTML."""
        return self.editor.toHtml()
    
    def setWindowTitle(self, title: str):
        """Update note title."""
        super().setWindowTitle(title)
        self.note.title = title