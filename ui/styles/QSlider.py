# ----- Utils Modules-----
from utils.color import COLOR_DARK_BLUE, COLOR_LIGHT_BLUE, THEME_BORDER


def qss() -> str:
    return f"""
    /* === Slider === */
    QSlider::groove:horizontal {{
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid {THEME_BORDER};
        height: 6px;
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background-color: {COLOR_LIGHT_BLUE};
        border: 2px solid {COLOR_DARK_BLUE};
        width: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}

    QSlider::handle:horizontal:hover {{
        background-color: #FFFFFF;
        border: 2px solid {COLOR_LIGHT_BLUE};
    }}
    """
