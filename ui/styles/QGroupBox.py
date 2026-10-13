# ----- Core Modules-----
from utils.constants import BORDER_RADIUS

# ----- Utils Modules-----
from utils.color import THEME_BG_SECONDARY, THEME_BORDER, THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === Group Box === */
    QGroupBox {{
        background-color: {THEME_BG_SECONDARY};
        border: 1px solid {THEME_BORDER};
        border-radius: {BORDER_RADIUS}px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: bold;
    }}

    QGroupBox::title {{
        color: {THEME_TEXT_PRIMARY};
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
    }}
    """
