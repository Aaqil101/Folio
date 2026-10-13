# ----- Utils Modules-----
from utils.color import THEME_BG_SECONDARY, AccentTheme


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    /* === Widget === */
    QWidget[CardsContainer="true"] {{
        background: transparent;
    }}

    /* === Header Bar (job toolbar + app buttons) === */
    #HeaderBar {{
        background-color: {THEME_BG_SECONDARY};
        border-bottom: 1px solid #323232;
    }}

    #HeaderSeparator {{
        background-color: #323232;
        border: none;
    }}

    /* === Search Container === */
    #SearchContainer {{
        background-color: {THEME_BG_SECONDARY};
        border: 1px solid {accent['border']};
        border-radius: 0px;
    }}
    """
