# ----- Core Modules-----
from utils.constants import BORDER_RADIUS_SMALL

# ----- Utils Modules-----
from utils.color import THEME_BG_PRIMARY


def qss() -> str:
    return f"""
    /* === Scroll Area === */
    QScrollArea {{
        border: none;
        background-color: {THEME_BG_PRIMARY};
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: {THEME_BG_PRIMARY};
    }}

    /* Vertical Scrollbar */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 12px;
        margin: 4px 2px 4px 2px;
        border-radius: {BORDER_RADIUS_SMALL}px;
    }}

    /* Scrollbar Handle (Thumb) */
    QScrollBar::handle:vertical {{
        background-color: rgba(122, 162, 247, 0.3);
        border-radius: {BORDER_RADIUS_SMALL}px;
        min-height: 30px;
        margin: 0px 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: rgba(122, 162, 247, 0.5);
    }}

    QScrollBar::handle:vertical:pressed {{
        background-color: rgba(122, 162, 247, 0.7);
    }}

    /* Remove arrow buttons */
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
        background: none;
        border: none;
    }}

    /* Scrollbar background track */
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: rgba(255, 255, 255, 0.02);
        border-radius: {BORDER_RADIUS_SMALL}px;
    }}

    /* Horizontal Scrollbar (if needed) */
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 12px;
        margin: 2px 4px 2px 4px;
        border-radius: {BORDER_RADIUS_SMALL}px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: rgba(122, 162, 247, 0.3);
        border-radius: {BORDER_RADIUS_SMALL}px;
        min-width: 30px;
        margin: 2px 0px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: rgba(122, 162, 247, 0.5);
    }}

    QScrollBar::handle:horizontal:pressed {{
        background-color: rgba(122, 162, 247, 0.7);
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
        background: none;
        border: none;
    }}

    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: rgba(255, 255, 255, 0.02);
        border-radius: {BORDER_RADIUS_SMALL}px;
    }}
    """
