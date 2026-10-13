# ----- Utils Modules-----
from utils.color import THEME_BG_PRIMARY, THEME_TEXT_PRIMARY


def qss() -> str:
    return f"""
    /* === Main Window === */
    QMainWindow {{
        background-color: {THEME_BG_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
    }}
    """
