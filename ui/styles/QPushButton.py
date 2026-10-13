# ----- Utils Modules-----
from utils.color import (
    COLOR_DARK_BLUE,
    COLOR_GREEN,
    COLOR_LIGHT_BLUE,
    COLOR_ORANGE,
    COLOR_RED,
    THEME_BORDER,
    THEME_TEXT_PRIMARY,
    AccentTheme,
)


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    /* === Buttons === */
    QPushButton {{
        background-color: rgba(255, 255, 255, 0.04);
        color: {THEME_TEXT_PRIMARY};
        border-radius: 0px;
        padding: 3px 10px;
        height: 18px;
    }}
    QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.08);
        border-bottom: 2px solid {COLOR_DARK_BLUE};
    }}
    QPushButton:pressed {{
        background-color: rgba(255, 255, 255, 0.12);
    }}
    QPushButton:focus {{
        background-color: rgba(255, 255, 255, 0.08);
        border-bottom: 2px solid {COLOR_DARK_BLUE};
        outline: none;
    }}

    /* === About Close Button === */
    #AboutCloseButton {{
        background-color: {accent['main_background']};
        color: {THEME_TEXT_PRIMARY};
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
        font-size: 10pt;
        font-weight: bold;
        text-align: center;
    }}
    #AboutCloseButton:hover {{
        background-color: {accent['hover_background']};
    }}
    #AboutCloseButton:pressed {{
        background-color: {accent['pressed_background']};
        color: {COLOR_RED};
    }}

    /* === Browse Button === */
    QPushButton[BrowseButton="true"] {{
        background-color: rgba(255, 255, 255, 0.04);
        color: {THEME_TEXT_PRIMARY};
        border-radius: 4px;
        padding: 4px 12px;
    }}
    QPushButton[BrowseButton="true"]:hover {{
        background-color: {accent['hover_background']};
        border-bottom: 2px solid {accent['border']};
    }}
    QPushButton[BrowseButton="true"]:pressed {{
        background-color: {accent['pressed_background']};
    }}
    QPushButton[BrowseButton="true"]:focus {{
        background-color: {accent['hover_background']};
        border-bottom: 2px solid {accent['border']};
        outline: none;
    }}

    /* === Save Button === */
    QPushButton[SaveButton="true"] {{
        background-color: rgba(158, 206, 106, 0.2);
        color: {COLOR_GREEN};
        border-radius: 4px;
        padding: 6px 16px;
    }}
    QPushButton[SaveButton="true"]:hover {{
        background-color: rgba(158, 206, 106, 0.3);
        border-bottom: 2px solid {COLOR_GREEN};
    }}
    QPushButton[SaveButton="true"]:pressed {{
        background-color: rgba(158, 206, 106, 0.4);
    }}
    QPushButton[SaveButton="true"]:focus {{
        background-color: rgba(158, 206, 106, 0.3);
        border-bottom: 2px solid {COLOR_GREEN};
        outline: none;
    }}

    /* === Collapse Button === */
    QPushButton[CollapseButton="true"] {{
        background-color: transparent;
        border: none;
        border-radius: 4px;
        padding: 2px;
    }}
    QPushButton[CollapseButton="true"]:hover {{
        background-color: {accent['hover_background']};
    }}
    QPushButton[CollapseButton="true"]:pressed {{
        background-color: {accent['pressed_background']};
    }}
    """
