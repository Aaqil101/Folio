# ----- Utils Modules-----
from utils.color import THEME_BG_SECONDARY


def qss() -> str:
    return f"""
    /* === About Dialog Container === */
    #AboutContainer {{
        background-color: {THEME_BG_SECONDARY};
        border: 1px solid #444444;
        border-radius: 0px;
    }}

    /* === Settings Group (Collapsible Section) === */
    QFrame[SettingsGroup="true"] {{
        background-color: {THEME_BG_SECONDARY};
        border: 1px solid #444444;
        padding: 4px;
        margin-bottom: 4px;
    }}
    """
