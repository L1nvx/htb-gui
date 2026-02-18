"""
Top navigation bar with icons.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QButtonGroup
)
from PySide6.QtCore import Signal, QSize, Qt

import qtawesome as qta
from ui.styles import HTB_GREEN, HTB_TEXT_SEC, HTB_BG_HOVER, HTB_BG_CARD

class TopNav(QWidget):
    page_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border-bottom: 1px solid #222;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.btn_group.buttonClicked.connect(self._on_btn_clicked)
        
        # Navigation Items (ID, Icon, Tooltip)
        items = [
            ("dashboard", "fa5s.tachometer-alt", "Dashboard"),
            ("machines", "fa5s.desktop", "Machines"),
            ("seasons", "fa5s.trophy", "Seasons"),
            ("toolkit", "fa5s.tools", "Toolkit"),
            ("vpn", "fa5s.network-wired", "VPN"),
            ("settings", "fa5s.cog", "Settings"),
        ]
        
        for btn_id, icon, tooltip in items:
            btn = self._create_nav_btn(btn_id, icon, tooltip)
            layout.addWidget(btn)
            self.btn_group.addButton(btn)
        
        layout.addStretch()
        
        # Select first one by default
        if self.btn_group.buttons():
            self.btn_group.buttons()[0].setChecked(True)

    def _create_nav_btn(self, btn_id: str, icon_name: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName(btn_id)
        btn.setCheckable(True)
        btn.setFixedSize(45, 45)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        
        # Icons
        icon_normal = qta.icon(icon_name, color=HTB_TEXT_SEC)
        icon_active = qta.icon(icon_name, color=HTB_GREEN)
        
        btn.setIcon(icon_normal)
        btn.setIconSize(QSize(20, 20))
        
        # Store icons for state changes - we'll use a dynamic property or just re-set
        # Using a simple approach: updated in _update_icon
        btn.setProperty("icon_name", icon_name)
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {HTB_BG_HOVER};
            }}
            QPushButton:checked {{
                background-color: {HTB_BG_CARD};
                border: none;
            }}
        """)
        
        btn.toggled.connect(lambda checked, b=btn: self._update_icon(b, checked))
        
        return btn
    
    def _update_icon(self, btn, checked):
        icon_name = btn.property("icon_name")
        if checked:
            btn.setIcon(qta.icon(icon_name, color=HTB_GREEN))
        else:
            btn.setIcon(qta.icon(icon_name, color=HTB_TEXT_SEC))

    def _on_btn_clicked(self, btn):
        btn_id = btn.objectName()
        self.page_changed.emit(btn_id)
        
    def set_active(self, page_id: str):
        btn = self.findChild(QPushButton, page_id)
        if btn:
            btn.setChecked(True)
