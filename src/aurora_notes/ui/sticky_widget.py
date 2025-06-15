"""Custom sticky note header widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QWidget


class StickyHeader(QWidget):
    """Title bar with pin, minimize and close buttons."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Restrict header height to 40 px on all platforms
        self.setMaximumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Layout with consistent padding to avoid DPI cropping
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)  # 6 px horizontal padding
        layout.setSpacing(6)

        # Pin, minimise and close buttons in that order
        self.pin_button = QPushButton()
        self.minimize_button = QPushButton()
        self.close_button = QPushButton()

        for btn in (self.pin_button, self.minimize_button, self.close_button):
            btn.setObjectName("headerButton")  # For stylesheet targeting
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)

        # Spacer to push buttons to the right if header expands
        layout.addStretch()

        self.setLayout(layout)
