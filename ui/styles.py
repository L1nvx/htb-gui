"""
HTB Client Styles - 'Deep Space' Theme.
A premium, dark, and vibrant aesthetic inspired by modern cyberpunk/hacker trends.
"""

from PySide6.QtGui import QColor, QPalette

# --- COLOR PALETTE ---
# Main Backgrounds (User Provided)
HTB_BG_DARKEST = "#101927"      # Main Page / Input
HTB_BG_MAIN    = "#151F2E"      # Sidebar / Secondary
HTB_BG_CARD    = "#1E2939"      # Card Background
HTB_BG_HOVER   = "#242F40"      # Hover / Brighter
HTB_BG_INPUT   = "#101927"      # Matches Darkest
HTB_BG_DARK    = HTB_BG_MAIN    # Alias

# Accents (User Provided)
HTB_GREEN      = "#9FEF00"      # Neon Green
HTB_GREEN_DIM  = "#92C61F"      # Dim/secondary Green
HTB_RED        = "#DB5353"      # Red
HTB_RED_DIM    = "#5E0D0F"      # Dark Red (Backgrounds for error)
HTB_CYAN       = "#00fff0"      # Keeping for accents
HTB_PURPLE     = "#bc13fe"      # Keeping for accents
HTB_ORANGE     = "#ff9e00"      # Keeping for accents

# Difficulty Colors
DIFF_EASY      = HTB_GREEN
DIFF_MEDIUM    = HTB_ORANGE
DIFF_HARD      = HTB_RED
DIFF_INSANE    = HTB_PURPLE

# Status Colors
STATUS_SUCCESS = HTB_GREEN
STATUS_WARNING = HTB_ORANGE
STATUS_ERROR   = HTB_RED
STATUS_INFO    = HTB_CYAN
HTB_TEXT_MAIN  = "#ffffff"
HTB_TEXT_SEC   = "#94a3b8"
HTB_TEXT_DIM   = "#64748b"
HTB_TEXT_MUTED = "#475569"

# Borders
HTB_BORDER     = "#242F40"      # Matches user provided #242F40
HTB_BORDER_GLOW= "#9FEF0040"    # Glow effect

# Gradients (CSS format)
GRADIENT_MAIN = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {HTB_BG_DARKEST}, stop:1 {HTB_BG_MAIN})"
GRADIENT_BTN  = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {HTB_GREEN}, stop:1 {HTB_GREEN_DIM})"

# --- FONTS ---
FONT_FAMILY_MAIN = "'Inter', 'Segoe UI', 'Roboto', sans-serif"
FONT_FAMILY_MONO = "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"

# --- GLOBAL STYLESHEET ---
GLOBAL_STYLE = f"""
/* Global Reset */
* {{
    font-family: {FONT_FAMILY_MAIN};
    color: {HTB_TEXT_MAIN};
    outline: none;
}}

/* Main Window */
QMainWindow {{
    background-color: {HTB_BG_DARKEST};
}}

QWidget {{
    background: transparent;
}}

/* Scrollbars - Minimalist & Dark */
QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background: {HTB_BG_MAIN};
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: #333;
    min-height: 30px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: #444;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {HTB_BG_MAIN};
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: #333;
    min-width: 30px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: #444;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    height: 0px;
}}

/* Tooltips */
QToolTip {{
    background-color: {HTB_BG_CARD};
    color: {HTB_TEXT_MAIN};
    border: 1px solid {HTB_BORDER};
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}}

/* Menu Bar / Menus */
QMenu {{
    background-color: {HTB_BG_CARD};
    border: 1px solid {HTB_BORDER};
    padding: 5px;
    border-radius: 8px;
}}

QMenu::item {{
    padding: 8px 25px 8px 15px;
    border-radius: 4px;
    color: {HTB_TEXT_SEC};
}}


QMenu::item:selected {{
    background-color: {HTB_BG_HOVER};
    color: {HTB_TEXT_MAIN};
}}

/* Inputs & Combos */
QLineEdit, QComboBox {{
    background-color: {HTB_BG_INPUT};
    border: 1px solid {HTB_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {HTB_TEXT_MAIN};
    outline: none;
}}

QLineEdit:focus, QComboBox:focus, QComboBox:hover {{
    border: 1px solid {HTB_BORDER};
    background-color: {HTB_BG_HOVER};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
    padding-right: 8px;
}}

QComboBox::down-arrow {{
    image: none;
    border: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {HTB_TEXT_SEC};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {HTB_BG_CARD};
    border: 1px solid {HTB_BORDER};
    border-radius: 4px;
    padding: 0px;
    outline: none;
    selection-background-color: {HTB_BG_HOVER};
    selection-color: {HTB_TEXT_MAIN};
}}

QComboBox QAbstractItemView::item {{
    background-color: {HTB_BG_CARD};
    color: {HTB_TEXT_SEC};
    padding: 6px 12px;
    border: none;
}}

QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {{
    background-color: {HTB_BG_HOVER};
    color: {HTB_TEXT_MAIN};
}}

QComboBox QFrame {{
    background-color: {HTB_BG_CARD};
    border: 1px solid {HTB_BORDER};
    border-radius: 4px;
}}

/* Tables */
QTableWidget, QTableView {{
    background-color: {HTB_BG_CARD};
    border: 1px solid {HTB_BORDER};
    border-radius: 8px;
    gridline-color: {HTB_BORDER};
}}

QTableWidget::item, QTableView::item {{
    padding: 8px;
    border-bottom: 1px solid {HTB_BORDER};
}}

QHeaderView::section {{
    background-color: {HTB_BG_MAIN};
    color: {HTB_TEXT_SEC};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {HTB_BORDER};
    font-weight: 600;
}}
"""

# --- BUTTON STYLES (Legacy/Standard support) ---
_BTN_UNIFORM = f"""
    QPushButton {{
        background-color: {HTB_BG_HOVER};
        border: 1px solid {HTB_BORDER};
        color: {HTB_TEXT_SEC};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {HTB_BG_CARD};
        color: {HTB_TEXT_MAIN};
    }}
"""

BTN_PRIMARY = _BTN_UNIFORM
BTN_DANGER = _BTN_UNIFORM
BTN_DEFAULT = _BTN_UNIFORM
