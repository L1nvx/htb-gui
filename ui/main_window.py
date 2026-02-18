"""Main application window."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QStatusBar, QLabel, QSizeGrip
)
from PySide6.QtCore import Qt, Slot, QSize, QPoint
from PySide6.QtGui import QCloseEvent, QColor, QPalette

from config import config
from ui.styles import GLOBAL_STYLE, HTB_GREEN, HTB_TEXT_MUTED, HTB_BG_DARKEST
from ui.top_nav import TopNav
from ui.widgets.title_bar import TitleBar
from ui.pages import (
    DashboardPage, MachinesPage, MachineDetailPage,
    SeasonsPage, ToolkitPage, VPNPage, SettingsPage
)
from ui.widgets.fade_stack import FadeStackWidget
from utils.debug import debug_log


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.drag_pos = None
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        debug_log("UI", "MainWindow initialized")

    def closeEvent(self, event: QCloseEvent):
        """Stop threads before closing."""
        pages_with_threads = [
            self.dashboard,
            self.machines,
            self.machine_detail,
            self.seasons,
            self.vpn,
        ]
        for page in pages_with_threads:
            if hasattr(page, "stop_background_tasks"):
                page.stop_background_tasks()
        event.accept()
    
    def _setup_window(self):
        self.setWindowTitle("HackTheBox Client")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        # Frameless Window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(GLOBAL_STYLE)
    
    def _setup_ui(self):
        # We need a central widget that acts as the real window background
        # because the main window is transparent to allow for rounded corners if desired
        central = QWidget()
        central.setObjectName("CentralWidget")
        central.setStyleSheet(f"""
            QWidget#CentralWidget {{
                background-color: {HTB_BG_DARKEST};
                border: 1px solid #333;
                border-radius: 10px;
            }}
        """)
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Custom Title Bar
        self.title_bar = TitleBar(self)
        layout.addWidget(self.title_bar)

        # Top navigation
        self.top_nav = TopNav()
        layout.addWidget(self.top_nav)
        
        # Content Area
        # Content Area
        self.stack = FadeStackWidget()
        layout.addWidget(self.stack)
        
        # Create pages
        self.dashboard = DashboardPage()
        
        # Initialize other pages (placeholders for now to match imports)
        self.machines = MachinesPage()
        self.machine_detail = MachineDetailPage()
        self.seasons = SeasonsPage()
        self.toolkit = ToolkitPage()
        self.vpn = VPNPage()
        self.settings = SettingsPage()
        
        # Add to stack
        self.pages = {
            "dashboard": self.dashboard,
            "machines": self.machines,
            "machine_detail": self.machine_detail,
            "seasons": self.seasons,
            "toolkit": self.toolkit,
            "vpn": self.vpn,
            "settings": self.settings,
        }
        
        for page in self.pages.values():
            self.stack.addWidget(page)
        
        # Status bar implementation (custom at bottom of central widget)
        self.status_bar = QWidget()
        self.status_bar.setFixedHeight(24)
        self.status_bar.setStyleSheet(f"background-color: {HTB_BG_DARKEST}; border-top: 1px solid #222;")
        sb_layout = QHBoxLayout(self.status_bar)
        sb_layout.setContentsMargins(10, 0, 10, 0)
        
        self.connection_label = QLabel("🔴 Not connected")
        self.connection_label.setStyleSheet(f"color: {HTB_TEXT_MUTED}; font-size: 11px;")
        sb_layout.addStretch()
        sb_layout.addWidget(self.connection_label)
        
        # Size Grip for resizing
        self.size_grip = QSizeGrip(self.status_bar)
        sb_layout.addWidget(self.size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        
        layout.addWidget(self.status_bar)

    def _connect_signals(self):
        self.top_nav.page_changed.connect(self._on_page_changed)
        
        # Machine selection
        self.machines.machine_selected.connect(self._on_machine_selected)
        self.seasons.machine_selected.connect(self._on_machine_selected)
        
        # Machine detail back button
        self.machine_detail.back_clicked.connect(
            lambda: self._on_page_changed("machines"))
        
        # Settings token changed
        self.settings.token_changed.connect(self._on_token_changed)
    
    @Slot(str)
    def _on_page_changed(self, page_id: str):
        debug_log("UI", f"Page changed: {page_id}")
        if page_id in self.pages:
            self.stack.setCurrentWidget(self.pages[page_id])
            self.top_nav.set_active(page_id)
    
    @Slot(object)
    def _on_machine_selected(self, machine):
        debug_log("UI", f"Machine selected: {machine.name}")
        self.machine_detail.set_machine(machine)
        self.stack.setCurrentWidget(self.machine_detail)
        self.top_nav.set_active("machines")
    
    @Slot()
    def _on_token_changed(self):
        debug_log("UI", "Token changed, refreshing...")
        
        if config.is_configured():
            self.connection_label.setText(f"🟢 Configured")
            self.connection_label.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px;")
        
        # Refresh dashboard
        self.dashboard.load_data()
