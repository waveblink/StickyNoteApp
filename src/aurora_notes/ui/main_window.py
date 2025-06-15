# File: src/aurora_notes/ui/main_window.py
"""Main application window - minimal manager for desktop sticky notes."""

import sys
from typing import Dict, List, Optional
from uuid import UUID
from PySide6.QtCore import Qt, QTimer, Slot, QPoint, QSettings
from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QMenuBar, QMenu, QSystemTrayIcon,
    QVBoxLayout, QWidget, QListWidget, QListWidgetItem,
    QMessageBox, QApplication
)
from PySide6.QtGui import QIcon, QCloseEvent, QAction
from PySide6.QtGui import QIcon, QCloseEvent

from .desktop_sticky import DesktopStickyNote
from .folder_dock import FolderDock
from .search_bar import SearchBar
from .dialogs import HotkeyDialog, ThemeDialog
from ..services.note_service import NoteService
from ..services.folder_service import FolderService
from ..services.theme_service import ThemeService
from ..services.hotkey_service import HotkeyService
from ..services.reminder_service import ReminderService


class MainWindow(QMainWindow):
    """Main window - acts as a note manager, not container."""
    
    def __init__(self):
        super().__init__()
        
        # Services
        self.note_service = NoteService()
        self.folder_service = FolderService()
        self.theme_service = ThemeService()
        self.hotkey_service = HotkeyService()
        self.reminder_service = ReminderService()
        
        # Track sticky windows
        self.sticky_windows: Dict[UUID, DesktopStickyNote] = {}
        self.settings = QSettings("Aurora", "AuroraNotes")
        
        # Initialize UI
        self._init_ui()
        self._setup_services()
        
        # Start minimized to tray
        self.hide()
        
        # Show first-run message
        if not self.settings.value("shown_welcome", False, bool):
            QTimer.singleShot(500, self._show_welcome_message)
            self.settings.setValue("shown_welcome", True)
        
        # Load notes after UI is ready
        QTimer.singleShot(100, self._load_notes)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Aurora Notes Manager")
        self.setGeometry(100, 100, 400, 600)
        
        # Central widget - note list
        central = QWidget()
        layout = QVBoxLayout(central)
        
        # Search bar
        self.search_bar = SearchBar()
        self.search_bar.searchRequested.connect(self._perform_search)
        layout.addWidget(self.search_bar)
        
        # Note list
        self.note_list = QListWidget()
        self.note_list.itemDoubleClicked.connect(self._show_note)
        layout.addWidget(self.note_list)
        
        self.setCentralWidget(central)
        
        # Toolbar
        self._create_toolbar()
        
        # Menu bar
        self._create_menu_bar()
        
        # Folder dock
        self.folder_dock = FolderDock(self.folder_service)
        self.folder_dock.folderSelected.connect(self._on_folder_selected)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.folder_dock)
        
        # System tray
        self._create_tray_icon()
    
    def _create_toolbar(self):
        """Create main toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # New note action
        new_action = QAction("New Note", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._create_new_note)
        toolbar.addAction(new_action)
        
        toolbar.addSeparator()
        
        # Show all notes
        show_all_action = QAction("Show All Notes", self)
        show_all_action.triggered.connect(self._show_all_notes)
        toolbar.addAction(show_all_action)
        
        # Hide all notes
        hide_all_action = QAction("Hide All Notes", self)
        hide_all_action.triggered.connect(self._hide_all_notes)
        toolbar.addAction(hide_all_action)
        
        toolbar.addSeparator()
        
        # Theme button
        theme_action = QAction("Theme", self)
        theme_action.triggered.connect(self._show_theme_dialog)
        toolbar.addAction(theme_action)
        
        # Settings button
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings)
        toolbar.addAction(settings_action)
    
    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Note", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._create_new_note)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Add theme submenu
        theme_menu = view_menu.addMenu("Theme")
        for theme in self.theme_service.get_available_themes():
            action = QAction(theme.replace("-", " ").title(), self)
            action.triggered.connect(lambda checked, t=theme: self._apply_theme(t))
            theme_menu.addAction(action)
    
    def _create_tray_icon(self):
        """Create system tray icon."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setToolTip("Aurora Notes")
            
            # Tray menu
            tray_menu = QMenu()
            
            show_manager_action = QAction("Show Manager", self)
            show_manager_action.triggered.connect(self.show)
            tray_menu.addAction(show_manager_action)
            
            new_action = QAction("New Note", self)
            new_action.triggered.connect(self._create_new_note)
            tray_menu.addAction(new_action)
            
            tray_menu.addSeparator()
            
            show_all_action = QAction("Show All Notes", self)
            show_all_action.triggered.connect(self._show_all_notes)
            tray_menu.addAction(show_all_action)
            
            hide_all_action = QAction("Hide All Notes", self)
            hide_all_action.triggered.connect(self._hide_all_notes)
            tray_menu.addAction(hide_all_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self._quit_app)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._on_tray_activated)
            self.tray_icon.show()
    
    def _setup_services(self):
        """Setup service connections."""
        # Hotkey service
        default_hotkey = "ctrl+alt+shift+n"
        self.hotkey_service.hotkeyPressed.connect(self._on_hotkey_pressed)
        self.hotkey_service.register_hotkey(default_hotkey, self._on_hotkey_pressed)
        
        # Reminder service
        self.reminder_service.reminderTriggered.connect(self._show_reminder)
        self.reminder_service.reschedule_all_reminders(self.note_service)
        
        # Apply default theme
        self.theme_service.apply_theme("cozy-parchment")
    
    def _load_notes(self):
        """Load all notes."""
        notes = self.note_service.get_all_notes()
        
        for note, body in notes:
            # Add to list
            item = QListWidgetItem(note.title)
            item.setData(Qt.UserRole, note.id)
            self.note_list.addItem(item)
            
            # Create sticky window if it was visible
            if self.settings.value(f"note_visible_{note.id}", True, bool):
                self._create_sticky_window(note, body, show=True)
    
    def _create_sticky_window(self, note, body: str, show: bool = True) -> DesktopStickyNote:
        """Create desktop sticky window for note."""
        # Check if already exists
        if note.id in self.sticky_windows:
            sticky = self.sticky_windows[note.id]
            if show:
                sticky.show()
                sticky.raise_()
                sticky.activateWindow()
            return sticky
        
        # Create new sticky
        sticky = DesktopStickyNote(note, body, self.theme_service)
        sticky.contentChanged.connect(lambda: self._on_note_changed(sticky))
        sticky.deleteRequested.connect(lambda: self._delete_note(note.id))
        sticky.closed.connect(lambda: self._on_sticky_closed(note.id))
        
        # Restore position if saved
        pos = self.settings.value(f"note_pos_{note.id}")
        if pos:
            sticky.move(pos)
        else:
            # Cascade new windows
            offset = len(self.sticky_windows) * 30
            sticky.move(100 + offset, 100 + offset)
        
        # Restore size
        size = self.settings.value(f"note_size_{note.id}")
        if size:
            sticky.resize(size)
        
        self.sticky_windows[note.id] = sticky
        
        if show:
            sticky.show()
        
        return sticky
    
    @Slot()
    def _create_new_note(self):
        """Create new note."""
        note = self.note_service.create_note(
            title="New Note",
            body="",
            folder_id=self.folder_dock.current_folder_id
        )
        
        # Add to list
        item = QListWidgetItem(note.title)
        item.setData(Qt.UserRole, note.id)
        self.note_list.addItem(item)
        
        # Create and show sticky
        sticky = self._create_sticky_window(note, "", show=True)
        sticky.focus_title()
    
    @Slot(QListWidgetItem)
    def _show_note(self, item: QListWidgetItem):
        """Show note from list."""
        note_id = item.data(Qt.UserRole)
        note_data = self.note_service.get_note(note_id)
        if note_data:
            note, body = note_data
            self._create_sticky_window(note, body, show=True)
    
    def _show_all_notes(self):
        """Show all sticky windows."""
        for sticky in self.sticky_windows.values():
            sticky.show()
            sticky.raise_()
    
    def _hide_all_notes(self):
        """Hide all sticky windows."""
        for sticky in self.sticky_windows.values():
            sticky.hide()
    
    def _on_note_changed(self, sticky: DesktopStickyNote):
        """Handle note content change."""
        note = sticky.note
        self.note_service.update_note(
            note.id,
            title=sticky.get_title(),
            body=sticky.get_content()
        )
        
        # Update list
        for i in range(self.note_list.count()):
            item = self.note_list.item(i)
            if item.data(Qt.UserRole) == note.id:
                item.setText(sticky.get_title())
                break
    
    def _on_sticky_closed(self, note_id: UUID):
        """Handle sticky window closed."""
        self.settings.setValue(f"note_visible_{note_id}", False)
    
    def _delete_note(self, note_id: UUID):
        """Delete note."""
        reply = QMessageBox.question(
            self,
            "Delete Note",
            "Are you sure you want to delete this note?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.note_service.delete_note(note_id):
                # Remove from list
                for i in range(self.note_list.count()):
                    item = self.note_list.item(i)
                    if item.data(Qt.UserRole) == note_id:
                        self.note_list.takeItem(i)
                        break
                
                # Close sticky if open
                sticky = self.sticky_windows.pop(note_id, None)
                if sticky:
                    sticky.close()
                
                # Clear saved settings
                self.settings.remove(f"note_pos_{note_id}")
                self.settings.remove(f"note_size_{note_id}")
                self.settings.remove(f"note_visible_{note_id}")
    
    @Slot(UUID)
    def _on_folder_selected(self, folder_id: Optional[UUID]):
        """Handle folder selection."""
        # Refresh list
        self.note_list.clear()
        notes = self.note_service.get_all_notes(folder_id)
        
        for note, _ in notes:
            item = QListWidgetItem(note.title)
            item.setData(Qt.UserRole, note.id)
            self.note_list.addItem(item)
    
    @Slot(str)
    def _perform_search(self, query: str):
        """Perform fuzzy search."""
        if not query:
            # Show all notes
            self._on_folder_selected(self.folder_dock.current_folder_id)
            return
        
        # Search and update list
        self.note_list.clear()
        results = self.note_service.search_notes(query)
        
        for note, _, score in results:
            item = QListWidgetItem(f"{note.title} ({score:.0f}%)")
            item.setData(Qt.UserRole, note.id)
            self.note_list.addItem(item)
    
    def _apply_theme(self, theme_name: str):
        """Apply theme to all windows."""
        self.theme_service.apply_theme(theme_name)
        
        # Update all sticky windows
        for sticky in self.sticky_windows.values():
            sticky.update_theme()
    
    @Slot()
    def _on_hotkey_pressed(self):
        """Handle global hotkey."""
        self._create_new_note()
    
    @Slot(UUID, str, str)
    def _show_reminder(self, note_id: UUID, title: str, body_preview: str):
        """Show reminder notification."""
        if self.tray_icon:
            self.tray_icon.showMessage(
                f"Reminder: {title}",
                body_preview,
                QSystemTrayIcon.Information,
                10000
            )
        
        # Show the note
        note_data = self.note_service.get_note(note_id)
        if note_data:
            note, body = note_data
            self._create_sticky_window(note, body, show=True)
    
    @Slot()
    def _show_theme_dialog(self):
        """Show theme selection dialog."""
        dialog = ThemeDialog(self.theme_service, self)
        dialog.exec()
    
    @Slot()
    def _show_settings(self):
        """Show settings dialog."""
        dialog = HotkeyDialog(self.hotkey_service, self)
        dialog.exec()
    
    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def _quit_app(self):
        """Quit application completely."""
        # Save sticky positions
        for note_id, sticky in self.sticky_windows.items():
            self.settings.setValue(f"note_pos_{note_id}", sticky.pos())
            self.settings.setValue(f"note_size_{note_id}", sticky.size())
            self.settings.setValue(f"note_visible_{note_id}", sticky.isVisible())
        
        # Cleanup
        self.reminder_service.shutdown()
        self.hotkey_service.stop_listening()
        
        # Quit
        QApplication.quit()
    
    def closeEvent(self, event: QCloseEvent):
        """Handle close event - hide to tray."""
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
            
            # Show message on first minimize
            if not self.settings.value("shown_tray_message", False, bool):
                self.tray_icon.showMessage(
                    "Aurora Notes",
                    "Application minimized to tray",
                    QSystemTrayIcon.Information,
                    3000
                )
                self.settings.setValue("shown_tray_message", True)
    
    def _show_welcome_message(self):
        """Show welcome message for first-time users."""
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Welcome to Aurora Notes!",
                "Notes appear as floating desktop windows. Right-click the tray icon or press Ctrl+Alt+Shift+N to create a new note.",
                QSystemTrayIcon.Information,
                8000
            )