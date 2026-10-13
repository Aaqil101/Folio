# ----- Utils Modules-----
from utils.color import THEME_BG_PRIMARY, THEME_BG_SECONDARY, THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === File Dialog === */
    QFileDialog {{
        background-color: {THEME_BG_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #444444;
        outline: 0;
    }}
    """
