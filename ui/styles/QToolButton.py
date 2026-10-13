# ----- Core Modules-----
from utils.constants import BORDER_RADIUS_SMALL

# ----- Utils Modules-----
from utils.color import AccentTheme


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    /* === Tool Button === */
    QToolButton {{
        background-color: rgba(255, 255, 255, 0.04);
        border: none;
        border-radius: {BORDER_RADIUS_SMALL}px;
        padding: 2px;
        min-width: 15px;
        min-height: 15px;
    }}
    QToolButton:hover {{
        background-color: rgba(122, 162, 247, 0.15);
    }}
    QToolButton:pressed {{
        background-color: rgba(122, 162, 247, 0.25);
    }}

    /* === Main Tool Button === */
    QToolButton[MainToolButton="true"] {{
        background-color: transparent;
        border: none;
        border-radius: 0px;
        padding: 4px;
    }}

    QToolButton[MainToolButton="true"]:hover {{
        background-color: {accent['hover_background']};
    }}

    QToolButton[MainToolButton="true"]:pressed {{
        background-color: {accent['pressed_background']};
    }}
    """
