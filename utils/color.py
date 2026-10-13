"""
Tokyo Night color palette for Obsidian Forge.
Based on GitUI's Tokyo Night theme.
"""

# ----- Built-In Modules -----
import random

# ══════════════════════════════════════════════════════════════════
# THEME - TOKYO NIGHT
# ══════════════════════════════════════════════════════════════════
THEME_BG_PRIMARY = "#232323"
THEME_BG_SECONDARY = "#282828"
THEME_TEXT_PRIMARY = "#E6E6E6"
THEME_TEXT_SECONDARY = "#AAAAAA"
THEME_BORDER = "#414868"

# Color Accents
COLOR_LIGHT_BLUE = "#7aa2f7"
COLOR_DARK_BLUE = "#0078d7"
COLOR_CYAN = "#7dcfff"
COLOR_GREEN = "#9ece6a"
COLOR_YELLOW = "#e0af68"
COLOR_ORANGE = "#ff9e64"
COLOR_RED = "#f7768e"
COLOR_PURPLE = "#bb9af7"

# Status Colors
COLOR_SUCCESS = "#9ece6a"
COLOR_FAILED = "#f7768e"
COLOR_PENDING = "#e0af68"
COLOR_QUEUED = "#7aa2f7"
COLOR_SCANNING = "#7dcfff"
COLOR_COMPLETE = "#9ece6a"


# ══════════════════════════════════════════════════════════════════
# ACCENT THEME - Dynamic Color Variations
# ══════════════════════════════════════════════════════════════════
class AccentTheme:
    """Accent color theme provider with background and border variations.

    Provides a shared random accent color theme that's consistent across the entire app.
    The theme is chosen once on first access and reused throughout the session.
    """

    BLUE: dict[str, str] = {
        "main_background": "rgba(83, 144, 247, 0.2)",
        "hover_background": "rgba(83, 144, 247, 0.3)",
        "pressed_background": "rgba(83, 144, 247, 0.4)",
        "border": "rgb(83, 144, 247)",
    }
    BROWN: dict[str, str] = {
        "main_background": "rgba(255, 166, 75, 0.2)",
        "hover_background": "rgba(255, 166, 75, 0.3)",
        "pressed_background": "rgba(255, 166, 75, 0.4)",
        "border": "rgb(255, 166, 75)",
    }
    RED: dict[str, str] = {
        "main_background": "rgba(225, 80, 69, 0.2)",
        "hover_background": "rgba(225, 80, 69, 0.3)",
        "pressed_background": "rgba(225, 80, 69, 0.4)",
        "border": "rgb(225, 80, 69)",
    }
    PURPLE: dict[str, str] = {
        "main_background": "rgba(153, 116, 248, 0.2)",
        "hover_background": "rgba(153, 116, 248, 0.3)",
        "pressed_background": "rgba(153, 116, 248, 0.4)",
        "border": "rgb(153, 116, 248)",
    }
    GREEN: dict[str, str] = {
        "main_background": "rgba(89, 143, 76, 0.2)",
        "hover_background": "rgba(89, 143, 76, 0.3)",
        "pressed_background": "rgba(89, 143, 76, 0.4)",
        "border": "rgb(89, 143, 76)",
    }
    GRAY: dict[str, str] = {
        "main_background": "rgba(151, 151, 151, 0.2)",
        "hover_background": "rgba(151, 151, 151, 0.3)",
        "pressed_background": "rgba(151, 151, 151, 0.4)",
        "border": "rgb(151, 151, 151)",
    }

    # Shared instance - initialized once on first access
    _shared_theme: dict[str, str] | None = None

    @staticmethod
    def get() -> dict[str, str]:
        """Get the app's accent color theme.

        Returns the same random theme for the entire app session.
        The theme is chosen once on first call and cached.
        """
        if AccentTheme._shared_theme is None:
            AccentTheme._shared_theme = random.choice(
                [
                    AccentTheme.BLUE,
                    AccentTheme.BROWN,
                    AccentTheme.RED,
                    AccentTheme.PURPLE,
                    AccentTheme.GREEN,
                    AccentTheme.GRAY,
                ]
            )
        return AccentTheme._shared_theme

    @staticmethod
    def pin(name: str) -> None:
        """Pin a named accent for this session (issue #12).

        Call before the first get() to force a specific theme; pass
        'random' (or any unknown name) to clear the pin and let get()
        choose freshly on next access.
        """
        accents: dict[str, dict[str, str]] = {
            "blue": AccentTheme.BLUE,
            "brown": AccentTheme.BROWN,
            "red": AccentTheme.RED,
            "purple": AccentTheme.PURPLE,
            "green": AccentTheme.GREEN,
            "gray": AccentTheme.GRAY,
        }
        AccentTheme._shared_theme = accents.get(name.lower())
