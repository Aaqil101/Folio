"""
Configuration manager for Folio.
Handles per-user settings persisted as JSON under %APPDATA%, keyed by the
OS username. Ported from Obsidian-Forge's src/core/config.py.
"""

# ----- Built-In Modules -----
import json
import os
from pathlib import Path

# ----- Utils Modules -----
from utils.constants import APP_NAME


class Config:
    """Configuration manager: JSON settings keyed by OS username."""

    def __init__(self) -> None:
        # Get username and sanitize it
        self.username: str = (
            os.getlogin().replace(" ", "_").replace("\\", "_").replace("/", "_")
        )

        # Use %APPDATA%/Folio/ directory
        appdata = os.getenv("APPDATA")
        if appdata:
            self.config_dir: Path = Path(appdata) / APP_NAME
        else:
            # Fallback to user home if APPDATA is not set
            self.config_dir = Path.home() / ".folio"

        # Single shared config file
        self.config_file: Path = self.config_dir / "settings.json"
        self.all_settings = self._load_all_settings()
        self.settings = self.all_settings["users"].get(
            self.username, self._default_settings()
        )

        # Ensure current user exists in settings
        if self.username not in self.all_settings["users"]:
            self.all_settings["users"][self.username] = self.settings
            self.save_settings()

    def _load_all_settings(self) -> dict:
        """Load all settings from shared config file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Ensure structure exists
                    if "users" not in data:
                        return self._create_new_config_structure()
                    if "version" not in data:
                        data["version"] = "1.0"
                    return data
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._create_new_config_structure()
        return self._create_new_config_structure()

    def _create_new_config_structure(self) -> dict:
        """Create new config structure with version and users."""
        return {"version": "1.0", "users": {}}

    def _default_settings(self) -> dict:
        """Return default settings."""
        return {
            "accent": "random",
            "default_output_dir": "",
            "default_input_dir": "",
            "default_folder_dir": "",
            "image_view_mode": "list",
            "auto_open_output": False,
            "open_output_mode": "reveal",
            "output_filename_template": "{stem}_booklet.pdf",
            "confirm_overwrite": True,
            "clear_log_per_run": False,
            "sheet_size": "A4",
            "persist_queue": False,
            "auto_open_mode": "last",
        }

    def _increment_version(self) -> None:
        """Increment the version number."""
        try:
            current = self.all_settings.get("version", "1.0")
            major, minor = current.split(".")
            minor = str(int(minor) + 1)
            self.all_settings["version"] = f"{major}.{minor}"
        except Exception:
            # If version parsing fails, just increment a counter
            self.all_settings["version"] = "1.0"

    def save_settings(self) -> bool:
        """Save current settings to shared config file."""
        try:
            # Update current user's settings in the all_settings structure
            self.all_settings["users"][self.username] = self.settings

            # Increment version on each save
            self._increment_version()

            # Save to file
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.all_settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    @property
    def accent(self) -> str:
        """Get accent theme choice ('random' or a pinned accent name)."""
        return self.settings.get("accent", "random")

    @accent.setter
    def accent(self, value: str) -> None:
        """Set accent theme choice."""
        self.settings["accent"] = value

    @property
    def default_output_dir(self) -> str:
        """Get default output folder ('' = next to the input PDF)."""
        return self.settings.get("default_output_dir", "")

    @default_output_dir.setter
    def default_output_dir(self, path: str) -> None:
        """Set default output folder."""
        self.settings["default_output_dir"] = path

    @property
    def default_input_dir(self) -> str:
        """Get default start folder for the Open PDF dialog ('' = OS default)."""
        return self.settings.get("default_input_dir", "")

    @default_input_dir.setter
    def default_input_dir(self, path: str) -> None:
        """Set default start folder for the Open PDF dialog."""
        self.settings["default_input_dir"] = path

    @property
    def default_folder_dir(self) -> str:
        """Get default start folder for the Add Folder dialog ('' = fallback)."""
        return self.settings.get("default_folder_dir", "")

    @default_folder_dir.setter
    def default_folder_dir(self, path: str) -> None:
        """Set default start folder for the Add Folder dialog."""
        self.settings["default_folder_dir"] = path

    @property
    def image_view_mode(self) -> str:
        """Get image-set dialog layout: 'list' or 'thumbnails'."""
        value = self.settings.get("image_view_mode", "list")
        return value if value in ("list", "thumbnails") else "list"

    @image_view_mode.setter
    def image_view_mode(self, value: str) -> None:
        """Set image-set dialog layout."""
        if value not in ("list", "thumbnails"):
            value = "list"
        self.settings["image_view_mode"] = value

    @property
    def auto_open_output(self) -> bool:
        """Get whether to reveal the booklet after a successful run."""
        return self.settings.get("auto_open_output", False)

    @auto_open_output.setter
    def auto_open_output(self, value: bool) -> None:
        """Set whether to reveal the booklet after a successful run."""
        self.settings["auto_open_output"] = value

    @property
    def open_output_mode(self) -> str:
        """Get post-save action: 'reveal' (Explorer) or 'open' (default app)."""
        return self.settings.get("open_output_mode", "reveal")

    @open_output_mode.setter
    def open_output_mode(self, value: str) -> None:
        """Set post-save action: 'reveal' or 'open'."""
        self.settings["open_output_mode"] = value

    @property
    def output_filename_template(self) -> str:
        """Get the output filename pattern ('{stem}' is the input filename stem)."""
        return self.settings.get("output_filename_template", "{stem}_booklet.pdf")

    @output_filename_template.setter
    def output_filename_template(self, value: str) -> None:
        """Set the output filename pattern."""
        self.settings["output_filename_template"] = value

    @property
    def confirm_overwrite(self) -> bool:
        """Get whether to ask before overwriting an existing output file."""
        return self.settings.get("confirm_overwrite", True)

    @confirm_overwrite.setter
    def confirm_overwrite(self, value: bool) -> None:
        """Set whether to ask before overwriting an existing output file."""
        self.settings["confirm_overwrite"] = value

    @property
    def clear_log_per_run(self) -> bool:
        """Get whether to reset the log window before each booklet run."""
        return self.settings.get("clear_log_per_run", False)

    @clear_log_per_run.setter
    def clear_log_per_run(self, value: bool) -> None:
        """Set whether to reset the log window before each booklet run."""
        self.settings["clear_log_per_run"] = value

    @property
    def sheet_size(self) -> str:
        """Get output sheet size name (key into SHEET_SIZES)."""
        return self.settings.get("sheet_size", "A4")

    @sheet_size.setter
    def sheet_size(self, value: str) -> None:
        """Set output sheet size name."""
        self.settings["sheet_size"] = value

    @property
    def persist_queue(self) -> bool:
        """Get whether to persist the job queue across sessions."""
        return self.settings.get("persist_queue", False)

    @persist_queue.setter
    def persist_queue(self, value: bool) -> None:
        """Set whether to persist the job queue across sessions."""
        self.settings["persist_queue"] = value

    @property
    def auto_open_mode(self) -> str:
        """Get auto-open mode after queue: 'none', 'last', or 'all'."""
        return self.settings.get("auto_open_mode", "last")

    @auto_open_mode.setter
    def auto_open_mode(self, value: str) -> None:
        """Set auto-open mode after queue."""
        if value not in ("none", "last", "all"):
            value = "last"
        self.settings["auto_open_mode"] = value


# Shared instance used across the app
config = Config()
