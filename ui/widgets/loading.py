"""
Loading Spinner Widget
Animated loading indicator.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, Property
from PySide6.QtGui import QPainter, QColor, QPen

from ui.styles import HTB_GREEN, HTB_BG_DARK


class LoadingSpinner(QWidget):
    """
    Animated loading spinner widget.
    """
    
    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self._size = size
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._color = QColor(HTB_GREEN)
        
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)
    
    def start(self):
        """Start the spinner animation."""
        self._timer.start(16)  # ~60 FPS
        self.show()
    
    def stop(self):
        """Stop the spinner animation."""
        self._timer.stop()
        self.hide()
    
    def _rotate(self):
        """Rotate the spinner."""
        self._angle = (self._angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Paint the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate dimensions
        center = self._size // 2
        radius = (self._size - 8) // 2
        
        # Draw arc
        pen = QPen(self._color)
        pen.setWidth(4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Create gradient effect by drawing multiple arcs
        for i in range(8):
            alpha = 255 - (i * 30)
            color = QColor(self._color)
            color.setAlpha(max(alpha, 30))
            pen.setColor(color)
            painter.setPen(pen)
            
            angle = self._angle - (i * 20)
            painter.drawArc(
                4, 4, 
                self._size - 8, self._size - 8,
                angle * 16, 30 * 16
            )


class LoadingOverlay(QWidget):
    """
    Full overlay with loading spinner and optional message.
    """
    
    def __init__(self, message: str = "Loading...", parent=None):
        super().__init__(parent)
        self._setup_ui(message)
    
    def _setup_ui(self, message: str):
        self.setStyleSheet("""
            background-color: rgba(16, 25, 39, 0.92);
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Spinner
        self.spinner = LoadingSpinner(60, self)
        layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        
        # Message
        if message:
            label = QLabel(message)
            label.setStyleSheet(f"""
                color: {HTB_GREEN};
                font-size: 14px;
                font-weight: 500;
                margin-top: 16px;
                background: transparent;
            """)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
        
        self.spinner.start()
    
    def setMessage(self, message: str):
        """Update the loading message."""
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setText(message)
                break
    
    def showEvent(self, event):
        """Start spinner when shown."""
        self.spinner.start()
        super().showEvent(event)
    
    def hideEvent(self, event):
        """Stop spinner when hidden."""
        self.spinner.stop()
        super().hideEvent(event)
