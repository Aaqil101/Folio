# ----- Core Modules-----
from utils.constants import BORDER_RADIUS_SMALL

# ----- Utils Modules-----
from utils.color import (
    THEME_BG_PRIMARY,
    THEME_BG_SECONDARY,
    THEME_BORDER,
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
)


def qss() -> str:
    return f"""
    /* === Tab Widget === */
    QTabWidget::pane {{
        background-color: {THEME_BG_PRIMARY};
        border: 1px solid {THEME_BORDER};
        border-radius: {BORDER_RADIUS_SMALL}px;
    }}
    QTabBar::tab {{
        background-color: {THEME_BG_SECONDARY};
        color: {THEME_TEXT_SECONDARY};
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: {BORDER_RADIUS_SMALL}px;
        border-top-right-radius: {BORDER_RADIUS_SMALL}px;
    }}
    QTabBar::tab:hover {{
        background-color: rgba(122, 162, 247, 0.1);
        color: {THEME_TEXT_PRIMARY};
    }}
    QTabBar::tab:selected {{
        background-color: rgba(122, 162, 247, 0.2);
        color: #FFFFFF;
        font-weight: bold;
    }}
    QTabBar::tab:disabled {{
        color: {THEME_BG_SECONDARY};
    }}
    QTabBar:focus {{
        outline: none;
    }}
    """
