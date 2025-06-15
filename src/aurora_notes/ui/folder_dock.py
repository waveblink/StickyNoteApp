"""Folder tree dock widget."""

from typing import Optional
from uuid import UUID
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget, QTreeView, QMenu,
    QVBoxLayout, QWidget, QPushButton, QInputDialog,
    QMessageBox
)
from PySide6.QtGui import QAction, QStandardItemModel, QStandardItem

from ..services.folder_service import FolderService


class FolderDock(QDockWidget):
    """Dockable folder tree widget."""
    
    folderSelected = Signal(object)  # Optional[UUID]
    
    def __init__(self, folder_service: FolderService, parent=None):
        super().__init__("Folders", parent)
        self.folder_service = folder_service
        self.current_folder_id: Optional[UUID] = None
        
        self._init_ui()
        self._load_folders()
    
    def _init_ui(self):
        """Initialize UI."""
        # Main widget
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add folder button
        self.add_button = QPushButton("+ New Folder")
        self.add_button.clicked.connect(self._add_folder)
        layout.addWidget(self.add_button)
        
        # Tree view
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        # Model
        self.model = QStandardItemModel()
        self.tree.setModel(self.model)
        
        # Selection
        self.tree.selectionModel().currentChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.tree)
        self.setWidget(widget)
        
        # Dock settings
        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )
    
    def _load_folders(self):
        """Load folders from service."""
        self.model.clear()
        
        # Add "All Notes" item
        all_notes = QStandardItem("All Notes")
        all_notes.setData(None, Qt.UserRole)
        self.model.appendRow(all_notes)
        
        # Add folders
        folders = self.folder_service.get_all_folders()
        for folder in folders:
            item = QStandardItem(folder.name)
            item.setData(folder.id, Qt.UserRole)
            self.model.appendRow(item)
        
        # Select "All Notes" by default
        self.tree.setCurrentIndex(self.model.index(0, 0))
    
    def _add_folder(self):
        """Add new folder."""
        name, ok = QInputDialog.getText(
            self,
            "New Folder",
            "Folder name:"
        )
        
        if ok and name:
            folder = self.folder_service.create_folder(name)
            if folder:
                item = QStandardItem(folder.name)
                item.setData(folder.id, Qt.UserRole)
                self.model.appendRow(item)
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "A folder with this name already exists."
                )
    
    def _show_context_menu(self, pos):
        """Show context menu for folders."""
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        
        item = self.model.itemFromIndex(index)
        folder_id = item.data(Qt.UserRole)
        
        if folder_id is None:  # "All Notes" item
            return
        
        menu = QMenu(self)
        
        # Rename
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_folder(item, folder_id))
        menu.addAction(rename_action)
        
        # Delete
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_folder(item, folder_id))
        menu.addAction(delete_action)
        
        menu.exec(self.tree.mapToGlobal(pos))
    
    def _rename_folder(self, item: QStandardItem, folder_id: UUID):
        """Rename folder."""
        old_name = item.text()
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Folder",
            "New name:",
            text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            folder = self.folder_service.rename_folder(folder_id, new_name)
            if folder:
                item.setText(new_name)
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "A folder with this name already exists."
                )
    
    def _delete_folder(self, item: QStandardItem, folder_id: UUID):
        """Delete folder."""
        reply = QMessageBox.question(
            self,
            "Delete Folder",
            "Delete this folder? Notes will be moved to 'All Notes'.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.folder_service.delete_folder(folder_id):
                self.model.removeRow(item.row())
    
    def _on_selection_changed(self, current, previous):
        """Handle folder selection."""
        if current.isValid():
            item = self.model.itemFromIndex(current)
            self.current_folder_id = item.data(Qt.UserRole)
            self.folderSelected.emit(self.current_folder_id)