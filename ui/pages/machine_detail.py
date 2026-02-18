"""Machine Detail Page - Borderless HTB Style."""

import re
from datetime import datetime, timezone

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QMessageBox,
    QScrollArea, QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject, QTimer, QUrl, QSize
from PySide6.QtGui import QColor, QPalette, QPixmap, QIcon, QPainter, QPainterPath
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from typing import Optional, List

from api.endpoints import HTBApi
from models.machine import Machine
from ui.styles import (
    HTB_GREEN, HTB_BG_CARD, HTB_BG_MAIN, HTB_TEXT_DIM,
    DIFF_EASY, DIFF_MEDIUM, DIFF_HARD, DIFF_INSANE,
    BTN_PRIMARY, BTN_DANGER, BTN_DEFAULT
)
from ui.widgets.activity_item import ActivityItem
from ui.widgets.modern_widgets import ModernButton, ModernInput
from utils.debug import debug_log


class ActionWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, action: str, machine_id: int, flag: str = None):
        super().__init__()
        self.action = action
        self.machine_id = machine_id
        self.flag = flag
    
    def run(self):
        try:
            if self.action == "spawn":
                success, result = HTBApi.spawn_machine(self.machine_id)
            elif self.action == "terminate":
                success, result = HTBApi.terminate_machine(self.machine_id)
            elif self.action == "reset":
                success, result = HTBApi.reset_machine(self.machine_id)
            elif self.action == "flag":
                success, result = HTBApi.submit_flag(self.machine_id, self.flag)
            else:
                self.error.emit("Unknown action")
                return
            
            if success:
                self.finished.emit({"action": self.action, "result": result})
            else:
                self.error.emit(str(result))
        except Exception as e:
            self.error.emit(str(e))


class ActivityWorker(QObject):
    finished = Signal(list)
    error = Signal(str)
    
    def __init__(self, machine_id: int):
        super().__init__()
        self.machine_id = machine_id
    
    def run(self):
        try:
            success, result = HTBApi.get_machine_activity(self.machine_id)
            if success and isinstance(result, dict):
                info = result.get("info", {})
                activity = info.get("activity", [])
                self.finished.emit(activity)
            else:
                self.error.emit(str(result) if not success else "Invalid response")
        except Exception as e:
            self.error.emit(str(e))


class ActiveMachineWorker(QObject):
    """Obtiene la máquina activa (solo hay una en HTB) para mostrar IP en detalle."""
    finished = Signal(object)  # ActiveMachine or None
    error = Signal(str)
    
    def run(self):
        try:
            success, result = HTBApi.get_active_machine()
            if success and isinstance(result, dict):
                from models.connection import ActiveMachine
                active = ActiveMachine.from_api(result)
                self.finished.emit(active)
            else:
                self.finished.emit(None)
        except Exception as e:
            self.error.emit(str(e))


class _ToggleSwitch(QWidget):
    """A proper iOS-style toggle switch widget."""
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(40, 22)
        self.setCursor(Qt.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        self._checked = checked
        self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.update()
        self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2

        # Track
        if self._checked:
            p.setBrush(QColor(HTB_GREEN))
            p.setPen(QColor(HTB_GREEN))
        else:
            p.setBrush(QColor("#2a2a3e"))
            p.setPen(QColor("#555"))
        p.drawRoundedRect(0, 0, w, h, r, r)

        # Knob
        knob_r = h - 4
        x = (w - knob_r - 2) if self._checked else 2
        p.setBrush(QColor("#ffffff"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(x, 2, knob_r, knob_r)
        p.end()


class MachineDetailPage(QWidget):
    back_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._machine: Optional[Machine] = None
        self._action_thread = None
        self._action_worker = None
        self._activity_thread = None
        self._activity_worker = None
        
        self._activity_timer = QTimer(self)
        self._activity_timer.setInterval(15000)  # 15 segundos
        self._activity_timer.timeout.connect(self._load_activity)
        self._activity_countdown = QTimer(self)
        self._activity_countdown.setInterval(1000)
        self._activity_countdown.timeout.connect(self._update_refresh_countdown)
        self._activity_seconds_left = 15
        
        # Timer para polling de IP después del spawn
        self._ip_poll_timer = QTimer(self)
        self._ip_poll_timer.setInterval(3000)  # Cada 3 segundos
        self._ip_poll_timer.timeout.connect(self._poll_for_ip)
        self._ip_poll_count = 0
        
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_activity_avatar_loaded)
        self._avatar_network = QNetworkAccessManager(self)
        self._avatar_network.finished.connect(self._on_machine_avatar_loaded)
        self._activity_items: List[ActivityItem] = []
        self._active_machine_thread = None
        self._active_machine_worker = None
        
        # Timer para animación "Starting."
        self._starting_anim_timer = QTimer(self)
        self._starting_anim_timer.setInterval(400)
        self._starting_anim_timer.timeout.connect(self._animate_starting)
        self._starting_dots = 0
        self._zombie_threads: List[QThread] = []

        # --- Auto-Spawn state ---
        self._auto_spawn_enabled = False
        self._auto_spawn_countdown_timer = QTimer(self)
        self._auto_spawn_countdown_timer.setInterval(1000)
        self._auto_spawn_countdown_timer.timeout.connect(self._auto_spawn_tick)
        self._release_dt: Optional[datetime] = None
        self._spawn_attempts = 0
        self._spawn_phase = "countdown"  # "countdown" | "spawning"

        # --- Flag Watcher state ---
        self._flag_watcher_enabled = False
        self._flag_watcher_timer = QTimer(self)
        self._flag_watcher_timer.setInterval(2000)
        self._flag_watcher_timer.timeout.connect(self._flag_watcher_tick)
        self._last_submitted_flag = ""
        self._flag_submitting = False

        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)
        
        # Back
        back_btn = ModernButton(" Back to Machines", "fa5s.arrow-left", "ghost")
        back_btn.setStyleSheet(back_btn.styleSheet() + "text-align: left; padding-left: 0;")
        back_btn.setFixedWidth(200)
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(16)
        
        # Avatar de la máquina
        self.machine_avatar = QLabel()
        self.machine_avatar.setFixedSize(56, 56)
        self.machine_avatar.setStyleSheet("background-color: #1a2638; border-radius: 10px;")
        self.machine_avatar.setAlignment(Qt.AlignCenter)
        header.addWidget(self.machine_avatar)
        
        self.os_icon = QLabel("🐧")
        self.os_icon.setStyleSheet("font-size: 48px;")
        header.addWidget(self.os_icon)
        
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        
        self.name_label = QLabel("Machine")
        self.name_label.setStyleSheet("font-size: 28px; font-weight: 700; letter-spacing: -0.5px;")
        self.name_label.setWordWrap(True)
        info_col.addWidget(self.name_label)
        
        meta_row = QHBoxLayout()
        meta_row.setSpacing(16)
        
        self.difficulty_badge = QLabel("Easy")
        self.difficulty_badge.setStyleSheet(f"color: {DIFF_EASY}; font-weight: 700; font-size: 14px;")
        meta_row.addWidget(self.difficulty_badge)
        
        self.rating_label = QLabel("⭐ 4.5")
        self.rating_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 14px;")
        meta_row.addWidget(self.rating_label)
        
        self.points_label = QLabel("20 pts")
        self.points_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 14px;")
        meta_row.addWidget(self.points_label)
        
        self.ip_label = QLabel("")
        self.ip_label.setStyleSheet(f"color: {HTB_GREEN}; font-size: 14px; font-weight: 600; font-family: monospace;")
        meta_row.addWidget(self.ip_label)
        
        meta_row.addStretch()
        info_col.addLayout(meta_row)
        
        header.addLayout(info_col)
        header.addStretch()
        layout.addLayout(header)
        
        # Stats
        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)
        
        self.user_owns_label = QLabel("👤 0 user owns")
        self.user_owns_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        stats_row.addWidget(self.user_owns_label)
        
        self.root_owns_label = QLabel("💀 0 root owns")
        self.root_owns_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        stats_row.addWidget(self.root_owns_label)
        
        stats_row.addStretch()
        layout.addLayout(stats_row)
        
        # Machine actions: una sola tarjeta (Spawn/Reset/Stop + IP + Flag + status)
        actions_frame = QFrame()
        actions_frame.setObjectName("actions_card")
        actions_frame.setStyleSheet(f"background-color: {HTB_BG_MAIN}; border-radius: 14px;")
        actions_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(24, 20, 24, 20)
        actions_layout.setSpacing(18)
        
        actions_title = QLabel("MACHINE ACTIONS")
        actions_title.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        actions_layout.addWidget(actions_title)
        
        btns_row = QHBoxLayout()
        btns_row.setSpacing(12)
        
        self.spawn_btn = ModernButton(" Spawn Machine", "fa5s.play", "primary")
        self.spawn_btn.clicked.connect(lambda: self._do_action("spawn"))
        btns_row.addWidget(self.spawn_btn)
        
        self.reset_btn = ModernButton(" Reset", "fa5s.redo", "ghost")
        self.reset_btn.clicked.connect(lambda: self._do_action("reset"))
        btns_row.addWidget(self.reset_btn)
        
        self.terminate_btn = ModernButton(" Stop", "fa5s.stop", "danger")
        self.terminate_btn.clicked.connect(lambda: self._do_action("terminate"))
        btns_row.addWidget(self.terminate_btn)
        
        btns_row.addStretch()
        actions_layout.addLayout(btns_row)
        
        ip_row = QHBoxLayout()
        ip_row.setSpacing(12)
        ip_title = QLabel("Machine IP:")
        ip_title.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px; font-weight: 600;")
        ip_row.addWidget(ip_title)
        self.ip_display = QLabel("—")
        self.ip_display.setStyleSheet(f"color: {HTB_GREEN}; font-size: 16px; font-weight: 600; font-family: monospace; min-width: 140px; background: transparent; border: none;")
        self.ip_display.setCursor(Qt.IBeamCursor)
        ip_row.addWidget(self.ip_display)
        self.copy_ip_btn = ModernButton(" Copy IP", "fa5s.copy", "ghost")
        self.copy_ip_btn.setToolTip("Copy IP to clipboard")
        self.copy_ip_btn.clicked.connect(self._copy_ip_to_clipboard)
        ip_row.addWidget(self.copy_ip_btn)
        ip_row.addStretch()
        actions_layout.addLayout(ip_row)
        
        flag_row = QHBoxLayout()
        flag_row.setSpacing(12)
        self.flag_input = ModernInput("Enter the flag")
        self.flag_input.setObjectName("flag_input")
        self.flag_input.setMinimumHeight(42)
        self.flag_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        flag_row.addWidget(self.flag_input)
        
        submit_btn = ModernButton(" Submit Flag", "fa5s.flag", "primary")
        submit_btn.clicked.connect(self._submit_flag)
        flag_row.addWidget(submit_btn)
        actions_layout.addLayout(flag_row)

        # --- Flag Watcher row ---
        fw_row = QHBoxLayout()
        fw_row.setContentsMargins(0, 4, 0, 4)
        fw_row.setSpacing(8)
        self.flag_watcher_toggle = _ToggleSwitch()
        self.flag_watcher_toggle.toggled.connect(self._toggle_flag_watcher)
        fw_row.addWidget(self.flag_watcher_toggle)
        fw_lbl = QLabel("Auto Submit Flag")
        fw_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 12px; font-weight: 600;")
        fw_row.addWidget(fw_lbl)
        self.flag_watcher_status = QLabel("")
        self.flag_watcher_status.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px;")
        fw_row.addWidget(self.flag_watcher_status)
        fw_row.addStretch()
        actions_layout.addLayout(fw_row)

        # --- Auto-Spawn row ---
        as_row = QHBoxLayout()
        as_row.setContentsMargins(0, 4, 0, 4)
        as_row.setSpacing(8)
        self.auto_spawn_toggle = _ToggleSwitch()
        self.auto_spawn_toggle.toggled.connect(self._toggle_auto_spawn)
        as_row.addWidget(self.auto_spawn_toggle)
        as_lbl = QLabel("Auto Spawn Machine")
        as_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 12px; font-weight: 600;")
        as_row.addWidget(as_lbl)
        self.auto_spawn_status = QLabel("")
        self.auto_spawn_status.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px;")
        as_row.addWidget(self.auto_spawn_status)
        as_row.addStretch()
        self.auto_spawn_row_widget = QWidget()
        self.auto_spawn_row_widget.setLayout(as_row)
        self.auto_spawn_row_widget.setVisible(False)
        actions_layout.addWidget(self.auto_spawn_row_widget)

        layout.addWidget(actions_frame)
        
        # Activity timeline
        activity_header = QHBoxLayout()
        activity_label = QLabel("RECENT ACTIVITY")
        activity_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        activity_header.addWidget(activity_label)
        activity_header.addStretch()
        self.refresh_indicator = QLabel("Refreshing in 15s")
        self.refresh_indicator.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px; font-weight: 500;")
        activity_header.addWidget(self.refresh_indicator)
        layout.addLayout(activity_header)

        self.activity_scroll = QScrollArea()
        self.activity_scroll.setWidgetResizable(True)
        self.activity_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.activity_scroll.setStyleSheet("background: transparent; border: none;")
        self.activity_scroll.setFrameShape(QFrame.NoFrame)
        self._activity_container = QWidget()
        self._activity_layout = QVBoxLayout(self._activity_container)
        self._activity_layout.setContentsMargins(0, 0, 8, 0)
        self._activity_layout.setSpacing(8)
        self._activity_layout.setAlignment(Qt.AlignTop)
        self.activity_scroll.setWidget(self._activity_container)
        self.activity_scroll.setMinimumHeight(220)
        self.activity_scroll.setMaximumHeight(280)
        layout.addWidget(self.activity_scroll)
        layout.addStretch()
    
    def set_machine(self, machine: Machine):
        self._machine = machine
        self._update_ui()
        self._load_machine_avatar()
        self._activity_seconds_left = 15
        self.refresh_indicator.setText("Refreshing in 15s")
        self._load_activity()
        self._activity_timer.start()
        self._activity_countdown.start()
        # HTB solo permite una máquina activa: si esta es la activa, obtener IP desde machine/active
        self._fetch_active_machine_ip()

        # --- Auto-spawn: show toggle if machine has future release date ---
        self._stop_auto_spawn()
        self.auto_spawn_toggle.blockSignals(True)
        self.auto_spawn_toggle.setChecked(False)
        self.auto_spawn_toggle.blockSignals(False)
        self.auto_spawn_status.setText("")
        self._release_dt = None
        if machine.release_date:
            try:
                rd = machine.release_date
                # Try common formats
                for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                    try:
                        self._release_dt = datetime.strptime(rd, fmt).replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue
                if self._release_dt and self._release_dt > datetime.now(timezone.utc):
                    self.auto_spawn_row_widget.setVisible(True)
                    td = self._release_dt - datetime.now(timezone.utc)
                    self.auto_spawn_status.setText(f"Releases in {self._format_td(td)}")
                else:
                    self.auto_spawn_row_widget.setVisible(False)
            except Exception:
                self.auto_spawn_row_widget.setVisible(False)
        else:
            self.auto_spawn_row_widget.setVisible(False)

        # --- Reset flag watcher ---
        self._stop_flag_watcher()
        self.flag_watcher_toggle.blockSignals(True)
        self.flag_watcher_toggle.setChecked(False)
        self.flag_watcher_toggle.blockSignals(False)
        self.flag_watcher_status.setText("")
    
    def _load_machine_avatar(self):
        """Cargar el avatar de la máquina."""
        if not self._machine or not self._machine.avatar:
            return
        req = QNetworkRequest(QUrl(self._machine.avatar))
        self._avatar_network.get(req)
    
    @Slot(QNetworkReply)
    def _on_machine_avatar_loaded(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            reply.deleteLater()
            return
        data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if not pixmap.isNull():
            # Escalar y redondear esquinas
            scaled = pixmap.scaled(56, 56, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            rounded = QPixmap(56, 56)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 56, 56, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, 56, 56, scaled)
            painter.end()
            self.machine_avatar.setPixmap(rounded)
            self.machine_avatar.setStyleSheet("border-radius: 10px; background: transparent;")
        reply.deleteLater()
    
    def _fetch_active_machine_ip(self):
        """Obtener máquina activa; si coincide con la actual, mostrar su IP."""
        if not self._machine:
            return
        if self._active_machine_thread and self._active_machine_thread.isRunning():
            return
        self._active_machine_thread = QThread()
        self._active_machine_worker = ActiveMachineWorker()
        self._active_machine_worker.moveToThread(self._active_machine_thread)
        self._active_machine_thread.started.connect(self._active_machine_worker.run)
        self._active_machine_worker.finished.connect(self._on_active_machine_fetched)
        self._active_machine_worker.error.connect(lambda e: debug_log("MACHINE", f"Active fetch: {e}"))
        self._active_machine_thread.start()

    @Slot(object)
    def _on_active_machine_fetched(self, active):
        self._safe_cleanup_thread(self._active_machine_thread, self._active_machine_worker)
        self._active_machine_thread = None
        self._active_machine_worker = None
        if not self._machine or not active or not active.ip:
            return
        if active.id == self._machine.id:
            self.ip_label.setText(active.ip)
            self._set_ip_display(active.ip)
            self.copy_ip_btn.setEnabled(True)

    def _update_ui(self):
        if not self._machine:
            return
        
        m = self._machine
        self.os_icon.setText(m.os_icon)
        self.name_label.setText(m.name)
        
        diff_colors = {
            "easy": DIFF_EASY, "medium": DIFF_MEDIUM,
            "hard": DIFF_HARD, "insane": DIFF_INSANE,
        }
        color = diff_colors.get(m.difficulty_text.lower(), HTB_TEXT_DIM)
        
        self.difficulty_badge.setText(m.difficulty_text)
        self.difficulty_badge.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 14px;")
        
        self.rating_label.setText(f"⭐ {m.rating:.1f}")
        self.points_label.setText(f"{m.points} pts")
        ip_text = m.ip if m.ip else ""
        self.ip_label.setText(ip_text)
        self._set_ip_display(ip_text)
        
        self.user_owns_label.setText(f"👤 {m.user_owns_count:,} user owns")
        self.root_owns_label.setText(f"💀 {m.root_owns_count:,} root owns")
    
    def _load_activity(self):
        if not self._machine:
            return
        self._cleanup_activity_thread()
        
        self._activity_thread = QThread()
        self._activity_worker = ActivityWorker(self._machine.id)
        self._activity_worker.moveToThread(self._activity_thread)
        self._activity_thread.started.connect(self._activity_worker.run)
        self._activity_worker.finished.connect(self._on_activity_loaded)
        self._activity_worker.error.connect(self._on_activity_error)
        self._activity_thread.start()
    
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

    def _cleanup_activity_thread(self):
        self._safe_cleanup_thread(self._activity_thread, self._activity_worker)
        self._activity_thread = None
        self._activity_worker = None

    def stop_background_tasks(self):
        self._activity_timer.stop()
        self._activity_countdown.stop()
        self._ip_poll_timer.stop()
        self._auto_spawn_countdown_timer.stop()
        self._flag_watcher_timer.stop()
        self._cleanup_action_thread()
        self._cleanup_activity_thread()
        self._safe_cleanup_thread(self._active_machine_thread, self._active_machine_worker)
        self._active_machine_thread = None
        self._active_machine_worker = None

    def _update_refresh_countdown(self):
        self._activity_seconds_left -= 1
        if self._activity_seconds_left <= 0:
            self._activity_seconds_left = 15
        self.refresh_indicator.setText(f"Refreshing in {self._activity_seconds_left}s")
    
    @Slot(list)
    def _on_activity_loaded(self, activity: List[dict]):
        self._cleanup_activity_thread()
        self._activity_seconds_left = 15
        self.refresh_indicator.setText("Refreshing in 15s")
        # Limpiar items anteriores
        for w in self._activity_items:
            w.deleteLater()
        self._activity_items.clear()
        while self._activity_layout.count():
            item = self._activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # Añadir nuevos
        for i, entry in enumerate(activity[:20]):
            date_diff = entry.get("date_diff", "")
            user_name = entry.get("user_name", "")
            entry_type = entry.get("type", "")  # "blood", "user", or "root"
            blood_type = entry.get("blood_type", "")  # "user" or "root" when type=="blood"
            avatar_url = entry.get("user_avatar", "") or entry.get("avatar", "")
            if avatar_url and not avatar_url.startswith("http"):
                avatar_url = f"https://labs.hackthebox.com{avatar_url}"
            row = ActivityItem(date_diff, user_name, entry_type, blood_type, avatar_url)
            self._activity_layout.addWidget(row)
            self._activity_items.append(row)
            if avatar_url:
                req = QNetworkRequest(QUrl(avatar_url))
                reply = self._network_manager.get(req)
                reply.setProperty("index", i)
    
    @Slot(QNetworkReply)
    def _on_activity_avatar_loaded(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            reply.deleteLater()
            return
        idx = reply.property("index")
        if idx is not None and 0 <= idx < len(self._activity_items):
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                self._activity_items[idx].set_avatar_pixmap(pixmap)
        reply.deleteLater()
    
    @Slot(str)
    def _on_activity_error(self, error: str):
        self._cleanup_activity_thread()
        debug_log("MACHINE", f"Activity error: {error}")
    
    def _do_action(self, action: str):
        if not self._machine:
            return
        
        if action in ["terminate", "reset"]:
            reply = QMessageBox.question(
                self, "Confirm",
                f"Are you sure you want to {action} this machine?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self._cleanup_action_thread()
        self._action_thread = QThread()
        self._action_worker = ActionWorker(action, self._machine.id)
        self._action_worker.moveToThread(self._action_thread)
        self._action_thread.started.connect(self._action_worker.run)
        self._action_worker.finished.connect(self._on_action_done)
        self._action_worker.error.connect(self._on_action_error)
        self._action_thread.start()
    
    def _submit_flag(self):
        flag = self.flag_input.text().strip()
        if not flag or not self._machine:
            return
        self._cleanup_action_thread()
        self._action_thread = QThread()
        self._action_worker = ActionWorker("flag", self._machine.id, flag)
        self._action_worker.moveToThread(self._action_thread)
        self._action_thread.started.connect(self._action_worker.run)
        self._action_worker.finished.connect(self._on_flag_result)
        self._action_worker.error.connect(self._on_action_error)
        self._action_thread.start()
    
    def _cleanup_action_thread(self):
        self._safe_cleanup_thread(self._action_thread, self._action_worker)
        self._action_thread = None
        self._action_worker = None
    
    @Slot(dict)
    def _on_action_done(self, data: dict):
        self._cleanup_action_thread()
        action = data.get("action", "")
        msg = data.get("result", {}).get("message", "Action completed successfully")
        
        if action == "spawn":
            self._starting_dots = 0
            self._animate_starting()  # Mostrar "Starting." inmediatamente
            self._starting_anim_timer.start()
            self._ip_poll_count = 0
            self._ip_poll_timer.start()
            self.copy_ip_btn.setEnabled(False)
            QMessageBox.information(self, "Success", msg + "\n\nLa IP aparecerá aquí en unos segundos.")
        elif action == "terminate":
            self.ip_label.setText("")
            self._set_ip_display("—")
            self._ip_poll_timer.stop()
            self.copy_ip_btn.setEnabled(True)
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.information(self, "Success", msg)
    
    def _poll_for_ip(self):
        """Consultar la API para obtener la IP de la máquina activa."""
        self._ip_poll_count += 1
        
        # Máximo 20 intentos (60 segundos)
        if self._ip_poll_count > 20:
            self._ip_poll_timer.stop()
            self._starting_anim_timer.stop()
            self.ip_label.setText("❌ Timeout getting IP")
            self._set_ip_display("❌ Timeout")
            self.copy_ip_btn.setEnabled(True)
            return
        
        try:
            success, result = HTBApi.get_active_machine()
            if success and result:
                from models.connection import ActiveMachine
                active = ActiveMachine.from_api(result)
                if active and active.ip:
                    self._ip_poll_timer.stop()
                    self._starting_anim_timer.stop()
                    self.ip_label.setText(active.ip)
                    self._set_ip_display(active.ip)
                    self.copy_ip_btn.setEnabled(True)
                    debug_log("MACHINE", f"Got IP: {active.ip}")
        except Exception as e:
            debug_log("MACHINE", f"Error polling IP: {e}")
    
    def _animate_starting(self):
        """Animar los puntos de 'Starting.'"""
        self._starting_dots = (self._starting_dots % 3) + 1
        dots = "." * self._starting_dots
        text = f"⏳ Starting{dots}"
        self.ip_label.setText(text)
        self._set_ip_display(text)
    
    def _set_ip_display(self, text: str):
        """Sincronizar el bloque IP de la sección de acciones."""
        self.ip_display.setText(text if text else "—")
    
    def _copy_ip_to_clipboard(self):
        """Copiar la IP de la máquina al portapapeles."""
        ip = self.ip_display.text().strip()
        if ip and ip != "—" and not ip.startswith("⏳") and not ip.startswith("❌"):
            cb = QApplication.clipboard()
            if cb:
                cb.setText(ip)
                QMessageBox.information(self, "Copied", f"IP copied: {ip}")
        elif ip and ip != "—":
            QMessageBox.information(self, "IP", "Wait for the IP to appear after spawning.")
    
    @Slot(dict)
    def _on_flag_result(self, data: dict):
        self._cleanup_action_thread()
        result = data.get("result", {})
        if result.get("success"):
            QMessageBox.information(self, "🎉 Correct!", result.get("message", "Flag accepted!"))
            self.flag_input.clear()
        else:
            QMessageBox.warning(self, "Incorrect", result.get("message", "Wrong flag"))
    
    @Slot(str)
    def _on_action_error(self, error: str):
        self._cleanup_action_thread()
        self._ip_poll_timer.stop()
        QMessageBox.warning(self, "Error", error)
    
    # =================================================================
    # AUTO-SPAWN LOGIC
    # =================================================================

    @staticmethod
    def _format_td(td) -> str:
        """Format timedelta to Xd Xh Xm Xs."""
        total = int(td.total_seconds())
        if total < 0:
            return "0s"
        d, r = divmod(total, 86400)
        h, r = divmod(r, 3600)
        m, s = divmod(r, 60)
        parts = []
        if d > 0:
            parts.append(f"{d}d")
        if h > 0:
            parts.append(f"{h}h")
        if m > 0:
            parts.append(f"{m}m")
        parts.append(f"{s}s")
        return " ".join(parts)

    def _toggle_auto_spawn(self, checked: bool):
        if checked:
            if not self._release_dt:
                self.auto_spawn_toggle.setChecked(False)
                return
            self._auto_spawn_enabled = True
            self._spawn_phase = "countdown"
            self._spawn_attempts = 0
            self.auto_spawn_status.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px; font-weight: 600;")
            self._auto_spawn_countdown_timer.start()
            debug_log("AUTO-SPAWN", f"Enabled for release: {self._release_dt.isoformat()}")
        else:
            self._stop_auto_spawn()

    def _stop_auto_spawn(self):
        self._auto_spawn_enabled = False
        self._auto_spawn_countdown_timer.stop()
        self.auto_spawn_status.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px;")

    def _auto_spawn_tick(self):
        """Called every 1 second when auto-spawn is enabled."""
        if not self._auto_spawn_enabled or not self._release_dt or not self._machine:
            return

        now = datetime.now(timezone.utc)
        remaining = (self._release_dt - now).total_seconds()

        if remaining > 10:
            # Still counting down
            self._spawn_phase = "countdown"
            td = self._release_dt - now
            self.auto_spawn_status.setText(f"\u23f3 {self._format_td(td)} until release")
        elif remaining > -60:
            # Within the spawn window: T-10s to T+60s
            if self._spawn_phase == "countdown":
                self._spawn_phase = "spawning"
                self._spawn_attempts = 0
                debug_log("AUTO-SPAWN", "Entering spawn phase")

            self._spawn_attempts += 1
            self.auto_spawn_status.setText(
                f"\U0001f680 Attempting spawn... (#{self._spawn_attempts})"
            )
            # Try spawn in thread
            self._attempt_auto_spawn()
        else:
            # Past T+60s, give up
            self.auto_spawn_status.setText("\u274c Timeout - spawn window passed")
            self._stop_auto_spawn()
            self.auto_spawn_toggle.blockSignals(True)
            self.auto_spawn_toggle.setChecked(False)
            self.auto_spawn_toggle.blockSignals(False)

    def _attempt_auto_spawn(self):
        """Try to spawn machine in a background thread."""
        try:
            success, result = HTBApi.spawn_machine(self._machine.id)
            if success:
                msg = result.get("message", "Spawned!") if isinstance(result, dict) else str(result)
                self.auto_spawn_status.setText(f"\u2705 {msg}")
                self._stop_auto_spawn()
                self.auto_spawn_toggle.blockSignals(True)
                self.auto_spawn_toggle.setChecked(False)
                self.auto_spawn_toggle.blockSignals(False)
                # Trigger IP polling
                self._starting_dots = 0
                self._animate_starting()
                self._starting_anim_timer.start()
                self._ip_poll_count = 0
                self._ip_poll_timer.start()
                debug_log("AUTO-SPAWN", f"Spawn success: {msg}")
        except Exception as e:
            debug_log("AUTO-SPAWN", f"Attempt #{self._spawn_attempts} failed: {e}")

    # =================================================================
    # FLAG WATCHER LOGIC
    # =================================================================

    _FLAG_PATTERN = re.compile(r'^[a-fA-F0-9]{32}$')

    def _toggle_flag_watcher(self, checked: bool):
        if checked:
            self._flag_watcher_enabled = True
            self._last_submitted_flag = ""
            self._flag_watcher_timer.start()
            self.flag_watcher_status.setText("\U0001f441 Watching clipboard...")
            self.flag_watcher_status.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px; font-weight: 600;")
            debug_log("FLAG-WATCHER", "Started")
        else:
            self._stop_flag_watcher()

    def _stop_flag_watcher(self):
        self._flag_watcher_enabled = False
        self._flag_watcher_timer.stop()
        self.flag_watcher_status.setText("")
        self.flag_watcher_status.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px;")

    def _flag_watcher_tick(self):
        """Check clipboard for MD5-like flag every 2 seconds."""
        if not self._flag_watcher_enabled or not self._machine or self._flag_submitting:
            return

        cb = QApplication.clipboard()
        if not cb:
            return
        text = cb.text().strip()
        if not text or text == self._last_submitted_flag:
            return

        if self._FLAG_PATTERN.match(text):
            self._last_submitted_flag = text
            self._flag_submitting = True
            short = text[:8] + "..."
            self.flag_watcher_status.setText(f"\U0001f4e4 Submitting {short}")
            debug_log("FLAG-WATCHER", f"Detected flag: {text}")

            try:
                success, result = HTBApi.submit_flag(self._machine.id, text)
                if success and isinstance(result, dict) and result.get("success"):
                    msg = result.get("message", "Flag accepted!")
                    self.flag_watcher_status.setText(f"\u2705 {msg}")
                    self.flag_input.setText(text)
                    debug_log("FLAG-WATCHER", f"Flag accepted: {msg}")
                else:
                    err = result.get("message", str(result)) if isinstance(result, dict) else str(result)
                    self.flag_watcher_status.setText(f"\u274c {err}")
                    debug_log("FLAG-WATCHER", f"Flag rejected: {err}")
            except Exception as e:
                self.flag_watcher_status.setText(f"\u274c Error: {e}")
                debug_log("FLAG-WATCHER", f"Error: {e}")
            finally:
                self._flag_submitting = False

    def hideEvent(self, event):
        super().hideEvent(event)
        self._activity_timer.stop()
        self._activity_countdown.stop()
        self._ip_poll_timer.stop()
        self._auto_spawn_countdown_timer.stop()
        self._flag_watcher_timer.stop()
        self._cleanup_action_thread()
        self._cleanup_activity_thread()
        if self._active_machine_thread and self._active_machine_thread.isRunning():
            self._active_machine_thread.quit()
            self._active_machine_thread.wait(2000)
        self._active_machine_thread = None
        self._active_machine_worker = None
