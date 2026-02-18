"""Machine Card Widget - HTB style, hover con borde verde, con avatar de máquina."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter, QPainterPath

from models.machine import Machine
from ui.styles import (
    HTB_GREEN, HTB_BG_CARD, HTB_BG_HOVER, HTB_TEXT_DIM, HTB_TEXT_SEC, HTB_TEXT_MAIN,
    HTB_BORDER, DIFF_EASY, DIFF_MEDIUM, DIFF_HARD, DIFF_INSANE
)


class MachineCard(QFrame):
    clicked = Signal(object)
    
    def __init__(self, machine: Machine, parent=None):
        super().__init__(parent)
        self.machine = machine
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setMinimumWidth(200)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        diff_colors = {"easy": DIFF_EASY, "medium": DIFF_MEDIUM, "hard": DIFF_HARD, "insane": DIFF_INSANE}
        self._color = diff_colors.get(self.machine.difficulty_text.lower(), HTB_TEXT_SEC)
        
        # Modern Card Styles
        self._normal = f"""
            MachineCard {{
                background-color: {HTB_BG_CARD};
                border-radius: 12px;
                border: 1px solid {HTB_BORDER};
            }}
        """
        self._hover = f"""
            MachineCard {{
                background-color: {HTB_BG_HOVER};
                border-radius: 12px;
                border: 1px solid {HTB_GREEN};
            }}
        """
        self.setStyleSheet(self._normal)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        
        # Top row: Avatar + OS icon + difficulty
        top = QHBoxLayout()
        top.setSpacing(10)
        
        # Avatar de la máquina (imagen)
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(40, 40)
        self.avatar_label.setStyleSheet("background-color: #1a2638; border-radius: 8px; border: none;")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        top.addWidget(self.avatar_label)
        
        # OS Icon (using text for now, could be qtawesome if logic allowed)
        os_lbl = QLabel(self.machine.os_icon)
        os_lbl.setStyleSheet("font-size: 20px; background: transparent; border: none;")
        top.addWidget(os_lbl)
        
        top.addStretch()
        
        diff_lbl = QLabel(self.machine.difficulty_text)
        diff_lbl.setStyleSheet(f"color: {self._color}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; background: transparent; border: none;")
        top.addWidget(diff_lbl)
        layout.addLayout(top)
        
        name = QLabel(self.machine.name)
        name.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {HTB_TEXT_MAIN}; background: transparent; border: none;")
        name.setWordWrap(True)
        layout.addWidget(name)
        
        meta = QLabel(f"⭐ {self.machine.rating:.1f}  ·  {self.machine.user_owns_count:,} owns")
        meta.setStyleSheet(f"color: {HTB_TEXT_SEC}; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(meta)
        
        layout.addStretch()
        
        if self.machine.auth_user_in_root_owns:
            owned = QLabel("✓ Owned")
            owned.setStyleSheet(f"color: {HTB_GREEN}; font-size: 12px; font-weight: 600; background: transparent; border: none;")
            layout.addWidget(owned)
    
    def set_avatar_pixmap(self, pixmap: QPixmap):
        """Setear el avatar de la máquina desde un pixmap cargado externamente."""
        if pixmap.isNull():
            return
        # Escalar y redondear esquinas
        scaled = pixmap.scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        rounded = QPixmap(40, 40)
        rounded.fill(Qt.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, 40, 40, 8, 8)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, 40, 40, scaled)
        painter.end()
        self.avatar_label.setPixmap(rounded)
        self.avatar_label.setStyleSheet("border-radius: 8px; background: transparent; border: none;")
    
    def enterEvent(self, event):
        self.setStyleSheet(self._hover)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setStyleSheet(self._normal)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.machine)
        super().mousePressEvent(event)
