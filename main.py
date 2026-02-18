#!/usr/bin/env python3
"""
HTB Desktop Client
A modern GUI application for interacting with HackTheBox API.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from config import config
from ui.main_window import MainWindow
from utils.debug import debug_log


def main():
    """Main entry point."""
    debug_log("APP", "Starting HTB Desktop Client...")
    debug_log("APP", f"Debug mode: {config.debug}")
    debug_log("APP", f"API configured: {config.is_configured()}")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("HTB Client")
    app.setApplicationVersion("1.0.0")
    
    # Set default font - try Inter, fallback to system fonts
    font = QFont()
    font.setFamilies(["Inter", "Segoe UI", "SF Pro Display", "Roboto"])
    font.setPointSize(10)
    font.setWeight(QFont.Weight.Normal)
    app.setFont(font)
    
    # High DPI scaling is enabled by default in Qt6
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    debug_log("APP", "Application started successfully")
    
    # Check if token is configured
    if not config.is_configured():
        debug_log("APP", "No API token configured - showing settings")
        window.top_nav.page_changed.emit("settings")
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
