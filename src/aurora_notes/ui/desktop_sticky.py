# File: src/aurora_notes/ui/desktop_sticky.py
"""Desktop sticky note widget - individual floating windows."""

import re
from typing import Optional
from uuid import UUID
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QMenu,
    QGraphicsDropShadowEffect, QSizeGrip
)
from PySide6.QtGui import QAction, QColor, QMouseEvent, QPalette

from ..models.base import Note


class DesktopStickyNote(QWidget):
    """Individual desktop sticky note window."""
    
    contentChanged = Signal()
    deleteRequested = Signal()
    closed = Signal()
    
    def __init__(self, note: Note, content: str, theme_service, parent=None):
        super().__init__(parent)
        self.note = note
        self.theme_service = theme_service
        self._last_content = content
        self._last_title = note.title
        self._moving = False
        self._move_pos = QPoint()
        
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
        
        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 4, 8, 4)
        
        # Title edit
        self.title_edit = QLineEdit(self.note.title)
        self.title_edit.setFrame(False)
        self.title_edit.textChanged.connect(self._on_text_changed)
        title_layout.addWidget(self.title_edit)
        
        # Buttons
        self.pin_button = QPushButton("📌" if self.note.pinned else "📍")
        self.pin_button.setFixedSize(20, 20)
        self.pin_button.clicked.connect(self._toggle_pin)
        self.pin_button.setToolTip("Pin/Unpin")
        title_layout.addWidget(self.pin_button)
        
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.hide)
        self.close_button.setToolTip("Hide")
        title_layout.addWidget(self.close_button)
        
        layout.addWidget(title_bar)
        
        # Content editor
        self.editor = QTextEdit()
        self.editor.setHtml(content)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._show_context_menu)
        self.editor.setFrameShape(QTextEdit.NoFrame)
        layout.addWidget(self.editor)
        
        # Size grip for resizing
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(16, 16)
        
        # Position size grip at bottom right
        layout.addWidget(self.size_grip, 0, Qt.AlignRight)
        
        # Set initial size
        self.resize(250, 300)
        
        # Enable dragging
        title_bar.mousePressEvent = self._start_move
        title_bar.mouseMoveEvent = self._do_move
        title_bar.mouseReleaseEvent = self._end_move
        
        # Apply shadow
        self._apply_shadow()
    
    def update_theme(self):
        """Update styling based on current theme."""
        theme = self.theme_service.current_theme
        
        if theme == "cozy-parchment":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: rgba(255, 248, 231, 0.95);
                    border: 2px solid #8B4513;
                    border-radius: 6px;
                }
                QLineEdit {
                    background: transparent;
                    border: none;
                    color: #3E2723;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #8B4513;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: rgba(139, 69, 19, 0.1);
                    border-radius: 2px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #3E2723;
                    font-family: "EB Garamond", "Palatino", serif;
                    font-size: 13px;
                    padding: 8px;
                }
            """)
            
        elif theme == "dark":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: rgba(45, 45, 45, 0.95);
                    border: 1px solid #555555;
                    border-radius: 6px;
                }
                QLineEdit {
                    background: transparent;
                    border: none;
                    color: #E0E0E0;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #0D7377;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: rgba(13, 115, 119, 0.2);
                    border-radius: 2px;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #E0E0E0;
                    font-family: "Inter", "Segoe UI", sans-serif;
                    font-size: 13px;
                    padding: 8px;
                }
            """)
            
        elif theme == "neon":
            self.container.setStyleSheet("""
                QWidget {
                    background-color: rgba(26, 0, 51, 0.95);
                    border: 2px solid #FF00FF;
                    border-radius: 6px;
                }
                QLineEdit {
                    background: transparent;
                    border: none;
                    color: #00FFFF;
                    font-weight: bold;
                    font-size: 14px;
                    text-transform: uppercase;
                }
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #FF00FF;
                    font-size: 16px;
                }
                QPushButton:hover {
                    color: #00FFFF;
                    text-shadow: 0 0 10px #00FFFF;
                }
                QTextEdit {
                    background: transparent;
                    border: none;
                    color: #00FFFF;
                    font-family: "JetBrains Mono", "Consolas", monospace;
                    font-size: 12px;
                    padding: 8px;
                }
            """)
            self._apply_neon_glow()
    
    def _apply_shadow(self):
        """Apply drop shadow effect."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(3, 3)
        self.container.setGraphicsEffect(shadow)
    
    def _apply_neon_glow(self):
        """Apply neon glow effect."""
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(255, 0, 255, 128))
        glow.setOffset(0, 0)
        self.container.setGraphicsEffect(glow)
    
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
        current_title = self.title_edit.text()
        
        if current_content != self._last_content or current_title != self._last_title:
            self._last_content = current_content
            self._last_title = current_title
            self.note.title = current_title
            self.contentChanged.emit()
    
    def _toggle_pin(self):
        """Toggle pin status."""
        self.note.pinned = not self.note.pinned
        
        # Update button
        self.pin_button.setText("📌" if self.note.pinned else "📍")
        
        # Update window flags
        flags = self.windowFlags()
        if self.note.pinned:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        self.show()
        self.contentChanged.emit()
    
    def _show_context_menu(self, pos):
        """Show context menu."""
        menu = QMenu(self)
        
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
        return self.title_edit.text()
    
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