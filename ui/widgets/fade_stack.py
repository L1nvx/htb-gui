"""
FadeStackWidget - QStackedWidget with fade-in transition.
"""

from PySide6.QtWidgets import QStackedWidget, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt

class FadeStackWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 200
        self.easing = QEasingCurve.OutQuad

    def setCurrentIndex(self, index: int):
        self.fade_to(index)

    def setCurrentWidget(self, widget: QWidget):
        index = self.indexOf(widget)
        if index != -1:
            self.fade_to(index)

    def fade_to(self, index: int):
        curr_idx = self.currentIndex()
        if curr_idx == index:
            return

        # Hide current immediately
        current = self.currentWidget()
        if current:
            current.hide()
            
        # Switch to new
        super().setCurrentIndex(index)
        
        # Animate new
        next_widget = self.widget(index)
        if next_widget:
            # Create effect if needed
            eff = next_widget.graphicsEffect()
            if not eff or not isinstance(eff, QGraphicsOpacityEffect):
                eff = QGraphicsOpacityEffect(next_widget)
                next_widget.setGraphicsEffect(eff)
            
            # Reset opacity to 0
            eff.setOpacity(0)
            
            # Animate to 1
            self.anim = QPropertyAnimation(eff, b"opacity")
            self.anim.setDuration(self.duration)
            self.anim.setStartValue(0)
            self.anim.setEndValue(1)
            self.anim.setEasingCurve(self.easing)
            self.anim.start()
