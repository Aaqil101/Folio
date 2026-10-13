# ----- Utils Modules-----
from utils.color import THEME_BG_PRIMARY, THEME_BG_SECONDARY, THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === Table View === */
    QTableView {{
        background-color: {THEME_BG_SECONDARY};
        alternate-background-color: {THEME_BG_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #444444;
        outline: 0;
    }}

    QTableView::item {{
        padding: 4px 8px;
        border: none;
    }}

    QTableView::item:hover {{
        background-color: #4F4F4F;
    }}

    QTableView::item:focus {{
        background-color: #3B5689;
    }}

    QTableView::item:selected {{
        background-color: #3B5689;
        color: {THEME_TEXT_PRIMARY};
    }}

    QTableView::item:selected:!active {{
        color: {THEME_TEXT_PRIMARY};
    }}

    QHeaderView {{
        background-color: {THEME_BG_SECONDARY};
        color: {THEME_TEXT_PRIMARY};
    }}

    QHeaderView::section {{
        background-color: {THEME_BG_SECONDARY};
        border: none;
        padding: 4px 8px;
        min-height: 20px;
        border-bottom: 1px solid #323232;
    }}
    """