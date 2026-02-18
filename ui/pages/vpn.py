"""VPN Page - Borderless HTB Style."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QFrame, QMessageBox, QFileDialog, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject

from api.endpoints import HTBApi
from models.connection import Connection
from ui.styles import HTB_GREEN, HTB_BG_CARD, HTB_BG_MAIN, HTB_TEXT_DIM
from ui.widgets.modern_widgets import ModernButton
from utils.debug import debug_log


class VPNWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def run(self):
        data = {}
        try:
            success, result = HTBApi.get_connection_status()
            if success and isinstance(result, list) and len(result) > 0:
                data["connection"] = Connection.from_api(result[0])
            
            success, result = HTBApi.get_vpn_servers("competitive")
            if success:
                data["servers"] = result
            
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class VPNPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._servers = {}
        self._thread = None
        self._worker = None
        self._loading = False
        self._loaded = False
        self._zombie_threads: List[QThread] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)
        
        # Header
        title = QLabel("VPN Connection")
        title.setStyleSheet("font-size: 28px; font-weight: 700; letter-spacing: -0.5px;")
        layout.addWidget(title)
        
        # Status
        section1 = QLabel("CONNECTION STATUS")
        section1.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(section1)
        
        status_frame = QFrame()
        status_frame.setStyleSheet(f"background-color: {HTB_BG_CARD}; border-radius: 12px;")
        status_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(24, 20, 24, 20)
        
        self.status_icon = QLabel("🔴")
        self.status_icon.setStyleSheet("font-size: 32px;")
        status_layout.addWidget(self.status_icon)
        
        status_info = QVBoxLayout()
        status_info.setSpacing(2)
        
        self.status_text = QLabel("Disconnected")
        self.status_text.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.status_text.setWordWrap(True)
        status_info.addWidget(self.status_text)
        
        self.status_details = QLabel("Connect using your VPN client")
        self.status_details.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 14px;")
        self.status_details.setWordWrap(True)
        status_info.addWidget(self.status_details)
        
        status_layout.addLayout(status_info)
        status_layout.addStretch()
        
        refresh_btn = ModernButton(" Refresh", "fa5s.sync-alt", "ghost")
        refresh_btn.clicked.connect(self._force_reload)
        status_layout.addWidget(refresh_btn)
        
        layout.addWidget(status_frame)
        
        # Download
        section2 = QLabel("DOWNLOAD CONFIG")
        section2.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(section2)
        
        dl_frame = QFrame()
        dl_frame.setStyleSheet(f"background-color: {HTB_BG_MAIN}; border-radius: 12px;")
        dl_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        dl_layout = QVBoxLayout(dl_frame)
        dl_layout.setContentsMargins(24, 20, 24, 20)
        dl_layout.setSpacing(16)
        
        # Row 1
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        
        region_lbl = QLabel("Region:")
        region_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM};")
        row1.addWidget(region_lbl)
        
        self.region_combo = QComboBox()
        self.region_combo.addItems(["EU", "US", "AU", "SG"])
        self.region_combo.currentTextChanged.connect(self._update_servers)
        row1.addWidget(self.region_combo)
        
        row1.addSpacing(24)
        
        proto_lbl = QLabel("Protocol:")
        proto_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM};")
        row1.addWidget(proto_lbl)
        
        self.proto_combo = QComboBox()
        self.proto_combo.addItems(["UDP", "TCP"])
        row1.addWidget(self.proto_combo)
        
        row1.addStretch()
        dl_layout.addLayout(row1)
        
        # Row 2
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        
        server_lbl = QLabel("Server:")
        server_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM};")
        row2.addWidget(server_lbl)
        
        self.server_combo = QComboBox()
        self.server_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row2.addWidget(self.server_combo)
        
        dl_layout.addLayout(row2)
        
        # Download button
        dl_btn = ModernButton(" Download .ovpn File", "fa5s.download", "secondary")
        dl_btn.clicked.connect(self._download)
        dl_layout.addWidget(dl_btn, alignment=Qt.AlignLeft)
        
        layout.addWidget(dl_frame)
        
        # Help
        help_text = QLabel("💡 Import the downloaded .ovpn file into OpenVPN or another VPN client to connect.")
        help_text.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        layout.addStretch()
    
    def _force_reload(self):
        self._loaded = False
        self.load_data()
    
    def load_data(self):
        if self._loading:
            return
        self._loading = True
        self._cleanup_thread()
        
        self._thread = QThread()
        self._worker = VPNWorker()
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
    
    @Slot(dict)
    def _on_loaded(self, data: dict):
        self._loading = False
        self._loaded = True
        self._cleanup_thread()
        
        if "connection" in data and data["connection"]:
            c = data["connection"]
            self.status_icon.setText("🟢")
            self.status_text.setText(f"Connected to {c.server_friendly_name}")
            self.status_details.setText(f"Your IP: {c.ip_display}")
        else:
            self.status_icon.setText("🔴")
            self.status_text.setText("Disconnected")
            self.status_details.setText("Connect using your VPN client")
        
        if "servers" in data:
            self._servers = data["servers"].get("data", {}).get("options", {})
            self._update_servers()
    
    @Slot(str)
    def _on_error(self, error: str):
        self._loading = False
        self._cleanup_thread()
        debug_log("VPN", f"Error: {error}")
    
    def _update_servers(self):
        region = self.region_combo.currentText()
        self.server_combo.clear()
        
        if region in self._servers:
            for arena_data in self._servers[region].values():
                for sid, server in arena_data.get("servers", {}).items():
                    status = "🟢" if not server.get("full") else "🔴"
                    clients = server.get("current_clients", 0)
                    name = server.get("friendly_name", f"Server {sid}")
                    self.server_combo.addItem(f"{status} {name} ({clients} users)", int(sid))
    
    def _download(self):
        server_id = self.server_combo.currentData()
        if not server_id:
            QMessageBox.warning(self, "Error", "Please select a server first")
            return
        
        # IMPORTANT: Switch to the server BEFORE downloading the VPN file
        # Without this, the machine will be on a different IP and unreachable,
        # and flags will be considered invalid
        switch_success, switch_result = HTBApi.switch_server(server_id)
        if not switch_success:
            QMessageBox.warning(
                self, "Error", 
                f"Failed to switch to server: {switch_result}\n\n"
                "The VPN file will not work correctly without switching servers first."
            )
            return
        
        tcp = 1 if self.proto_combo.currentText() == "TCP" else 0
        success, result = HTBApi.download_vpn_file(server_id, 0, tcp)
        
        if not success:
            QMessageBox.warning(self, "Error", str(result))
            return
        if not isinstance(result, bytes) or len(result) < 100:
            QMessageBox.warning(self, "Error", "Respuesta inválida del servidor (¿rate limit?). Intenta de nuevo.")
            return
        # No guardar HTML (ej. página de error 429)
        if result.lstrip()[:1] == b"<":
            QMessageBox.warning(self, "Error", "El servidor devolvió una página de error. Espera unos segundos (rate limit) e intenta de nuevo.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save VPN Configuration",
            "htb_vpn.ovpn",
            "OpenVPN Files (*.ovpn)"
        )
        if filename:
            with open(filename, 'wb') as f:
                f.write(result)
            QMessageBox.information(self, "Success", f"Configuration saved to:\n{filename}")
    
    def showEvent(self, event):
        super().showEvent(event)
        if not self._loaded and not self._loading:
            self.load_data()
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self._cleanup_thread()
