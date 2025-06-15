"""Main application window."""

import sys
from typing import Dict, Optional
from uuid import UUID
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QMainWindow, QMdiArea, QToolBar, QMenuBar,
    QMenu, QDockWidget, QSystemTrayIcon, QLineEdit,
    QVBoxLayout, QWidget, QSplashScreen, QMessageBox,
    QAction
)
from PySide6.QtGui import QIcon, QPixmap, QCloseEvent

from .sticky_window import StickyWindow
from .folder_dock import FolderDock
from .search_bar import SearchBar
from .dialogs import HotkeyDialog, ThemeDialog
from ..services.note_service import NoteService
from ..services.folder_service import FolderService
from ..services.theme_service import ThemeService
from ..services.hotkey_service import HotkeyService
from ..services.reminder_service import ReminderService


class MainWindow(QMainWindow):
    """Main application window with MDI area."""
    
    def __init__(self):
        super().__init__()
        
        # Services
        self.note_service = NoteService()
        self.folder_service = FolderService()
        self.theme_service = ThemeService()
        self.hotkey_service = HotkeyService()
        self.reminder_service = ReminderService()
        
        # UI state
        self.sticky_windows: Dict[UUID, StickyWindow] = {}
        self.tray_icon: Optional[QSystemTrayIcon] = None
        
        # Initialize UI
        self._init_ui()
        self._setup_services()
        
        # Load notes after UI is ready
        QTimer.singleShot(100, self._load_notes)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Aurora Notes")
        self.setGeometry(100, 100, 1200, 800)
        
        # MDI Area
        self.mdi_area = QMdiArea()
        self.mdi_area.setViewMode(QMdiArea.TabbedView)
        self.mdi_area.setTabsClosable(True)
        self.mdi_area.setTabsMovable(True)
        self.setCentralWidget(self.mdi_area)
        
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
        
        # Search bar
        self.search_bar = SearchBar()
        self.search_bar.searchRequested.connect(self._perform_search)
        toolbar.addWidget(self.search_bar)
        
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
        
        import_action = QAction("Import...", self)
        import_action.triggered.connect(self._import_notes)
        file_menu.addAction(import_action)
        
        export_action = QAction("Export...", self)
        export_action.triggered.connect(self._export_notes)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Add theme submenu
        theme_menu = view_menu.addMenu("Theme")
        for theme in self.theme_service.get_available_themes():
            action = QAction(theme.title(), self)
            action.triggered.connect(lambda checked, t=theme: self.theme_service.apply_theme(t))
            theme_menu.addAction(action)
    
    def _create_tray_icon(self):
        """Create system tray icon."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setToolTip("Aurora Notes")
            
            # Tray menu
            tray_menu = QMenu()
            
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            new_action = QAction("New Note", self)
            new_action.triggered.connect(self._create_new_note)
            tray_menu.addAction(new_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.close)
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
        """Load all notes into MDI area."""
        notes = self.note_service.get_all_notes()
        
        for note, body in notes:
            self._create_sticky_window(note, body)
    
    def _create_sticky_window(self, note, body: str) -> StickyWindow:
        """Create sticky window for note."""
        sticky = StickyWindow(note, body)
        sticky.contentChanged.connect(lambda: self._on_note_changed(sticky))
        sticky.deleteRequested.connect(lambda: self._delete_note(note.id))
        
        sub_window = self.mdi_area.addSubWindow(sticky)
        sub_window.setWindowTitle(note.title)
        
        self.sticky_windows[note.id] = sticky
        
        return sticky
    
    @Slot()
    def _create_new_note(self):
        """Create new note."""
        note = self.note_service.create_note(
            title="New Note",
            body="",
            folder_id=self.folder_dock.current_folder_id
        )
        
        sticky = self._create_sticky_window(note, "")
        sticky.show()
        sticky.setFocus()
    
    @Slot(UUID)
    def _on_folder_selected(self, folder_id: Optional[UUID]):
        """Handle folder selection."""
        # Filter visible notes
        for note_id, sticky in self.sticky_windows.items():
            note, _ = self.note_service.get_note(note_id)
            if note:
                visible = folder_id is None or note.folder_id == folder_id
                sticky.parent().setVisible(visible)
    
    @Slot(str)
    def _perform_search(self, query: str):
        """Perform fuzzy search."""
        if not query:
            # Show all notes
            for sticky in self.sticky_windows.values():
                sticky.parent().setVisible(True)
            return
        
        # Search and filter
        results = self.note_service.search_notes(query)
        matched_ids = {note.id for note, _, _ in results}
        
        for note_id, sticky in self.sticky_windows.items():
            sticky.parent().setVisible(note_id in matched_ids)
    
    def _on_note_changed(self, sticky: StickyWindow):
        """Handle note content change."""
        note = sticky.note
        self.note_service.update_note(
            note.id,
            title=sticky.windowTitle(),
            body=sticky.get_content()
        )
    
    @Slot()
    def _on_hotkey_pressed(self):
        """Handle global hotkey."""
        self.show()
        self.raise_()
        self.activateWindow()
        self._create_new_note()
    
    @Slot(UUID, str, str)
    def _show_reminder(self, note_id: UUID, title: str, body_preview: str):
        """Show reminder notification."""
        if self.tray_icon:
            self.tray_icon.showMessage(
                f"Reminder: {title}",
                body_preview,
                QSystemTrayIcon.Information,
                10000  # 10 seconds
            )
    
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
    
    def _import_notes(self):
        """Import notes from file."""
        # Implementation for import
        pass
    
    def _export_notes(self):
        """Export notes to file."""
        # Implementation for export
        pass
    
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
                sticky = self.sticky_windows.pop(note_id, None)
                if sticky:
                    sticky.parent().close()
    
    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def closeEvent(self, event: QCloseEvent):
        """Handle close event."""
        # Minimize to tray instead of closing
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            # Cleanup
            self.reminder_service.shutdown()
            self.hotkey_service.stop_listening()
            event.accept()