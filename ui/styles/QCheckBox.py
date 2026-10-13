# ----- Utils Modules-----
from utils.color import THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === Check Box === */
    QCheckBox {{
        color: {THEME_TEXT_PRIMARY};
        spacing: 8px;
    }}

    QCheckBox:focus {{
        background: transparent;
        color: {THEME_TEXT_PRIMARY};
    }}

    QCheckBox::indicator {{
        width: 0px;
        height: 0px;
        border: none;
        background: transparent;
    }}
    """
