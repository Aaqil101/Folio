# ----- Utils Modules-----
from utils.color import THEME_TEXT_PRIMARY, AccentTheme


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    QDoubleSpinBox {{
        background-color: {accent['main_background']};
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid {accent['border']};
        padding: 1px;
    }}

    QDoubleSpinBox:disabled {{
        color: #828282;
    }}

    QDoubleSpinBox:focus {{
        background-color: #222;
        border: 1px solid {accent['border']};
    }}

    QDoubleSpinBox[text=\"\"] {{
        color: {THEME_TEXT_PRIMARY};
    }}
    """
