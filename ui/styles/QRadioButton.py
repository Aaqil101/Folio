# ----- Utils Modules-----
from utils.color import THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === Radio Button === */
    QRadioButton {{
        color: {THEME_TEXT_PRIMARY};
        spacing: 8px;
    }}

    QRadioButton::indicator {{
        width: 0px;
        height: 0px;
        border: none;
        background: none;
    }}
    """
