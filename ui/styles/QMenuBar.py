# ----- Core Modules-----
from utils.constants import BORDER_RADIUS_SMALL

# ----- Utils Modules-----
from utils.color import (
    COLOR_LIGHT_BLUE,
    THEME_BG_PRIMARY,
    THEME_BG_SECONDARY,
    THEME_BORDER,
    THEME_TEXT_PRIMARY,
)


def qss() -> str:
    return f"""
    /* === Menu Bar === */
    QMenuBar {{
        background-color: {THEME_BG_SECONDARY};
        color: {THEME_TEXT_PRIMARY};
        border-bottom: 1px solid {THEME_BORDER};
        padding: 4px;
    }}

    QMenuBar::item {{
        background-color: {THEME_BG_SECONDARY};
    }}

    QMenuBar::item:selected {{
        background-color: {THEME_BG_PRIMARY};
        color: {COLOR_LIGHT_BLUE};
    }}

    QMenuBar::item:hover {{
        background-color: {THEME_BG_SECONDARY};
        color: {COLOR_LIGHT_BLUE};
    }}

    QMenuBar::item:pressed {{
        background-color: {THEME_BG_SECONDARY};
        color: {COLOR_LIGHT_BLUE};
    }}
    """
