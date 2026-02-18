"""
Custom Title Bar for Frameless Window.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QIcon

import qtawesome as qta
from ui.styles import HTB_BG_DARKEST, HTB_TEXT_SEC, HTB_TEXT_MAIN

class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {HTB_BG_DARKEST};")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(10)
        
        # Icon & Title
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(qta.icon("fa5s.terminal", color=HTB_TEXT_MAIN).pixmap(16, 16))
        
        self.title_lbl = QLabel("HTB Client")
        self.title_lbl.setStyleSheet(f"color: {HTB_TEXT_MAIN}; font-weight: 600; font-size: 13px;")
        
        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.title_lbl)
        layout.addStretch()
        
        # Window Controls
        btn_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """
        
        self.btn_min = QPushButton()
        self.btn_min.setIcon(qta.icon("fa5s.minus", color=HTB_TEXT_SEC))
        self.btn_min.setFixedSize(30, 30)
        self.btn_min.setStyleSheet(btn_style)
        self.btn_min.clicked.connect(self.minimize_window)
        
        self.btn_max = QPushButton()
        self.btn_max.setIcon(qta.icon("fa5s.expand", color=HTB_TEXT_SEC))
        self.btn_max.setFixedSize(30, 30)
        self.btn_max.setStyleSheet(btn_style)
        self.btn_max.clicked.connect(self.maximize_restore_window)
        
        self.btn_close = QPushButton()
        self.btn_close.setIcon(qta.icon("fa5s.times", color=HTB_TEXT_SEC))
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff2a6d;
                color: white;
            }
        """)
        self.btn_close.clicked.connect(self.close_window)
        
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)
        
        # Mouse tracking for dragging
        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.start_pos:
            self.parent_window.move(event.globalPosition().toPoint() - self.start_pos)
            event.accept()

    def minimize_window(self):
        self.parent_window.showMinimized()

    def maximize_restore_window(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.btn_max.setIcon(qta.icon("fa5s.expand", color=HTB_TEXT_SEC))
        else:
            self.parent_window.showMaximized()
            self.btn_max.setIcon(qta.icon("fa5s.compress", color=HTB_TEXT_SEC))

    def close_window(self):
        self.parent_window.close()
