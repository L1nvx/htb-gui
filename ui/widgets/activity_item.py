"""Single activity row - timeline style con avatar."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon, QPainter, QPainterPath

from ui.styles import HTB_TEXT_DIM, HTB_TEXT_MUTED


class ActivityItem(QFrame):
    """Una fila de actividad: avatar + usuario + tipo (user/root blood) + fecha."""

    def __init__(self, date_diff: str, user_name: str, entry_type: str, blood_type: str = "", avatar_url: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("activity_item")
        self.setStyleSheet(f"""
            QFrame#activity_item {{
                background-color: rgba(21, 31, 46, 0.6);
                border-radius: 10px;
                border: none;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(36, 36)
        self.avatar_label.setStyleSheet("background-color: #1a2638; border-radius: 18px;")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.avatar_label)

        # Texto: usuario + tipo
        # Si es blood, mostramos 🩸 + el tipo de blood (user/root)
        # Si no es blood, mostramos solo el tipo (user/root) sin icono de sangre
        text = QLabel()
        if entry_type == "blood":
            label = blood_type.upper() if blood_type else "BLOOD"
            icon = "🩸"
            text.setText(f"<span style='font-weight: 600;'>{user_name}</span>  <span style='color: #ff4444; font-size: 12px;'>{icon} {label}</span>")
        else:
            label = entry_type.upper() if entry_type else "OWN"
            text.setText(f"<span style='font-weight: 600;'>{user_name}</span>  <span style='color: #94a3b8; font-size: 12px;'>{label}</span>")
        text.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        text.setTextFormat(Qt.RichText)
        layout.addWidget(text)

        layout.addStretch()

        self.date_label = QLabel(date_diff)
        self.date_label.setStyleSheet(f"color: {HTB_TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self.date_label)

        self._avatar_url = avatar_url

    def set_avatar_pixmap(self, pixmap: QPixmap):
        if pixmap.isNull():
            return
        scaled = pixmap.scaled(36, 36, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        rounded = QPixmap(36, 36)
        rounded.fill(Qt.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, 36, 36)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, 36, 36, scaled)
        painter.end()
        self.avatar_label.setPixmap(rounded)
        self.avatar_label.setStyleSheet("border-radius: 18px;")
