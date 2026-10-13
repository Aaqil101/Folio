# ----- Utils Modules-----
from utils.color import THEME_TEXT_PRIMARY, AccentTheme


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    /* === Line Edit === */
    QLineEdit {{
        background-color: #1F1F1F;
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #444444;
        border-radius: 0px;
        padding: 1px;
    }}
    QLineEdit[text=\"\"] {{
        color: {THEME_TEXT_PRIMARY};
    }}

    /* === Main Line Edit === */
    QLineEdit[MainLineEdit="true"] {{
        background-color: {accent['main_background']};
        color: {THEME_TEXT_PRIMARY};
        border-radius: 4px;
        padding: 6px 10px;
        border: 2px solid transparent;
    }}
    QLineEdit[MainLineEdit="true"]:focus {{
        background-color: #1F1F1F;
        border-bottom: 2px solid {accent['border']};
        border-right: 2px solid {accent['border']};
        font-style: unset;
    }}

    /* === Search Bar === */
    QLineEdit[SearchBar="true"] {{
        background-color: {accent['main_background']};
        selection-background-color: {accent['border']};
        selection-color: {THEME_TEXT_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
        border-radius: 0px;
        padding: 1px;
    }}
    QLineEdit[SearchBar="true"]:hover {{
        background-color: {accent['hover_background']};
    }}
    QLineEdit[SearchBar="true"]:focus {{
        background-color: #222;
        border: 1px solid {accent['border']};
    }}
    QLineEdit QToolButton {{
        min-width: 16px;
        min-height: 16px;
        background-color: transparent;
        border: none;
        padding: 0px;
    }}
    """
