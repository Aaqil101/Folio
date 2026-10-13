# ----- Utils Modules-----
from utils.color import THEME_TEXT_PRIMARY, AccentTheme


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    QSpinBox {{
        background-color: {accent['main_background']};
        selection-background-color: {accent['border']};
        selection-color: {THEME_TEXT_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid {accent['border']};
        padding: 1px;
    }}

    QSpinBox:disabled {{
        color: #828282;
    }}

    QSpinBox:focus {{
        background-color: #222;
        border: 1px solid {accent['border']};
    }}

    QSpinBox[text=\"\"] {{
        color: {THEME_TEXT_PRIMARY};
    }}
    """
