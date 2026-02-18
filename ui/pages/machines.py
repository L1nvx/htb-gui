"""Machines Page - HTB Style with responsive grid and machine avatars."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QScrollArea, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtGui import QPixmap
from typing import List, Dict

from api.endpoints import HTBApi
from models.machine import Machine
from ui.styles import HTB_TEXT_DIM, HTB_TEXT_MAIN
from ui.widgets.machine_card import MachineCard
from ui.widgets.modern_widgets import ModernButton
from utils.debug import debug_log
from utils.image_cache import get_cached_image, save_to_cache


class MachinesWorker(QObject):
    finished = Signal(list)
    error = Signal(str)
    
    def run(self):
        try:
            success, result = HTBApi.get_machines()
            if success:
                machines = [Machine.from_api(m) for m in result.get("data", [])]
                self.finished.emit(machines)
            else:
                self.error.emit(str(result))
        except Exception as e:
            self.error.emit(str(e))


class MachinesPage(QWidget):
    machine_selected = Signal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._machines: List[Machine] = []
        self._thread = None
        self._worker = None
        self._loading = False
        self._loaded = False
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_avatar_loaded)
        self._machine_cards: Dict[int, MachineCard] = {}  # machine_id -> card
        self._zombie_threads: List[QThread] = [] # Prevent premature destruction
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)
        
        # Header + search bar
        header = QHBoxLayout()
        title = QLabel("Machines")
        title.setStyleSheet(f"font-size: 26px; font-weight: 700; letter-spacing: -0.5px; color: {HTB_TEXT_MAIN};")
        header.addWidget(title)
        header.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name...")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(280)
        self.search.setMaximumWidth(400)
        self.search.setMinimumHeight(42)
        # Global styles handle the rest
        self.search.textChanged.connect(self._apply_filters)
        header.addWidget(self.search)
        layout.addLayout(header)
        
        # Filters row
        filters = QHBoxLayout()
        filters.setSpacing(10)
        self.os_filter = QComboBox()
        self.os_filter.addItems(["All OS", "Linux", "Windows", "FreeBSD"])
        self.os_filter.currentTextChanged.connect(self._apply_filters)
        filters.addWidget(self.os_filter)
        self.diff_filter = QComboBox()
        self.diff_filter.addItems(["All Difficulty", "Easy", "Medium", "Hard", "Insane"])
        self.diff_filter.currentTextChanged.connect(self._apply_filters)
        filters.addWidget(self.diff_filter)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Machines", "Free Only", "Owned"])
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        filters.addWidget(self.status_filter)
        filters.addStretch()
        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        filters.addWidget(self.count_label)
        
        refresh_btn = ModernButton(" Refresh", "fa5s.sync-alt", "ghost")
        refresh_btn.clicked.connect(self._force_reload)
        filters.addWidget(refresh_btn)
        layout.addLayout(filters)
        
        # Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)
    
    def _force_reload(self):
        self._loaded = False
        self.load_data()
    
    def load_data(self):
        if self._loading:
            return
        self._loading = True
        self._cleanup_thread()
        
        self._thread = QThread()
        self._worker = MachinesWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_loaded)
        self._worker.error.connect(self._on_error)
        self._thread.start()
    
    def _safe_cleanup_thread(self, thread: QThread, worker: QObject):
        if not thread: return
        if worker:
            try: worker.disconnect()
            except: pass
        if thread.isRunning():
            self._zombie_threads.append(thread)
            thread.finished.connect(lambda t=thread: self._on_zombie_finished(t))
            thread.quit()
        else:
            thread.deleteLater()
            if worker: worker.deleteLater()

    def _on_zombie_finished(self, thread: QThread):
        if thread in self._zombie_threads:
            self._zombie_threads.remove(thread)
        thread.deleteLater()

    def _cleanup_thread(self):
        self._safe_cleanup_thread(self._thread, self._worker)
        self._thread = None
        self._worker = None

    def stop_background_tasks(self):
        """Llamado al cerrar la app para evitar QThread destroyed while running."""
        self._loading = False
        self._cleanup_thread()
    
    @Slot(list)
    def _on_loaded(self, machines: List[Machine]):
        self._loading = False
        self._loaded = True
        self._machines = machines
        self._cleanup_thread()
        self._apply_filters()
    
    @Slot(str)
    def _on_error(self, error: str):
        self._loading = False
        self._cleanup_thread()
        debug_log("MACHINES", f"Error: {error}")
    
    def _apply_filters(self):
        query = self.search.text().lower()
        os_f = self.os_filter.currentText()
        diff_f = self.diff_filter.currentText()
        status_f = self.status_filter.currentText()
        
        filtered = []
        for m in self._machines:
            if query and query not in m.name.lower():
                continue
            if os_f != "All OS" and m.os != os_f:
                continue
            if diff_f != "All Difficulty" and m.difficulty_text != diff_f:
                continue
            if status_f == "Free Only" and not m.free:
                continue
            if status_f == "Owned" and not m.auth_user_in_root_owns:
                continue
            filtered.append(m)
        
        self._display(filtered)
    
    def _display(self, machines: List[Machine]):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._machine_cards.clear()
        self.count_label.setText(f"{len(machines)} machines")
        
        cols = max(1, (self.width() - 80) // 220)
        
        for i, m in enumerate(machines):
            card = MachineCard(m)
            card.clicked.connect(self.machine_selected.emit)
            self.grid_layout.addWidget(card, i // cols, i % cols)
            self._machine_cards[m.id] = card
            
            # Cargar avatar si tiene URL (usar caché)
            if m.avatar:
                cached = get_cached_image(m.avatar)
                if cached:
                    card.set_avatar_pixmap(cached)
                else:
                    req = QNetworkRequest(QUrl(m.avatar))
                    reply = self._network_manager.get(req)
                    reply.setProperty("machine_id", m.id)
                    reply.setProperty("url", m.avatar)
    
    @Slot(QNetworkReply)
    def _on_avatar_loaded(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            reply.deleteLater()
            return
        machine_id = reply.property("machine_id")
        url = reply.property("url")
        if machine_id is not None and machine_id in self._machine_cards:
            data = reply.readAll()
            pixmap = save_to_cache(url, data) if url else None
            if not pixmap:
                pixmap = QPixmap()
                pixmap.loadFromData(data)
            if pixmap and not pixmap.isNull():
                self._machine_cards[machine_id].set_avatar_pixmap(pixmap)
        reply.deleteLater()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._machines:
            self._apply_filters()
    
    def showEvent(self, event):
        super().showEvent(event)
        if not self._loaded and not self._loading:
            self.load_data()
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self._cleanup_thread()

