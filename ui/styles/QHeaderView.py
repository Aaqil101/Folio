# ----- Utils Modules-----
from utils.color import THEME_BG_SECONDARY, THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === Header View === */
    QHeaderView {{
        background-color: {THEME_BG_SECONDARY};
        color: {THEME_TEXT_PRIMARY};
    }}

    QHeaderView::section {{
        background-color: {THEME_BG_SECONDARY};
        border: none;
        padding: 2px 4px;
        min-height: 18px;
    }}

    QFileDialog QHeaderView {{
        background-color: {THEME_BG_SECONDARY};
    }}

    QFileDialog QHeaderView::section {{
        background-color: {THEME_BG_SECONDARY};
        border: none;
    }}
    """
