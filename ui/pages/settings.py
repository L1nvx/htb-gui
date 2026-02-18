"""Settings Page - Borderless HTB Style."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QCheckBox, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from config import config
from api.endpoints import HTBApi
from ui.styles import HTB_GREEN, HTB_BG_CARD, HTB_BG_MAIN, HTB_TEXT_DIM, BTN_PRIMARY, BTN_DEFAULT
from ui.widgets.modern_widgets import ModernButton
from utils.debug import debug_log


class SettingsPage(QWidget):
    token_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)
        
        # Header
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 28px; font-weight: 700; letter-spacing: -0.5px;")
        layout.addWidget(title)
        
        # API Token
        section1 = QLabel("API TOKEN")
        section1.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(section1)
        
        token_frame = QFrame()
        token_frame.setStyleSheet(f"background-color: {HTB_BG_MAIN}; border-radius: 12px;")
        token_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        token_layout = QVBoxLayout(token_frame)
        token_layout.setContentsMargins(24, 20, 24, 20)
        token_layout.setSpacing(16)
        
        help_lbl = QLabel("Enter your HackTheBox API token to connect to the platform.")
        help_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 14px;")
        help_lbl.setWordWrap(True)
        token_layout.addWidget(help_lbl)
        
        link_lbl = QLabel(f"<a href='https://app.hackthebox.com/profile/settings' style='color: {HTB_GREEN}; text-decoration: none;'>Get your token from hackthebox.com →</a>")
        link_lbl.setOpenExternalLinks(True)
        link_lbl.setStyleSheet("font-size: 13px;")
        token_layout.addWidget(link_lbl)
        
        # Input
        input_row = QHBoxLayout()
        input_row.setSpacing(12)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Paste your API token here...")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setText(config.api_token)
        self.token_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        input_row.addWidget(self.token_input)
        
        show_btn = ModernButton("Show", btn_type="secondary")
        show_btn.setCheckable(True)
        show_btn.toggled.connect(lambda c: (
            self.token_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password),
            show_btn.setText("Hide" if c else "Show")
        ))
        input_row.addWidget(show_btn)
        
        token_layout.addLayout(input_row)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        
        save_btn = ModernButton("💾 Save Token", btn_type="secondary")
        save_btn.clicked.connect(self._save_token)
        btn_row.addWidget(save_btn)
        
        test_btn = ModernButton("🔗 Test Connection", btn_type="secondary")
        test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(test_btn)
        
        btn_row.addStretch()
        token_layout.addLayout(btn_row)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        self.status_label.setWordWrap(True)
        token_layout.addWidget(self.status_label)
        
        layout.addWidget(token_frame)
        
        # Debug
        section2 = QLabel("DEBUG")
        section2.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(section2)
        
        debug_frame = QFrame()
        debug_frame.setStyleSheet(f"background-color: {HTB_BG_MAIN}; border-radius: 12px;")
        debug_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        debug_layout = QVBoxLayout(debug_frame)
        debug_layout.setContentsMargins(24, 20, 24, 20)
        debug_layout.setSpacing(12)
        
        self.debug_check = QCheckBox("Enable debug logging")
        self.debug_check.setChecked(config.debug)
        self.debug_check.toggled.connect(self._toggle_debug)
        debug_layout.addWidget(self.debug_check)
        
        debug_info = QLabel("Debug output will appear in your terminal when running the application.")
        debug_info.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        debug_info.setWordWrap(True)
        debug_layout.addWidget(debug_info)
        
        layout.addWidget(debug_frame)
        
        # About
        section3 = QLabel("ABOUT")
        section3.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(section3)
        
        about_frame = QFrame()
        about_frame.setStyleSheet(f"background-color: {HTB_BG_MAIN}; border-radius: 12px;")
        about_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        about_layout = QVBoxLayout(about_frame)
        about_layout.setContentsMargins(24, 20, 24, 20)
        about_layout.setSpacing(4)
        
        name_lbl = QLabel("HTB Desktop Client")
        name_lbl.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {HTB_GREEN};")
        about_layout.addWidget(name_lbl)
        
        version_lbl = QLabel("Version 1.0.0 • Built with PySide6 and Python")
        version_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        version_lbl.setWordWrap(True)
        about_layout.addWidget(version_lbl)
        
        layout.addWidget(about_frame)
        layout.addStretch()
    
    def _save_token(self):
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Error", "Please enter a token")
            return
        
        config.api_token = token
        self.status_label.setText("✓ Token saved successfully!")
        self.status_label.setStyleSheet(f"color: {HTB_GREEN}; font-size: 13px;")
        self.token_changed.emit()
    
    def _test_connection(self):
        self.status_label.setText("Testing connection...")
        self.status_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 13px;")
        
        success, result = HTBApi.get_user_info()
        
        if success:
            name = result.get("info", {}).get("name", "Unknown")
            self.status_label.setText(f"✓ Connected as: {name}")
            self.status_label.setStyleSheet(f"color: {HTB_GREEN}; font-size: 13px;")
        else:
            self.status_label.setText(f"✗ Connection failed: {result}")
            self.status_label.setStyleSheet("color: #fc4747; font-size: 13px;")
    
    def _toggle_debug(self, enabled: bool):
        config.debug = enabled
        debug_log("SETTINGS", f"Debug mode: {enabled}")
