"""
Status Badge Widget
Displays status indicators with colors.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from ui.styles import (
    STATUS_SUCCESS, STATUS_WARNING, STATUS_ERROR, STATUS_INFO,
    HTB_GREEN, HTB_TEXT_DIM
)


class StatusBadge(QLabel):
    """
    Status badge with color-coded background.
    """
    
    STYLES = {
        "success": (STATUS_SUCCESS, "#ffffff"),
        "warning": (STATUS_WARNING, "#000000"),
        "error": (STATUS_ERROR, "#ffffff"),
        "info": (STATUS_INFO, "#ffffff"),
        "htb": (HTB_GREEN, "#000000"),
        "neutral": (HTB_TEXT_DIM, "#ffffff"),
    }
    
    def __init__(self, text: str, style: str = "neutral", parent=None):
        super().__init__(text, parent)
        self.setStatus(text, style)
    
    def setStatus(self, text: str, style: str = "neutral"):
        """Update the badge status."""
        self.setText(text)
        
        bg_color, text_color = self.STYLES.get(style, self.STYLES["neutral"])
        
        self.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 11px;
        """)
        
        self.setAlignment(Qt.AlignCenter)
        self.adjustSize()


class DifficultyBadge(QLabel):
    """
    Difficulty badge with appropriate colors.
    """
    
    COLORS = {
        "easy": "#9fef00",
        "medium": "#ffaf00",
        "hard": "#ff3e3e",
        "insane": "#7d3c98",
    }
    
    def __init__(self, difficulty: str, parent=None):
        super().__init__(difficulty, parent)
        self.setDifficulty(difficulty)
    
    def setDifficulty(self, difficulty: str):
        """Update the difficulty badge."""
        self.setText(difficulty)
        
        color = self.COLORS.get(difficulty.lower(), "#ffffff")
        
        self.setStyleSheet(f"""
            background-color: {color}20;
            color: {color};
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 11px;
        """)
        
        self.setAlignment(Qt.AlignCenter)
        self.adjustSize()


class OSBadge(QLabel):
    """
    Operating system badge with icon.
    """
    
    ICONS = {
        "linux": "🐧",
        "windows": "🪟",
        "freebsd": "😈",
        "android": "🤖",
        "other": "💻",
    }
    
    def __init__(self, os_name: str, parent=None):
        super().__init__(parent)
        self.setOS(os_name)
    
    def setOS(self, os_name: str):
        """Update the OS badge."""
        os_lower = os_name.lower()
        icon = self.ICONS.get(os_lower, self.ICONS["other"])
        
        self.setText(f"{icon} {os_name}")
        
        self.setStyleSheet(f"""
            background-color: #21262d;
            color: #e6edf3;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
        """)
        
        self.setAlignment(Qt.AlignCenter)
        self.adjustSize()
