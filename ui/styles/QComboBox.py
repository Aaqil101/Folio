# ----- Utils Modules -----
from utils.color import COLOR_DARK_BLUE, THEME_BG_PRIMARY, THEME_TEXT_PRIMARY, AccentTheme


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    /* === ComboBox === */
    QComboBox {{
        background-color: #1F1F1F;
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #444444;
        border-radius: 0px;
        padding: 1px 1px 1px 3px;
    }}
    QComboBox:hover {{
        background-color: rgba(255, 255, 255, 0.06);
    }}
    QComboBox:focus {{
        background-color: rgba(255, 255, 255, 0.06);
        outline: none;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border: none;
        background: transparent;
    }}
    QComboBox::down-arrow {{
        image: url(:/assets/expand_more.svg);
        width: 10px;
        height: 10px;
        border: none;
    }}
    QComboBox::down-arrow:on {{
        image: url(:/assets/expand_less.svg);
    }}

    /* Dropdown list styling */
    QComboBox QAbstractItemView {{
        background-color: {THEME_BG_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
        border-radius: 0px;
        selection-background-color: #4F4F4F;
        selection-color: {THEME_TEXT_PRIMARY};
        show-decoration-selected: 1;
        outline: none;
    }}
    QComboBox QAbstractItemView::item {{
        background-color: {THEME_BG_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
        height: 20px;
        padding: 2px 4px;
        border: none;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background-color: #4F4F4F;
        color: {THEME_TEXT_PRIMARY};
    }}
    QComboBox QAbstractItemView::item:selected {{
        background-color: #3B5689;
        color: {THEME_TEXT_PRIMARY};
    }}
    QComboBox QAbstractItemView::item:selected:hover {{
        background-color: #3B5689;
        color: {THEME_TEXT_PRIMARY};
        border: none;
    }}

    QComboBox[MainComboBox="true"] {{
        background-color: rgba(255, 255, 255, 0.04);
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #444444;
        border-radius: 0px;
        padding: 1px 1px 1px 3px;
    }}
    QComboBox[MainComboBox="true"]:hover {{
        background-color: rgba(255, 255, 255, 0.06);
        border-bottom: 2px solid {accent['border']};
    }}
    QComboBox[MainComboBox="true"]:focus {{
        background-color: rgba(255, 255, 255, 0.06);
        border-bottom: 2px solid {accent['border']};
        outline: none;
    }}
    QComboBox[MainComboBox="true"]::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border: none;
        background: transparent;
    }}
    QComboBox[MainComboBox="true"]::down-arrow {{
        image: url(:/assets/expand_more.svg);
        width: 10px;
        height: 10px;
        border: none;
    }}
    QComboBox[MainComboBox="true"]::down-arrow:on {{
        image: url(:/assets/expand_less.svg);
    }}

    /* Dropdown list styling */
    QComboBox[MainComboBox="true"] QAbstractItemView {{
        background-color: {THEME_BG_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
        border-radius: 0px;
        selection-background-color: {COLOR_DARK_BLUE};
        selection-color: {THEME_TEXT_PRIMARY};
        show-decoration-selected: 1;
        outline: none;
    }}
    QComboBox[MainComboBox="true"] QAbstractItemView::item {{
        background-color: {THEME_BG_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
        height: 20px;
        padding: 2px 4px;
        border: none;
    }}
    QComboBox[MainComboBox="true"] QAbstractItemView::item:hover {{
        background-color: {accent['hover_background']};
        color: {THEME_TEXT_PRIMARY};
    }}
    QComboBox[MainComboBox="true"] QAbstractItemView::item:selected {{
        background-color: {accent['hover_background']};
        color: {THEME_TEXT_PRIMARY};
    }}
    QComboBox[MainComboBox="true"] QAbstractItemView::item:selected:hover {{
        background-color: {accent['hover_background']};
        border: none;
    }}
    """
