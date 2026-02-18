"""
Modern Custom Widgets for HTB Client.
"""

from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame, QVBoxLayout, QHBoxLayout, 
    QGraphicsDropShadowEffect, QLineEdit
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QBrush, QPen

from ui.styles import (
    HTB_GREEN, HTB_GREEN_DIM, HTB_BG_CARD, HTB_BG_HOVER, HTB_BORDER,
    HTB_TEXT_MAIN, HTB_TEXT_SEC, HTB_TEXT_MUTED, HTB_BG_INPUT, HTB_BG_MAIN,
    FONT_FAMILY_MAIN, HTB_RED, HTB_CYAN, HTB_RED_DIM
)

import qtawesome as qta


class ModernButton(QPushButton):
    """
    A modern button with animated hover effects and custom styling.
    """
    def __init__(self, text="", icon_name=None, btn_type="primary", parent=None):
        super().__init__(text, parent)
        self.btn_type = btn_type
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        
        if icon_name:
            # All buttons now use neutral icons by default, color on hover handled by stylesheet? 
            # Actually stylesheet can't change icon color easily without qtawesome re-render.
            # We'll stick to a neutral color for all, maybe subtle variation.
            icon_color = HTB_TEXT_SEC
            
            self.setIcon(qta.icon(icon_name, color=icon_color))

        self._setup_style()

    def _setup_style(self):
        # Single uniform style for ALL buttons — minimalist, no colors
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {HTB_BG_HOVER};
                border: 1px solid {HTB_BORDER};
                border-radius: 6px;
                color: {HTB_TEXT_SEC};
                font-family: {FONT_FAMILY_MAIN};
                font-weight: 600;
                font-size: 13px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {HTB_BG_CARD};
                color: {HTB_TEXT_MAIN};
            }}
            QPushButton:pressed {{
                background-color: {HTB_BG_MAIN};
            }}
        """)


class ModernCard(QFrame):
    """
    A card container with subtle borders and shadow.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            ModernCard {{
                background-color: {HTB_BG_MAIN};
                border: 1px solid {HTB_BORDER};
                border-radius: 6px;
            }}
        """)
        # Optional: Add shadow if desired, but might affect performance on some updates
        # shadow = QGraphicsDropShadowEffect(self)
        # shadow.setBlurRadius(20)
        # shadow.setColor(QColor(0, 0, 0, 80))
        # shadow.setOffset(0, 4)
        # self.setGraphicsEffect(shadow)


class SimpleStatCard(ModernCard):
    """
    A specialized card for displaying a single statistic.
    Uses generic widget layout instead of fixed properties for flexibility.
    """
    def __init__(self, title, value, icon_name="fa5s.chart-bar", color=HTB_GREEN, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        # Header with Icon
        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(qta.icon(icon_name, color=HTB_TEXT_SEC).pixmap(16, 16))
        icon.setFixedSize(16, 16)
        
        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(f"color: {HTB_TEXT_SEC}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        
        header.addWidget(icon)
        header.addWidget(lbl_title)
        header.addStretch()
        layout.addLayout(header)

        # Value
        self.lbl_value = QLabel(str(value))
        self.lbl_value.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 700;")
        layout.addWidget(self.lbl_value)
    
    def set_value(self, val):
        self.lbl_value.setText(str(val))


class ModernInput(QLineEdit):
    """
    Styled input field.
    """
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {HTB_BG_INPUT};
                border: 1px solid {HTB_BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                color: {HTB_TEXT_MAIN};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {HTB_GREEN};
                background-color: {HTB_BG_HOVER};
            }}
            QLineEdit::placeholder {{
                color: {HTB_TEXT_MUTED};
            }}
        """)
