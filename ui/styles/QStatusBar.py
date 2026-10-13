# ----- Utils Modules -----
from utils.color import THEME_BG_SECONDARY, THEME_BORDER, THEME_TEXT_SECONDARY


def qss() -> str:
    return f"""
    /* === Status Bar === */
    QStatusBar {{
        background-color: {THEME_BG_SECONDARY};
        color: {THEME_TEXT_SECONDARY};
        border-top: 1px solid {THEME_BORDER};
    }}
    """
