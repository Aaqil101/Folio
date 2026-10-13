# ----- Utils Modules-----
from utils.color import THEME_TEXT_PRIMARY, AccentTheme


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    /* === Text Edit === */
    QTextEdit {{
        background-color: {accent['main_background']};
        color: {THEME_TEXT_PRIMARY};
        border-radius: 0px;
        padding: 2px;
    }}

    QTextEdit:focus {{
        background-color: #1F1F1F;
        border-bottom: 2px solid {accent['border']};
        border-right: 2px solid {accent['border']};
    }}
    """
