# ----- Core Modules-----
from utils.constants import FONT_FAMILY

# ----- Utils Modules-----
from utils.color import (
    COLOR_LIGHT_BLUE,
    THEME_BG_PRIMARY,
    THEME_BG_SECONDARY,
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
    AccentTheme,
)


def qss() -> str:
    # Get the app's accent color theme
    accent: dict[str, str] = AccentTheme.get()

    return f"""
    /* === Labels === */
    QLabel {{
        background-color: transparent;
        color: {THEME_TEXT_PRIMARY};
    }}

    /* === Info Label === */
    QLabel[InfoBox="true"] {{
        background-color: {THEME_BG_SECONDARY};
        color: {THEME_TEXT_PRIMARY};
        border: 1px solid #444444;
        border-radius: 0px;
        padding: 6px;
    }}

    QLabel[InfoLabel="true"] {{
        color: {THEME_BG_SECONDARY};
        font-size: 9pt;
    }}

    /* === Card Title === */
    QLabel[CardTitle="true"] {{
        color: {THEME_TEXT_PRIMARY};
        font-size: 10pt;
        font-weight: bold;
        background-color: transparent;
    }}

    /* === Section Header === */
    QLabel[SectionHeader="true"] {{
        color: {accent['border']};
        font-size: 9pt;
        font-weight: bold;
        padding: 2px 4px 2px 4px;
    }}

    /* === Badge === */
    QLabel[Badge="true"] {{
        background-color: rgba(255, 255, 255, 0.06);
        color: {THEME_TEXT_SECONDARY};
        border-radius: 4px;
        padding: 2px 6px;
    }}

    /* === Title === */
    QLabel[Title="true"] {{
        color: {THEME_TEXT_PRIMARY};
        font-weight: bold;
    }}

    /* === Subtitle === */
    QLabel[Subtitle="true"] {{
        color: {THEME_TEXT_SECONDARY};
    }}

    /* === Placeholder === */
    QLabel[PlaceHolder="true"] {{
        color: {THEME_TEXT_SECONDARY};
        padding: 16px;
        text-align: center;
    }}

    /* === App Name Label === */
    #AppName {{
        font-family: "{FONT_FAMILY}";
        font-size: 20pt;
        font-weight: bold;
        color: {THEME_TEXT_PRIMARY};
        background: transparent;
    }}

    /* === Version Label === */
    #Version {{
        background-color: {accent['main_background']};
        color: {THEME_TEXT_PRIMARY};
        font-size: 9pt;
        font-weight: bold;
        padding: 4px 12px;
        border-radius: 10px;
    }}

    /* === Description Label === */
    #Description {{
        color: {THEME_TEXT_SECONDARY};
        font-size: 10pt;
        line-height: 1.5;
        background: transparent;
    }}

    /* === Features Frame === */
    #FeaturesFrame {{
        background-color: {THEME_BG_PRIMARY};
        border-radius: 8px;
        padding: 4px;
    }}

    /* === Features Title Label === */
    #FeaturesTitle {{
        color: {COLOR_LIGHT_BLUE};
        font-size: 10pt;
        font-weight: bold;
        background: transparent;
        margin-bottom: 4px;
    }}

    /* === Created Label === */
    Created {{
        color: {THEME_TEXT_SECONDARY};
        font-size: 9pt;
        background: transparent;
    }}

    /* === Heart Label === */
    #Heart {{
        color: #f7768e;
        font-size: 12px;
        background: transparent;
    }}

    /* === By Label === */
    #By {{
        color: {THEME_TEXT_SECONDARY};
        font-size: 9pt;
        background: transparent;
    }}

    /* === Website Label === */
    #Website {{
        color: {COLOR_LIGHT_BLUE};
        font-size: 9pt;
        text-decoration: none;
        background: transparent;
    }}

    /* === Feature Item Text Label === */
    #FeatureText {{
        color: {THEME_TEXT_SECONDARY};
        font-size: 10pt;
        background: transparent;
    }}
    """
