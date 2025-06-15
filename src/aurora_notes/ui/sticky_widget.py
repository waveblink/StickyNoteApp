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

        # Layout with padding so icons are never clipped at high DPI
        layout = QHBoxLayout(self)
        # Vertical margins give the buttons breathing room and keep them
        # centred when scaled on high-DPI displays.
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)

        # Spacer placed before buttons so they stay aligned right
        layout.addStretch()

        # Pin, minimise and close buttons in that order
        self.pin_button = QPushButton()
        self.minimize_button = QPushButton()
        self.close_button = QPushButton()

        for btn in (self.pin_button, self.minimize_button, self.close_button):
            btn.setObjectName("headerButton")  # For stylesheet targeting
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)

        self.setLayout(layout)
