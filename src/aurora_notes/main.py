"""Application entry point."""

import sys
import time
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPalette, QColor

from .models.base import init_db
from .crypto.encryption import encryption_service
from .ui.main_window import MainWindow


def show_splash():
    """Show splash screen."""
    splash = QSplashScreen()
    splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
    
    # Create simple splash pixmap
    pixmap = QPixmap(400, 300)
    pixmap.fill(QColor("#FFF8E7"))
    
    splash.setPixmap(pixmap)
    splash.showMessage(
        "Aurora Notes\nLoading...",
        Qt.AlignCenter,
        QColor("#3E2723")
    )
    
    return splash


def main():
    """Main application entry point."""
    # Record start time for performance tracking
    start_time = time.time()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Aurora Notes")
    app.setOrganizationName("Aurora")
    
    # Show splash screen
    splash = show_splash()
    splash.show()
    app.processEvents()
    
    try:
        # Initialize database
        init_db()
        
        # Initialize encryption
        if not encryption_service.initialize():
            print("Failed to initialize encryption")
            return 1
        
        # Create main window
        window = MainWindow()
        
        # Hide splash and show main window after 100ms
        def show_main():
            window.show()
            splash.finish(window)
            
            # Log startup time
            elapsed = (time.time() - start_time) * 1000
            print(f"Cold start time: {elapsed:.0f}ms")
        
        QTimer.singleShot(100, show_main)
        
        # Run application
        result = app.exec()
        
        # Cleanup
        encryption_service.clear_key()
        
        return result
        
    except Exception as e:
        print(f"Fatal error: {e}")
        splash.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())