# ----- Utils Modules-----
from utils.color import THEME_BG_SECONDARY, THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === Tree View === */
    QTreeView {{
        background-color: {THEME_BG_SECONDARY};
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #444444;
        outline: 0;
    }}

    QTreeView::item:hover {{
        background-color: #4F4F4F;
    }}

    QTreeView::item:selected {{
        background-color: #3B5689;
    }}

    QTreeView::item:selected:!active {{
        color: {THEME_TEXT_PRIMARY};
    }}
    """
