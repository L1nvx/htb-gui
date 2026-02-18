"""Seasons Page - Borderless HTB Style."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QFrame, QScrollArea, QHeaderView, QSizePolicy,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject, QUrl
from PySide6.QtGui import QPixmap, QIcon, QPainter, QPainterPath
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from typing import List, Optional

from api.endpoints import HTBApi
from models.season import Season, LeaderboardEntry
from models.machine import Machine
from ui.styles import HTB_GREEN, HTB_TEXT_DIM, HTB_BG_CARD
from ui.widgets.machine_card import MachineCard
from utils.debug import debug_log
from utils.image_cache import get_cached_image, save_to_cache


class SeasonsWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, season_id: Optional[int] = None):
        super().__init__()
        self.season_id = season_id
    
    def run(self):
        data = {}
        try:
            success, result = HTBApi.get_seasons()
            if success:
                seasons = [Season.from_api(s) for s in result.get("data", [])]
                data["seasons"] = seasons
                if self.season_id:
                    active = next((s for s in seasons if s.id == self.season_id), seasons[0] if seasons else None)
                else:
                    active = next((s for s in seasons if s.active), seasons[0] if seasons else None)
                if active:
                    data["active"] = active
                    self.season_id = active.id
            
            if self.season_id:
                success, result = HTBApi.get_season_machines(self.season_id)
                if success:
                    raw = [m for m in result.get("data", []) if not m.get("unknown")]
                    machines = [Machine.from_api(m) for m in raw]
                    # Enrich with real owns from machine profile
                    for machine in machines:
                        if machine.name and machine.user_owns_count == 0:
                            try:
                                ok, profile = HTBApi.get_machine_profile(machine.name)
                                if ok:
                                    info = profile.get("info", {})
                                    machine.user_owns_count = info.get("user_owns_count", 0)
                                    machine.root_owns_count = info.get("root_owns_count", 0)
                            except Exception:
                                pass
                    data["machines"] = machines
                
                success, result = HTBApi.get_season_leaderboard(self.season_id)
                if success:
                    data["leaderboard"] = [LeaderboardEntry.from_api(e) for e in result.get("data", [])]
            
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class SeasonsPage(QWidget):
    machine_selected = Signal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._seasons: List[Season] = []
        self._current: Optional[Season] = None
        self._thread = None
        self._worker = None
        self._loading = False
        self._loaded = False
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_leaderboard_avatar_loaded)
        self._machine_avatar_network = QNetworkAccessManager(self)
        self._machine_avatar_network.finished.connect(self._on_machine_avatar_loaded)
        self._machine_cards = {}
        self._zombie_threads: List[QThread] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)
        
        header = QHBoxLayout()
        title = QLabel("Seasons")
        title.setStyleSheet("font-size: 28px; font-weight: 700; letter-spacing: -0.5px;")
        header.addWidget(title)
        header.addStretch()
        self.season_combo = QComboBox()
        self.season_combo.setMinimumWidth(200)
        self.season_combo.currentIndexChanged.connect(self._on_season_changed)
        header.addWidget(self.season_combo)
        layout.addLayout(header)
        
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet(f"background-color: {HTB_BG_CARD}; border-radius: 12px;")
        self.info_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        info_layout = QHBoxLayout(self.info_frame)
        info_layout.setContentsMargins(24, 20, 24, 20)
        
        info_left = QVBoxLayout()
        self.season_name = QLabel("Season")
        self.season_name.setStyleSheet("font-size: 22px; font-weight: 700;")
        info_left.addWidget(self.season_name)
        self.season_dates = QLabel("")
        self.season_dates.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        info_left.addWidget(self.season_dates)
        info_layout.addLayout(info_left)
        info_layout.addStretch()
        
        info_right = QVBoxLayout()
        info_right.setAlignment(Qt.AlignRight)
        self.players_label = QLabel("0")
        self.players_label.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {HTB_GREEN};")
        info_right.addWidget(self.players_label, alignment=Qt.AlignRight)
        players_text = QLabel("Players")
        players_text.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 12px;")
        info_right.addWidget(players_text, alignment=Qt.AlignRight)
        info_layout.addLayout(info_right)
        layout.addWidget(self.info_frame)
        
        machines_label = QLabel("SEASON MACHINES")
        machines_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(machines_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(150)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setFrameShape(QFrame.NoFrame)
        self.machines_widget = QWidget()
        self.machines_widget.setStyleSheet("background: transparent;")
        self.machines_layout = QHBoxLayout(self.machines_widget)
        self.machines_layout.setAlignment(Qt.AlignLeft)
        self.machines_layout.setSpacing(16)
        self.machines_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.machines_widget)
        layout.addWidget(scroll)
        
        lb_label = QLabel("LEADERBOARD")
        lb_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(lb_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Rank", "Player", "Points", "Owns"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet(f"background-color: {HTB_BG_CARD}; border-radius: 8px;")
        layout.addWidget(self.table)
    
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

    def load_data(self, season_id: Optional[int] = None):
        if self._loading:
            return
        self._loading = True
        self._cleanup_thread()
        sid = season_id or (self._current.id if self._current else None)
        self._thread = QThread()
        self._worker = SeasonsWorker(sid)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_loaded)
        self._worker.error.connect(self._on_error)
        self._thread.start()
    
    @Slot(dict)
    def _on_loaded(self, data: dict):
        self._loading = False
        self._loaded = True
        self._cleanup_thread()
        
        if "seasons" in data:
            self._seasons = data["seasons"]
            self.season_combo.blockSignals(True)
            self.season_combo.clear()
            for s in self._seasons:
                self.season_combo.addItem(f"{'🟢' if s.active else '⚪'} {s.name}", s.id)
            self.season_combo.blockSignals(False)
        
        if "active" in data:
            s = data["active"]
            self._current = s
            self.season_name.setText(s.name)
            self.season_dates.setText(f"📅 {s.date_range}")
            self.players_label.setText(f"{s.players:,}")
        
        if "machines" in data:
            self._machine_cards.clear()
            while self.machines_layout.count():
                w = self.machines_layout.takeAt(0).widget()
                if w: w.deleteLater()
            for m in data["machines"]:
                card = MachineCard(m)
                card.clicked.connect(self.machine_selected.emit)
                self.machines_layout.addWidget(card)
                self._machine_cards[m.id] = card
                if m.avatar:
                    cached = get_cached_image(m.avatar)
                    if cached:
                        card.set_avatar_pixmap(cached)
                    else:
                        req = QNetworkRequest(QUrl(m.avatar))
                        reply = self._machine_avatar_network.get(req)
                        reply.setProperty("machine_id", m.id)
                        reply.setProperty("url", m.avatar)
        
        if "leaderboard" in data:
            entries = data["leaderboard"]
            self.table.setRowCount(len(entries))
            for i, e in enumerate(entries):
                self.table.setItem(i, 0, QTableWidgetItem(f"#{e.rank}"))
                player_item = QTableWidgetItem(e.name)
                self.table.setItem(i, 1, player_item)
                if e.avatar_thumb:
                    url = e.avatar_thumb if e.avatar_thumb.startswith("http") else f"https://labs.hackthebox.com{e.avatar_thumb}"
                    cached = get_cached_image(url)
                    if cached:
                        size = 28
                        rounded = QPixmap(size, size)
                        rounded.fill(Qt.transparent)
                        painter = QPainter(rounded)
                        painter.setRenderHint(QPainter.Antialiasing)
                        path = QPainterPath()
                        path.addEllipse(0, 0, size, size)
                        painter.setClipPath(path)
                        painter.drawPixmap(0, 0, size, size, cached.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                        painter.end()
                        player_item.setIcon(QIcon(rounded))
                    else:
                        req = QNetworkRequest(QUrl(url))
                        reply = self._network_manager.get(req)
                        reply.setProperty("row", i)
                        reply.setProperty("col", 1)
                        reply.setProperty("url", url)
                self.table.setItem(i, 2, QTableWidgetItem(str(e.points)))
                self.table.setItem(i, 3, QTableWidgetItem(f"{e.user_owns}/{e.root_owns}"))

    @Slot(QNetworkReply)
    def _on_machine_avatar_loaded(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            reply.deleteLater()
            return
        machine_id = reply.property("machine_id")
        url = reply.property("url")
        if machine_id is not None and machine_id in self._machine_cards:
            img_data = reply.readAll()
            pixmap = save_to_cache(url, img_data) if url else None
            if not pixmap:
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
            if pixmap and not pixmap.isNull():
                self._machine_cards[machine_id].set_avatar_pixmap(pixmap)
        reply.deleteLater()
    
    @Slot(QNetworkReply)
    def _on_leaderboard_avatar_loaded(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            reply.deleteLater()
            return
        row = reply.property("row")
        col = reply.property("col")
        url = reply.property("url")
        if row is not None and col is not None and row < self.table.rowCount():
            item = self.table.item(row, col)
            if item:
                img_data = reply.readAll()
                pixmap = save_to_cache(url, img_data) if url else None
                if not pixmap:
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                if pixmap and not pixmap.isNull():
                    size = 28
                    rounded = QPixmap(size, size)
                    rounded.fill(Qt.transparent)
                    painter = QPainter(rounded)
                    painter.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath()
                    path.addEllipse(0, 0, size, size)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, size, size, pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                    painter.end()
                    item.setIcon(QIcon(rounded))
        reply.deleteLater()

    @Slot(str)
    def _on_error(self, error: str):
        self._loading = False
        self._cleanup_thread()
    
    def _on_season_changed(self, index: int):
        if index < 0 or not self._seasons or self._loading:
            return
        sid = self.season_combo.itemData(index)
        if sid and (not self._current or sid != self._current.id):
            self.load_data(sid)
    
    def showEvent(self, event):
        super().showEvent(event)
        if not self._loaded and not self._loading:
            self.load_data()
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self._cleanup_thread()
