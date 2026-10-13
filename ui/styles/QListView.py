# ----- Utils Modules-----
from utils.color import THEME_BG_SECONDARY, THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === List Widget === */
    QListView {{
        background-color: {THEME_BG_SECONDARY};
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #444444;
        outline: 0;
    }}

    QListView::item {{
        color: {THEME_TEXT_PRIMARY};
        padding: 0px 2px;
        height: 28px;
    }}

    QListView::item:hover {{
        background-color: #4F4F4F;
    }}

    QListView::item:focus {{
        background-color: #3B5689;
    }}

    QListView::item:selected {{
        background-color: #3B5689;
    }}

    QListView::item:selected:!active {{
        color: {THEME_TEXT_PRIMARY};
    }}
    """
