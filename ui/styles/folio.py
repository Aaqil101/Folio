# ----- Utils Modules -----
from utils.color import (
    COLOR_RED,
    THEME_BG_PRIMARY,
    THEME_BG_SECONDARY,
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
    AccentTheme,
)


def qss() -> str:
    accent: dict[str, str] = AccentTheme.get()
    return f"""
    /* === Disabled Save/Generate Button === */
    QPushButton[SaveButton="true"]:disabled {{
        background-color: rgba(255, 255, 255, 0.04);
        color: rgba(255, 255, 255, 0.35);
        border: none;
    }}

    /* ============================================================
       QUEUE UI STYLES
       ============================================================ */

    /* --- Header Bar toolbar buttons --- */
    #HeaderBar HoverIconButtonSVG {{
        background-color: rgba(255, 255, 255, 0.04);
        color: {THEME_TEXT_PRIMARY};
        border-radius: 4px;
        padding: 4px 12px;
        font-size: 10pt;
    }}
    #HeaderBar HoverIconButtonSVG:hover {{
        background-color: {accent['hover_background']};
        border-bottom: 2px solid {accent['border']};
    }}
    #HeaderBar HoverIconButtonSVG:pressed {{
        background-color: {accent['pressed_background']};
    }}
    #HeaderBar HoverIconButtonSVG:focus {{
        background-color: {accent['hover_background']};
        border-bottom: 2px solid {accent['border']};
        outline: none;
    }}
    #HeaderBar HoverIconButtonSVG:disabled {{
        background-color: rgba(255, 255, 255, 0.04);
        border-bottom: none;
        color: #666;
    }}
    #HeaderBar HoverIconButtonSVG:disabled:hover {{
        background-color: transparent;
        border-bottom: none;
    }}

    /* Remove-style toolbar buttons (Delete / Clear All) */
    #HeaderBar HoverIconButtonSVG[RemoveButton="true"] {{
        background-color: rgba(247, 118, 142, 0.12);
        color: {COLOR_RED};
    }}
    #HeaderBar HoverIconButtonSVG[RemoveButton="true"]:hover {{
        background-color: rgba(247, 118, 142, 0.22);
        border-bottom: 2px solid {COLOR_RED};
    }}
    #HeaderBar HoverIconButtonSVG[RemoveButton="true"]:focus {{
        background-color: rgba(247, 118, 142, 0.22);
        border-bottom: 2px solid {COLOR_RED};
        outline: none;
    }}
    #HeaderBar HoverIconButtonSVG[RemoveButton="true"]:pressed {{
        background-color: rgba(247, 118, 142, 0.32);
    }}
    #HeaderBar HoverIconButtonSVG[RemoveButton="true"]:disabled {{
        background-color: rgba(255, 255, 255, 0.04);
        border-bottom: none;
        color: #666;
    }}
    #HeaderBar HoverIconButtonSVG[RemoveButton="true"]:disabled:hover {{
        background-color: transparent;
        border-bottom: none;
    }}

    /* --- Job Table --- */
    #JobTable {{
        background-color: {THEME_BG_SECONDARY};
        alternate-background-color: {THEME_BG_PRIMARY};
        color: {THEME_TEXT_PRIMARY};
        border: none;
        border-top: 1px solid #323232;
        outline: 0;
    }}
    #JobTable::item {{
        padding: 6px 8px;
        border: none;
    }}
    #JobTable::item:hover {{
        background-color: {accent['hover_background']};
    }}
    #JobTable::item:selected {{
        background-color: {accent['main_background']};
        color: {THEME_TEXT_PRIMARY};
        border-left: 2px solid {accent['border']};
    }}
    #JobTable::item:selected:!active {{
        background-color: {accent['main_background']};
    }}
    #JobTable QHeaderView::section {{
        background-color: {THEME_BG_SECONDARY};
        color: {THEME_TEXT_SECONDARY};
        border: none;
        border-bottom: 1px solid #323232;
        padding: 6px 8px;
        font-size: 10pt;
    }}

    /* Empty state placeholder (overlay label on the table viewport) */
    #EmptyStateLabel {{
        color: #828282;
        font-size: 13px;
        padding: 40px;
        background-color: transparent;
    }}

    /* --- Queue Status Label --- */
    #QueueStatusLabel {{
        color: {THEME_TEXT_SECONDARY};
        font-size: 10pt;
        padding: 4px 0;
    }}

    /* --- Job Table Context Menu --- */
    #JobContextMenu {{
        background-color: #1F1F1F;
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #323232;
        border-radius: 4px;
        padding: 4px;
    }}
    #JobContextMenu::item {{
        color: {THEME_TEXT_PRIMARY};
        border-radius: 4px;
        padding: 4px 12px;
        height: 16px;
    }}
    #JobContextMenu::item:selected {{
        color: {THEME_TEXT_PRIMARY};
        background-color: {accent['border']};
        border-radius: 4px;
    }}
    #JobContextMenu::item:disabled {{
        color: #828282;
    }}
    #JobContextMenu::separator {{
        background-color: #616161;
        border: none;
        height: 1px;
        margin: 4px 8px;
    }}

    /* --- Job Dialog Inline Validation Warning --- */
    #JobWarningLabel {{
        color: {COLOR_RED};
        font-size: 10pt;
        padding: 2px 0;
    }}
    """
