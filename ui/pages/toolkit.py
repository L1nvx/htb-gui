"""Toolkit Page - CyberChef-style Hacker Toolbox."""

import base64
import hashlib
import html
import json
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QComboBox, QLineEdit, QFrame, QScrollArea, QPushButton,
    QGridLayout, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Slot

from ui.styles import (
    HTB_GREEN, HTB_BG_CARD, HTB_BG_MAIN, HTB_BG_HOVER,
    HTB_TEXT_MAIN, HTB_TEXT_SEC, HTB_TEXT_DIM, HTB_BORDER,
    HTB_BG_DARKEST, HTB_BG_INPUT, FONT_FAMILY_MAIN
)
from ui.widgets.modern_widgets import ModernButton
from utils.debug import debug_log


def _get_tun0_ip() -> Optional[str]:
    """Get tun0 interface IP address."""
    try:
        out = subprocess.check_output(
            ["ip", "-4", "addr", "show", "tun0"],
            stderr=subprocess.DEVNULL, timeout=2
        ).decode()
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                return line.split()[1].split("/")[0]
    except Exception:
        pass
    return None


# ============================================================
# PAYLOADS DATA — loaded from JSON config
# ============================================================

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_PAYLOADS_FILE = _DATA_DIR / "payloads.json"


def _load_payloads():
    """Load payloads from JSON config file."""
    try:
        with open(_PAYLOADS_FILE, "r") as f:
            data = json.load(f)
        shells = data.get("reverse_shells", [])
        payloads = {}
        for cat, items in data.get("quick_payloads", {}).items():
            payloads[cat] = [(p["name"], p["code"]) for p in items]
        return shells, payloads
    except Exception as e:
        debug_log("TOOLKIT", f"Failed to load payloads.json: {e}")
        return [], {}


REVERSE_SHELLS, QUICK_PAYLOADS = _load_payloads()


ENCODING_OPS = [
    "URL Encode",
    "URL Decode",
    "Base64 Encode",
    "Base64 Decode",
    "HTML Encode",
    "HTML Decode",
    "Hex Encode",
    "Hex Decode",
    "ROT13",
    "MD5 Hash",
    "SHA1 Hash",
    "SHA256 Hash",
    "Double URL Encode",
    "Unicode Escape",
]


def _apply_encoding(op: str, text: str) -> str:
    """Apply encoding/decoding operation."""
    try:
        if op == "URL Encode":
            return urllib.parse.quote(text)
        elif op == "URL Decode":
            return urllib.parse.unquote(text)
        elif op == "Double URL Encode":
            return urllib.parse.quote(urllib.parse.quote(text))
        elif op == "Base64 Encode":
            return base64.b64encode(text.encode()).decode()
        elif op == "Base64 Decode":
            return base64.b64decode(text.encode()).decode()
        elif op == "HTML Encode":
            return html.escape(text)
        elif op == "HTML Decode":
            return html.unescape(text)
        elif op == "Hex Encode":
            return text.encode().hex()
        elif op == "Hex Decode":
            return bytes.fromhex(text).decode()
        elif op == "ROT13":
            import codecs
            return codecs.encode(text, "rot_13")
        elif op == "MD5 Hash":
            return hashlib.md5(text.encode()).hexdigest()
        elif op == "SHA1 Hash":
            return hashlib.sha1(text.encode()).hexdigest()
        elif op == "SHA256 Hash":
            return hashlib.sha256(text.encode()).hexdigest()
        elif op == "Unicode Escape":
            return text.encode("unicode_escape").decode()
        return text
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# WIDGETS
# ============================================================

class _CopyButton(ModernButton):
    """Button that shows '✓ Copied!' feedback."""

    def __init__(self, text="📋 Copy", parent=None):
        super().__init__(text, btn_type="secondary", parent=parent)
        self._original = text
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._reset)

    def flash_copied(self):
        self.setText("✓ Copied!")
        self._timer.start(1200)

    def _reset(self):
        self.setText(self._original)


class _CodeSnippet(QWidget):
    """A compact code snippet with title and copy button. Used for both payloads and shells."""

    def __init__(self, title: str, code_template: str, ip: str = "", port: str = "4444", parent=None):
        super().__init__(parent)
        self._template = code_template
        self._ip = ip
        self._port = port

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container frame
        frame = QFrame()
        frame.setObjectName("snippetFrame")
        frame.setStyleSheet(f"""
            QFrame#snippetFrame {{
                background-color: {HTB_BG_MAIN};
                border: 1px solid {HTB_BORDER};
                border-radius: 8px;
            }}
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(12, 8, 12, 8)
        frame_layout.setSpacing(6)

        # Header: title (left) + copy btn (right)
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel(title)
        title_lbl.setTextFormat(Qt.PlainText)
        title_lbl.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()

        self._copy_btn = _CopyButton("📋 Copy", self)
        self._copy_btn.setFixedHeight(22)
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {HTB_BG_HOVER};
                border: 1px solid {HTB_BORDER};
                border-radius: 4px;
                color: {HTB_TEXT_SEC};
                font-size: 10px;
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                background-color: {HTB_BG_CARD};
                color: {HTB_TEXT_MAIN};
            }}
        """)
        self._copy_btn.clicked.connect(self._do_copy)
        hdr.addWidget(self._copy_btn)
        frame_layout.addLayout(hdr)

        # Code text
        self._code_lbl = QLabel()
        self._code_lbl.setTextFormat(Qt.PlainText)
        self._code_lbl.setWordWrap(True)
        self._code_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._code_lbl.setStyleSheet(f"""
            background-color: {HTB_BG_DARKEST};
            color: {HTB_TEXT_SEC};
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
            font-size: 11px;
            border: 1px solid {HTB_BORDER};
            border-radius: 4px;
            padding: 8px;
        """)
        self._update_code()
        frame_layout.addWidget(self._code_lbl)

        layout.addWidget(frame)

    def _render(self) -> str:
        return self._template.replace("{IP}", self._ip).replace("{PORT}", self._port)

    def _update_code(self):
        self._code_lbl.setText(self._render())

    def update_params(self, ip: str, port: str):
        self._ip = ip
        self._port = port
        self._update_code()

    def _do_copy(self):
        QApplication.clipboard().setText(self._code_lbl.text())
        self._copy_btn.flash_copied()


# ============================================================
# TAB BUTTON
# ============================================================

class _TabButton(QPushButton):
    """Navigation pill tab button."""

    def __init__(self, text: str, tab_id: str, parent=None):
        super().__init__(text, parent)
        self.tab_id = tab_id
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
                color: {HTB_TEXT_SEC};
                font-family: {FONT_FAMILY_MAIN};
                font-weight: 600;
                font-size: 13px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {HTB_BG_HOVER};
                color: {HTB_TEXT_MAIN};
            }}
            QPushButton:checked {{
                background-color: {HTB_BG_HOVER};
                color: {HTB_GREEN};
                border: 1px solid {HTB_BORDER};
            }}
        """)


# ============================================================
# MAIN PAGE
# ============================================================

class ToolkitPage(QWidget):
    """CyberChef-style Hacker Toolkit."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shell_cards: list[_ShellCard] = []
        self._payload_cards: list[_PayloadCard] = []
        self._ip = _get_tun0_ip() or "10.10.14.1"
        self._port = "4444"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Header
        title = QLabel("Toolkit")
        title.setStyleSheet("font-size: 28px; font-weight: 700; letter-spacing: -0.5px;")
        layout.addWidget(title)

        # Tab Bar
        tab_bar = QHBoxLayout()
        tab_bar.setSpacing(8)

        self._tab_btns = {}
        tabs = [
            ("encoder", "🔄 Encoder / Decoder"),
            ("shells", "🐚 Reverse Shells"),
            ("payloads", "⚡ Quick Payloads"),
        ]
        for tid, label in tabs:
            btn = _TabButton(label, tid)
            btn.clicked.connect(lambda checked, t=tid: self._switch_tab(t))
            tab_bar.addWidget(btn)
            self._tab_btns[tid] = btn

        tab_bar.addStretch()
        layout.addLayout(tab_bar)

        # Content area (scroll)
        self._content_scroll = QScrollArea()
        self._content_scroll.setWidgetResizable(True)
        self._content_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: {HTB_BG_DARKEST};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {HTB_BG_HOVER};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        layout.addWidget(self._content_scroll)

        # Build tabs
        self._encoder_widget = self._build_encoder_tab()
        self._shells_widget = self._build_shells_tab()
        self._payloads_widget = self._build_payloads_tab()

        # Start on encoder
        self._switch_tab("encoder")

    # -------------------------------------------------------
    # TAB SWITCHING
    # -------------------------------------------------------

    def _switch_tab(self, tab_id: str):
        for tid, btn in self._tab_btns.items():
            btn.setChecked(tid == tab_id)

        # Remove current widget without deleting it
        old = self._content_scroll.takeWidget()
        if old:
            old.setParent(None)

        if tab_id == "encoder":
            self._content_scroll.setWidget(self._encoder_widget)
        elif tab_id == "shells":
            # Refresh tun0 IP
            ip = _get_tun0_ip()
            if ip:
                self._ip = ip
                self.ip_input.setText(ip)
            self._content_scroll.setWidget(self._shells_widget)
        elif tab_id == "payloads":
            ip = _get_tun0_ip()
            if ip:
                self._ip = ip
            self._content_scroll.setWidget(self._payloads_widget)

    # -------------------------------------------------------
    # TAB 1: ENCODER / DECODER
    # -------------------------------------------------------

    def _build_encoder_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Input
        in_label = QLabel("INPUT")
        in_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(in_label)

        self.enc_input = QTextEdit()
        self.enc_input.setPlaceholderText("Paste text here...")
        self.enc_input.setMinimumHeight(120)
        self.enc_input.setMaximumHeight(200)
        self.enc_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {HTB_BG_MAIN};
                border: 1px solid {HTB_BORDER};
                border-radius: 8px;
                color: {HTB_TEXT_MAIN};
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 13px;
                padding: 10px;
            }}
        """)
        layout.addWidget(self.enc_input)

        # Controls row
        ctrl = QHBoxLayout()
        ctrl.setSpacing(12)

        self.op_combo = QComboBox()
        for op in ENCODING_OPS:
            self.op_combo.addItem(op)
        self.op_combo.setMinimumWidth(200)
        self.op_combo.currentIndexChanged.connect(lambda: self._apply_encoding())
        ctrl.addWidget(self.op_combo)

        # Auto-apply on text change
        self.enc_input.textChanged.connect(self._apply_encoding)

        swap_btn = ModernButton("⇅ Swap", btn_type="secondary")
        swap_btn.clicked.connect(self._swap_io)
        ctrl.addWidget(swap_btn)

        clear_btn = ModernButton("✕ Clear", btn_type="secondary")
        clear_btn.clicked.connect(self._clear_enc)
        ctrl.addWidget(clear_btn)

        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Output
        out_label = QLabel("OUTPUT")
        out_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(out_label)

        out_row = QVBoxLayout()
        self.enc_output = QTextEdit()
        self.enc_output.setReadOnly(True)
        self.enc_output.setMinimumHeight(120)
        self.enc_output.setMaximumHeight(200)
        self.enc_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {HTB_BG_MAIN};
                border: 1px solid {HTB_BORDER};
                border-radius: 8px;
                color: {HTB_GREEN};
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 13px;
                padding: 10px;
            }}
        """)
        out_row.addWidget(self.enc_output)

        copy_out_btn = _CopyButton("📋 Copy Output", self)
        copy_out_btn.clicked.connect(lambda: self._copy_output(copy_out_btn))
        out_row.addWidget(copy_out_btn, alignment=Qt.AlignLeft)

        layout.addLayout(out_row)
        layout.addStretch()

        return w

    def _apply_encoding(self):
        text = self.enc_input.toPlainText()
        op = self.op_combo.currentText()
        result = _apply_encoding(op, text)
        self.enc_output.setPlainText(result)

    def _swap_io(self):
        out = self.enc_output.toPlainText()
        inp = self.enc_input.toPlainText()
        self.enc_input.setPlainText(out)
        self.enc_output.setPlainText(inp)

    def _clear_enc(self):
        self.enc_input.clear()
        self.enc_output.clear()

    def _copy_output(self, btn: _CopyButton):
        QApplication.clipboard().setText(self.enc_output.toPlainText())
        btn.flash_copied()

    # -------------------------------------------------------
    # TAB 2: REVERSE SHELLS
    # -------------------------------------------------------

    def _build_shells_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # IP / Port controls
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet(f"background-color: {HTB_BG_MAIN}; border-radius: 10px;")
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(16)

        ip_lbl = QLabel("LHOST")
        ip_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none;")
        ctrl_layout.addWidget(ip_lbl)

        self.ip_input = QLineEdit(self._ip)
        self.ip_input.setMinimumWidth(160)
        self.ip_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {HTB_BG_DARKEST};
                border: 1px solid {HTB_BORDER};
                border-radius: 6px;
                color: {HTB_GREEN};
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                padding: 6px 10px;
            }}
        """)
        self.ip_input.textChanged.connect(self._on_params_changed)
        ctrl_layout.addWidget(self.ip_input)

        port_lbl = QLabel("LPORT")
        port_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none;")
        ctrl_layout.addWidget(port_lbl)

        self.port_input = QLineEdit(self._port)
        self.port_input.setFixedWidth(80)
        self.port_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {HTB_BG_DARKEST};
                border: 1px solid {HTB_BORDER};
                border-radius: 6px;
                color: {HTB_GREEN};
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                padding: 6px 10px;
            }}
        """)
        self.port_input.textChanged.connect(self._on_params_changed)
        ctrl_layout.addWidget(port_lbl)
        ctrl_layout.addWidget(self.port_input)

        # tun0 indicator
        tun0_ip = _get_tun0_ip()
        if tun0_ip:
            tun0_lbl = QLabel(f"🟢 tun0: {tun0_ip}")
            tun0_lbl.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px; border: none;")
        else:
            tun0_lbl = QLabel("🔴 tun0: not detected")
            tun0_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; border: none;")
        ctrl_layout.addWidget(tun0_lbl)

        ctrl_layout.addStretch()

        # Listener command
        listener_lbl = QLabel("Listener:")
        listener_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 600; border: none;")
        ctrl_layout.addWidget(listener_lbl)

        self.listener_cmd = QLabel(f"nc -lvnp {self._port}")
        self.listener_cmd.setStyleSheet(f"""
            color: {HTB_TEXT_SEC};
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            background-color: {HTB_BG_DARKEST};
            border: 1px solid {HTB_BORDER};
            border-radius: 4px;
            padding: 4px 8px;
        """)
        ctrl_layout.addWidget(self.listener_cmd)

        listener_copy = _CopyButton("📋", self)
        listener_copy.setFixedSize(36, 28)
        listener_copy.clicked.connect(lambda: self._copy_listener(listener_copy))
        ctrl_layout.addWidget(listener_copy)

        layout.addWidget(ctrl_frame)

        # Shell cards
        shells_label = QLabel("SHELLS")
        shells_label.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(shells_label)

        self._shell_cards: list[_CodeSnippet] = []
        grid = QGridLayout()
        grid.setSpacing(8)
        for i, shell in enumerate(REVERSE_SHELLS):
            card = _CodeSnippet(shell["name"], shell["cmd"], self._ip, self._port)
            self._shell_cards.append(card)
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)

        layout.addStretch()
        return w

    def _on_params_changed(self):
        self._ip = self.ip_input.text()
        self._port = self.port_input.text() or "4444"
        self.listener_cmd.setText(f"nc -lvnp {self._port}")
        for card in self._shell_cards:
            card.update_params(self._ip, self._port)

    def _copy_listener(self, btn: _CopyButton):
        QApplication.clipboard().setText(self.listener_cmd.text())
        btn.flash_copied()

    # -------------------------------------------------------
    # TAB 3: QUICK PAYLOADS
    # -------------------------------------------------------

    def _build_payloads_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # IP / Port controls for payloads
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet(f"background-color: {HTB_BG_MAIN}; border-radius: 10px;")
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(16, 10, 16, 10)
        ctrl_layout.setSpacing(12)

        ip_lbl = QLabel("LHOST")
        ip_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none;")
        ctrl_layout.addWidget(ip_lbl)

        self.pay_ip_input = QLineEdit(self._ip)
        self.pay_ip_input.setMinimumWidth(140)
        self.pay_ip_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {HTB_BG_DARKEST};
                border: 1px solid {HTB_BORDER};
                border-radius: 6px;
                color: {HTB_GREEN};
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                padding: 5px 8px;
            }}
        """)
        self.pay_ip_input.textChanged.connect(self._on_payload_params_changed)
        ctrl_layout.addWidget(self.pay_ip_input)

        port_lbl = QLabel("LPORT")
        port_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none;")
        ctrl_layout.addWidget(port_lbl)

        self.pay_port_input = QLineEdit(self._port)
        self.pay_port_input.setFixedWidth(70)
        self.pay_port_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {HTB_BG_DARKEST};
                border: 1px solid {HTB_BORDER};
                border-radius: 6px;
                color: {HTB_GREEN};
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                padding: 5px 8px;
            }}
        """)
        self.pay_port_input.textChanged.connect(self._on_payload_params_changed)
        ctrl_layout.addWidget(self.pay_port_input)

        ctrl_layout.addStretch()
        layout.addWidget(ctrl_frame)

        # Payload cards
        self._payload_cards: list[_CodeSnippet] = []

        for category, payloads in QUICK_PAYLOADS.items():
            cat_lbl = QLabel(category.upper())
            cat_lbl.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
            layout.addWidget(cat_lbl)

            grid = QGridLayout()
            grid.setSpacing(8)
            for i, (name, code) in enumerate(payloads):
                card = _CodeSnippet(name, code, ip=self._ip, port=self._port)
                grid.addWidget(card, i // 2, i % 2)
                self._payload_cards.append(card)
            layout.addLayout(grid)

        layout.addStretch()
        return w

    def _on_payload_params_changed(self):
        ip = self.pay_ip_input.text()
        port = self.pay_port_input.text() or "4444"
        for card in self._payload_cards:
            card.update_params(ip, port)
