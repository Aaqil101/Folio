# ----- Utils Modules-----
from utils.color import THEME_TEXT_PRIMARY, AccentTheme


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    QListWidget[ScriptList="true"] {{
        background-color: transparent;
        border: none;
        border-radius: 0px;
        outline: none;
        padding: 6px;
    }}

    QListWidget[ScriptList="true"]::item {{
        background-color: transparent;
        border-radius: 6px;
        padding: 0px;
        margin: 2px 0px;
    }}

    QListWidget[ScriptList="true"]::item:hover {{
        background-color: {accent['hover_background']};
    }}

    QListWidget[ScriptList="true"]::item:focus {{
        background-color: {accent['pressed_background']};
    }}

    QListWidget[ScriptList="true"]::item:selected {{
        background-color: {accent['pressed_background']};
    }}

    QListWidget[ScriptList="true"]::item:selected:!active {{
        color: {THEME_TEXT_PRIMARY};
    }}
    """
