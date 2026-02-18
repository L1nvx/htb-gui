"""Dashboard Page - Modern UI."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QScrollArea, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject, QUrl, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from typing import Optional, List

from api.endpoints import HTBApi
from models.user import User
from models.connection import ActiveMachine, Connection
from ui.styles import (
    HTB_GREEN, HTB_TEXT_DIM, HTB_TEXT_MAIN, HTB_TEXT_SEC, FONT_FAMILY_MONO
)
from ui.widgets.activity_item import ActivityItem
from ui.widgets.modern_widgets import (
    ModernButton, ModernCard, SimpleStatCard, ModernInput
)
from utils.debug import debug_log
import qtawesome as qta


class DashboardWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def run(self):
        debug_log("DASHBOARD", "Loading data...")
        data = {}
        try:
            success, result = HTBApi.get_user_info()
            if success and isinstance(result, dict):
                data["user"] = User.from_api(result)
            
            success, result = HTBApi.get_active_machine()
            if success and isinstance(result, dict):
                data["active_machine"] = ActiveMachine.from_api(result)
            
            success, result = HTBApi.get_connection_status()
            if success and isinstance(result, list) and len(result) > 0:
                data["connection"] = Connection.from_api(result[0])
            
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class DashboardActionWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, action: str, machine_id: int, flag: str = ""):
        super().__init__()
        self.action = action
        self.machine_id = machine_id
        self.flag = flag
    
    def run(self):
        try:
            if self.action == "terminate":
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


class DashboardActivityWorker(QObject):
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
                self.finished.emit(info.get("activity", []))
            else:
                self.error.emit(str(result) if not success else "Invalid response")
        except Exception as e:
            self.error.emit(str(e))


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None
        self._loading = False
        self._active_machine_id: Optional[int] = None
        self._active_machine_avatar: str = ""
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_avatar_loaded)
        self._activity_network = QNetworkAccessManager(self)
        self._activity_network.finished.connect(self._on_activity_avatar_loaded)
        self._machine_avatar_network = QNetworkAccessManager(self)
        self._machine_avatar_network.finished.connect(self._on_machine_avatar_loaded)
        self._activity_thread = None
        self._activity_worker = None
        self._action_thread = None
        self._action_worker = None
        self._activity_timer = QTimer(self)
        self._activity_timer.setInterval(15000)
        self._activity_timer.timeout.connect(self._load_activity)
        self._activity_countdown = QTimer(self)
        self._activity_countdown.setInterval(1000)
        self._activity_countdown.timeout.connect(self._update_activity_countdown)
        self._activity_seconds_left = 15
        self._activity_items: List[ActivityItem] = []
        self._zombie_threads: List[QThread] = [] # Keep threads alive until they finish
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)
        
        # Welcome Header
        self.welcome_label = QLabel("Welcome back!")
        self.welcome_label.setStyleSheet(f"font-size: 32px; font-weight: 800; letter-spacing: -1px; color: {HTB_TEXT_MAIN};")
        layout.addWidget(self.welcome_label)
        
        # Stats Grid
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        # User Card
        self.user_card = self._create_user_card()
        stats_layout.addWidget(self.user_card)
        
        # Sub Card
        self.sub_card = SimpleStatCard("Subscription", "-", "fa5s.crown", HTB_GREEN)
        stats_layout.addWidget(self.sub_card)
        
        # Rank Card
        self.rank_card = SimpleStatCard("Server", "-", "fa5s.server", HTB_GREEN)
        stats_layout.addWidget(self.rank_card)
        
        layout.addLayout(stats_layout)
        
        # Active Machine Section
        section1 = QLabel("ACTIVE OPERATION")
        section1.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; margin-top: 10px;")
        layout.addWidget(section1)
        
        self.machine_card = ModernCard()
        machine_layout = QVBoxLayout(self.machine_card)
        machine_layout.setContentsMargins(30, 25, 30, 25)
        machine_layout.setSpacing(15)
        
        # Top Row: Avatar + Info + IP
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        
        self.machine_avatar = QLabel()
        self.machine_avatar.setFixedSize(60, 60)
        self.machine_avatar.setStyleSheet("background-color: #1a2638; border-radius: 12px;")
        self.machine_avatar.setAlignment(Qt.AlignCenter)
        self.machine_avatar.setVisible(False)
        top_row.addWidget(self.machine_avatar)
        
        info_col = QVBoxLayout()
        info_col.setSpacing(5)
        
        self.machine_name = QLabel("No active machine")
        self.machine_name.setStyleSheet("font-size: 22px; font-weight: 700;")
        info_col.addWidget(self.machine_name)
        
        self.machine_info = QLabel("Spawn a machine to start hacking")
        self.machine_info.setStyleSheet(f"color: {HTB_TEXT_SEC}; font-size: 14px;")
        self.machine_info.setWordWrap(True)
        info_col.addWidget(self.machine_info)
        
        top_row.addLayout(info_col)
        top_row.addStretch()
        
        # IP Display
        self.machine_ip = QLabel("")
        self.machine_ip.setStyleSheet(f"color: {HTB_GREEN}; font-size: 18px; font-weight: 700; font-family: {FONT_FAMILY_MONO};")
        top_row.addWidget(self.machine_ip)
        
        self.copy_ip_btn = ModernButton("", "fa5s.copy", "ghost")
        self.copy_ip_btn.setToolTip("Copy IP")
        self.copy_ip_btn.setFixedSize(40, 40)
        self.copy_ip_btn.clicked.connect(self._copy_ip_to_clipboard)
        self.copy_ip_btn.setVisible(False)
        top_row.addWidget(self.copy_ip_btn)
        
        machine_layout.addLayout(top_row)
        
        # Actions Area
        self.actions_widget = QWidget()
        actions_layout = QVBoxLayout(self.actions_widget)
        actions_layout.setContentsMargins(0, 15, 0, 0)
        actions_layout.setSpacing(15)
        
        # Buttons Row
        btns_row = QHBoxLayout()
        self.stop_btn = ModernButton("Stop Machine", "fa5s.stop", "danger")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        btns_row.addWidget(self.stop_btn)
        
        self.reset_btn = ModernButton("Reset", "fa5s.redo", "ghost")
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        btns_row.addWidget(self.reset_btn)
        
        btns_row.addStretch()
        actions_layout.addLayout(btns_row)
        
        # Flag Input Row
        flag_row = QHBoxLayout()
        self.flag_input = ModernInput("Enter flag hash...")
        flag_row.addWidget(self.flag_input)
        
        self.submit_flag_btn = ModernButton("Submit Flag", "fa5s.flag", "primary")
        self.submit_flag_btn.clicked.connect(self._on_submit_flag_clicked)
        flag_row.addWidget(self.submit_flag_btn)
        
        actions_layout.addLayout(flag_row)
        
        machine_layout.addWidget(self.actions_widget)
        self.actions_widget.setVisible(False)
        
        layout.addWidget(self.machine_card)
        
        # Activity Section (Collapsible/Conditional)
        activity_title_row = QHBoxLayout()
        activity_title_row.setContentsMargins(0, 10, 0, 0)
        self.activity_header = QLabel("RECENT ACTIVITY")
        self.activity_header.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 800; letter-spacing: 1.5px;")
        activity_title_row.addWidget(self.activity_header)
        
        activity_title_row.addStretch()
        self.activity_refresh_label = QLabel("Refreshing in 15s")
        self.activity_refresh_label.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px; font-weight: 600;")
        activity_title_row.addWidget(self.activity_refresh_label)
        
        layout.addLayout(activity_title_row)
        
        self.activity_scroll = QScrollArea()
        self.activity_scroll.setWidgetResizable(True)
        self._activity_container = QWidget()
        self._activity_layout = QVBoxLayout(self._activity_container)
        self._activity_layout.setContentsMargins(0, 0, 10, 0)
        self._activity_layout.setSpacing(8)
        self._activity_layout.setAlignment(Qt.AlignTop)
        self.activity_scroll.setWidget(self._activity_container)
        self.activity_scroll.setMinimumHeight(200)
        layout.addWidget(self.activity_scroll)
        
        self.activity_header.setVisible(False)
        self.activity_refresh_label.setVisible(False)
        self.activity_scroll.setVisible(False)
        
        layout.addStretch()

    def _create_user_card(self) -> ModernCard:
        card = ModernCard()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(50, 50)
        self.avatar_label.setStyleSheet("background-color: #1a2638; border-radius: 25px;")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.avatar_label)
        
        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        
        lbl = QLabel("USERNAME")
        lbl.setStyleSheet(f"color: {HTB_TEXT_SEC}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        vbox.addWidget(lbl)
        
        self.username_label = QLabel("-")
        self.username_label.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {HTB_GREEN};")
        vbox.addWidget(self.username_label)
        
        layout.addLayout(vbox)
        layout.addStretch()
        return card

    def _load_avatar(self, avatar_url: str):
        if not avatar_url: return
        request = QNetworkRequest(QUrl(avatar_url))
        self._network_manager.get(request)
    
    def _set_avatar_placeholder(self, username: str):
        initial = (username.strip() or "?")[0].upper()
        self.avatar_label.setText(initial)
        self.avatar_label.setPixmap(QPixmap())
        self.avatar_label.setStyleSheet(
            f"background-color: #1a2638; border-radius: 25px; color: {HTB_GREEN}; font-weight: 700; font-size: 20px;"
        )

    @Slot(QNetworkReply)
    def _on_avatar_loaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                scaled = pixmap.scaled(50, 50, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                # Circular mask
                circular = QPixmap(50, 50)
                circular.fill(Qt.transparent)
                from PySide6.QtGui import QPainter, QPainterPath
                painter = QPainter(circular)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, 50, 50)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                
                self.avatar_label.setPixmap(circular)
                self.avatar_label.setText("")
                self.avatar_label.setStyleSheet("background: transparent;")
        reply.deleteLater()
    
    def _update_card(self, card: ModernCard, value: str):
        if hasattr(card, "set_value"):
            card.set_value(value)
    
    def load_data(self):
        if self._loading: return
        self._loading = True
        self._cleanup_thread()
        
        self._thread = QThread()
        self._worker = DashboardWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_loaded)
        self._worker.error.connect(self._on_error)
        self._thread.start()
    
    def _safe_cleanup_thread(self, thread: QThread, worker: QObject):
        """
        Safely cleanup a thread. If it's running, detach it and let it finish (zombie).
        We disconnect signals so it doesn't try to update the UI of a potentially hidden/destroyed page.
        """
        if not thread:
            return
            
        # 1. Disconnect all signals from worker to prevent UI updates
        if worker:
            try: worker.disconnect()
            except: pass
        
        # 2. Check if running
        if thread.isRunning():
            # It's stuck (maybe in API retry loop). 
            # We can't force kill it without risk of crash/leak.
            # We move it to zombies and let it die when it finishes (if ever).
            self._zombie_threads.append(thread)
            
            # When finished, remove from zombies and delete
            # We use a lambda with default arg to capture the specific thread instance
            thread.finished.connect(lambda t=thread: self._on_zombie_finished(t))
            
            # Advise it to quit (in case it enters event loop)
            thread.quit()
        else:
            # Not running, just delete
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
        self._loading = False
        self._activity_timer.stop()
        self._activity_countdown.stop()
        self._cleanup_thread()
        self._cleanup_activity_thread()
        self._cleanup_action_thread()

    def _cleanup_activity_thread(self):
        self._safe_cleanup_thread(self._activity_thread, self._activity_worker)
        self._activity_thread = None
        self._activity_worker = None

    def _cleanup_action_thread(self):
        self._safe_cleanup_thread(self._action_thread, self._action_worker)
        self._action_thread = None
        self._action_worker = None

    def _copy_ip_to_clipboard(self):
        ip = self.machine_ip.text().strip()
        if ip and not ip.startswith("Joining"):
            cb = QApplication.clipboard()
            if cb:
                cb.setText(ip)
                QMessageBox.information(self, "Copied", f"IP copied: {ip}")
    
    def _update_activity_countdown(self):
        self._activity_seconds_left -= 1
        if self._activity_seconds_left <= 0:
            self._activity_seconds_left = 15
        self.activity_refresh_label.setText(f"Refreshing in {self._activity_seconds_left}s")

    def _load_activity(self):
        if not self._active_machine_id: return
        self._cleanup_activity_thread()
        self._activity_seconds_left = 15
        self.activity_refresh_label.setText("Refreshing in 15s")
        self._activity_thread = QThread()
        self._activity_worker = DashboardActivityWorker(self._active_machine_id)
        self._activity_worker.moveToThread(self._activity_thread)
        self._activity_thread.started.connect(self._activity_worker.run)
        self._activity_worker.finished.connect(self._on_activity_loaded)
        self._activity_worker.error.connect(lambda e: self._cleanup_activity_thread())
        self._activity_thread.start()

    @Slot(list)
    def _on_activity_loaded(self, activity: List[dict]):
        self._cleanup_activity_thread()
        self._activity_seconds_left = 15
        self.activity_refresh_label.setText("Refreshing in 15s")
        for w in self._activity_items:
            w.deleteLater()
        self._activity_items.clear()
        
        # Clear layout safely
        while self._activity_layout.count():
            item = self._activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, entry in enumerate(activity[:15]):
            date_diff = entry.get("date_diff", "")
            user_name = entry.get("user_name", "")
            entry_type = entry.get("type", "")
            blood_type = entry.get("blood_type", "")
            avatar_url = entry.get("user_avatar", "") or entry.get("avatar", "")
            if avatar_url and not avatar_url.startswith("http"):
                avatar_url = f"https://labs.hackthebox.com{avatar_url}"
            row = ActivityItem(date_diff, user_name, entry_type, blood_type, avatar_url)
            self._activity_layout.addWidget(row)
            self._activity_items.append(row)
            if avatar_url:
                req = QNetworkRequest(QUrl(avatar_url))
                reply = self._activity_network.get(req)
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

    @Slot(QNetworkReply)
    def _on_machine_avatar_loaded(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            reply.deleteLater()
            return
        data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if not pixmap.isNull():
            from PySide6.QtGui import QPainter, QPainterPath
            scaled = pixmap.scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            rounded = QPixmap(60, 60)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 60, 60, 12, 12)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled)
            painter.end()
            self.machine_avatar.setPixmap(rounded)
            self.machine_avatar.setStyleSheet("background: transparent;")
        reply.deleteLater()

    def _on_stop_clicked(self):
        if not self._active_machine_id: return
        r = QMessageBox.question(
            self, "Confirm", "Stop this machine?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r != QMessageBox.Yes: return
        self._run_action("terminate")

    def _on_reset_clicked(self):
        if not self._active_machine_id: return
        r = QMessageBox.question(
            self, "Confirm", "Reset this machine?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r != QMessageBox.Yes: return
        self._run_action("reset")

    def _on_submit_flag_clicked(self):
        if not self._active_machine_id: return
        flag = self.flag_input.text().strip()
        if not flag:
            QMessageBox.warning(self, "Flag", "Enter a flag.")
            return
        self._run_action("flag", flag)

    def _run_action(self, action: str, flag: str = ""):
        self._cleanup_action_thread()
        self._action_thread = QThread()
        self._action_worker = DashboardActionWorker(action, self._active_machine_id, flag)
        self._action_worker.moveToThread(self._action_thread)
        self._action_thread.started.connect(self._action_worker.run)
        self._action_worker.finished.connect(self._on_action_done)
        self._action_worker.error.connect(self._on_action_error)
        self._action_thread.start()

    @Slot(dict)
    def _on_action_done(self, data: dict):
        self._cleanup_action_thread()
        action = data.get("action", "")
        msg = data.get("result", {}).get("message", "Action successful.")
        if action == "terminate":
            self._active_machine_id = None
            self.machine_name.setText("No active machine")
            self.machine_info.setText("Spawn a machine to start hacking")
            self.machine_ip.setText("")
            self.copy_ip_btn.setVisible(False)
            self.actions_widget.setVisible(False)
            self.activity_header.setVisible(False)
            self.activity_refresh_label.setVisible(False)
            self.activity_scroll.setVisible(False)
            self._activity_timer.stop()
            self._activity_countdown.stop()
        if action == "flag":
            self.flag_input.clear()
        QMessageBox.information(self, "Success", msg)

    @Slot(str)
    def _on_action_error(self, error: str):
        self._cleanup_action_thread()
        QMessageBox.warning(self, "Error", error)
    
    @Slot(dict)
    def _on_loaded(self, data: dict):
        self._loading = False
        self._cleanup_thread()
        
        if "user" in data:
            u = data["user"]
            self.welcome_label.setText(f"Welcome back, {u.name}!")
            self.username_label.setText(u.name)
            self._update_card(self.sub_card, u.subscription_display)
            self._update_card(self.rank_card, f"Server {u.server_id}")
            if u.avatar_url:
                self._load_avatar(u.avatar_url)
            else:
                self._set_avatar_placeholder(u.name)
        
        if "active_machine" in data and data["active_machine"]:
            m = data["active_machine"]
            self._active_machine_id = m.id
            self.machine_name.setText(m.name)
            self.machine_info.setText(m.status_text)
            ip_text = m.ip if m.ip else "Joining..."
            self.machine_ip.setText(ip_text)
            self.copy_ip_btn.setVisible(bool(m.ip))
            self.actions_widget.setVisible(True)
            self.activity_header.setVisible(True)
            self.activity_refresh_label.setVisible(True)
            self.activity_scroll.setVisible(True)
            self._activity_seconds_left = 15
            self.activity_refresh_label.setText("Refreshing in 15s")
            self._load_activity()
            self._activity_timer.start()
            self._activity_countdown.start()
            
            if m.avatar:
                self._active_machine_avatar = m.avatar
                self.machine_avatar.setVisible(True)
                req = QNetworkRequest(QUrl(m.avatar))
                self._machine_avatar_network.get(req)
            else:
                self.machine_avatar.setVisible(False)
        else:
            self._active_machine_id = None
            self.machine_name.setText("No active machine")
            self.machine_info.setText("Spawn a machine to start hacking")
            self.machine_ip.setText("")
            self.copy_ip_btn.setVisible(False)
            self.actions_widget.setVisible(False)
            self.activity_header.setVisible(False)
            self.activity_refresh_label.setVisible(False)
            self.activity_scroll.setVisible(False)
            self.machine_avatar.setVisible(False)
            self._activity_timer.stop()
            self._activity_countdown.stop()
    
    @Slot(str)
    def _on_error(self, error: str):
        self._loading = False
        self._cleanup_thread()
        
    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self._activity_timer.stop()
        self._activity_countdown.stop()
        self._cleanup_thread()
        self._cleanup_activity_thread()
        self._cleanup_action_thread()
