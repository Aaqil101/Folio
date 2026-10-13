# ----- Utils Modules-----
from utils.color import THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === Menu === */
    QMenu {{
        background-color: #1F1F1F;
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #323232;
        border-radius: 0px;
        padding: 0px;
    }}
    QMenu::item {{
        color: {THEME_TEXT_PRIMARY};
        border-radius: 0px;
        padding: 2px 8px;
        height: 16px;
    }}
    QMenu::item::selected {{
        color: {THEME_TEXT_PRIMARY};
        background-color: #5076B2;
        border-radius: 0px;
    }}
    QMenu::icon {{
        margin: 3px;
    }}
    QMenu::item:disabled {{
        color: #828282;
    }}
    QMenu::separator {{
        background-color: #616161;
        border: none;
        height: 1px;
        margin: 0px 4px 0px 4px;
    }}
    """
