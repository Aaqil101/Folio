"""
Real settings dialog for Folio: accent, input/output defaults, sheet size,
post-save behavior, and log habits.

Ported from Obsidian-Forge's settings_dialog.py. Persists through
utils.config.Config (per-user JSON in %APPDATA%).
"""

# ----- PySide6 Modules -----
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

# ----- UI Modules -----
from ui.styles.build_styles import build_stylesheet
from ui.widgets import SettingsGroup

# ----- Utils Modules -----
from utils.color import COLOR_GREEN, COLOR_RED, THEME_TEXT_PRIMARY, AccentTheme
from utils.config import config
from utils.constants import APP_NAME, SHEET_SIZES
from utils.hover_button import HoverIconButtonSVG
from utils.resources import get_icon

# Accent choices offered in the picker: (label, config value)
ACCENT_CHOICES: list[tuple[str, str]] = [
    ("Random", "random"),
    ("Blue", "blue"),
    ("Brown", "brown"),
    ("Red", "red"),
    ("Purple", "purple"),
    ("Green", "green"),
    ("Gray", "gray"),
]


class SettingsDialog(QDialog):
    """Dialog for configuring Folio's application settings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Settings - {APP_NAME}")
        self.setMinimumWidth(640)
        self.setMinimumHeight(520)

        self.accent_theme: dict[str, str] = AccentTheme.get()
        self.saved: bool = False

        self.setup_ui()
        self.load_settings()

    def setup_ui(self) -> None:
        self._sections: list[SettingsGroup] = []

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        scroll_area: QScrollArea = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        sections_container: QWidget = QWidget()
        sections_layout: QVBoxLayout = QVBoxLayout(sections_container)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.setSpacing(0)

        # === Appearance section ===
        appearance_section: SettingsGroup = SettingsGroup(
            "Appearance", parent=sections_container
        )
        appearance_content: QWidget = QWidget()
        appearance_layout: QVBoxLayout = QVBoxLayout(appearance_content)
        appearance_layout.setContentsMargins(8, 8, 8, 8)
        appearance_layout.setSpacing(8)

        accent_row: QWidget = QWidget()
        accent_layout: QHBoxLayout = QHBoxLayout(accent_row)
        accent_layout.setContentsMargins(0, 0, 0, 0)
        accent_layout.setSpacing(8)

        accent_label: QLabel = QLabel("Accent color:")
        accent_label.setMinimumWidth(100)
        accent_layout.addWidget(accent_label)

        self.accent_combo: QComboBox = QComboBox()
        for label, value in ACCENT_CHOICES:
            self.accent_combo.addItem(label, value)
        accent_layout.addWidget(self.accent_combo, 1)
        accent_layout.addStretch()

        appearance_layout.addWidget(accent_row)

        accent_info: QLabel = QLabel(
            "Pins the highlight color used across the app.\n"
            "Random picks a fresh accent every launch."
        )
        accent_info.setWordWrap(True)
        appearance_layout.addWidget(accent_info)

        appearance_section.setWidget(appearance_content)
        self._add_section(sections_layout, appearance_section)

        # === Input section ===
        input_section: SettingsGroup = SettingsGroup(
            "Input", parent=sections_container
        )
        input_content: QWidget = QWidget()
        input_layout: QVBoxLayout = QVBoxLayout(input_content)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        input_row, self.input_folder_edit = self._build_folder_row(
            "Default folder:",
            "Leave empty to use the last visited folder",
            self.browse_input_folder,
        )
        input_layout.addWidget(input_row)

        add_folder_row, self.add_folder_edit = self._build_folder_row(
            "Add Folder default:",
            "Leave empty to use the default folder above",
            self.browse_add_folder,
        )
        input_layout.addWidget(add_folder_row)

        view_row: QWidget = QWidget()
        view_row_layout: QHBoxLayout = QHBoxLayout(view_row)
        view_row_layout.setContentsMargins(0, 0, 0, 0)
        view_row_layout.setSpacing(8)

        view_label: QLabel = QLabel("Image set view:")
        view_label.setMinimumWidth(100)
        view_row_layout.addWidget(view_label)

        self.view_mode_combo: QComboBox = QComboBox()
        self.view_mode_combo.addItem("List", "list")
        self.view_mode_combo.addItem("Thumbnails", "thumbnails")
        view_row_layout.addWidget(self.view_mode_combo, 1)
        view_row_layout.addStretch()

        input_layout.addWidget(view_row)

        view_info: QLabel = QLabel(
            "Layout used when arranging the images of an image-set job."
        )
        view_info.setWordWrap(True)
        input_layout.addWidget(view_info)

        input_section.setWidget(input_content)
        self._add_section(sections_layout, input_section)

        # === Output section ===
        output_section: SettingsGroup = SettingsGroup(
            "Output", parent=sections_container
        )
        output_content: QWidget = QWidget()
        output_layout: QVBoxLayout = QVBoxLayout(output_content)
        output_layout.setContentsMargins(8, 8, 8, 8)
        output_layout.setSpacing(12)

        folder_row, self.folder_edit = self._build_folder_row(
            "Default folder:",
            "Leave empty to save next to the input PDF",
            self.browse_output_folder,
        )
        output_layout.addWidget(folder_row)

        template_row: QWidget = QWidget()
        template_layout: QHBoxLayout = QHBoxLayout(template_row)
        template_layout.setContentsMargins(0, 0, 0, 0)
        template_layout.setSpacing(8)

        template_label: QLabel = QLabel("Filename pattern:")
        template_label.setMinimumWidth(100)
        template_layout.addWidget(template_label)

        self.template_edit: QLineEdit = QLineEdit()
        self.template_edit.setProperty("MainLineEdit", True)
        self.template_edit.setPlaceholderText("{stem}_booklet.pdf")
        template_layout.addWidget(self.template_edit, 1)

        output_layout.addWidget(template_row)

        template_info: QLabel = QLabel(
            'Pattern for the suggested output name. {stem} is the input '
            'filename without ".pdf".'
        )
        template_info.setWordWrap(True)
        output_layout.addWidget(template_info)

        self.confirm_overwrite_check: QCheckBox = QCheckBox(
            "Ask before overwriting an existing file"
        )
        self.confirm_overwrite_check.toggled.connect(
            lambda checked: self._set_check_icon(self.confirm_overwrite_check, checked)
        )
        output_layout.addWidget(self.confirm_overwrite_check)

        output_section.setWidget(output_content)
        self._add_section(sections_layout, output_section)

        # === After saving section ===
        after_section: SettingsGroup = SettingsGroup(
            "After saving", parent=sections_container
        )
        after_content: QWidget = QWidget()
        after_layout: QVBoxLayout = QVBoxLayout(after_content)
        after_layout.setContentsMargins(8, 8, 8, 8)
        after_layout.setSpacing(8)

        self.auto_open_check: QCheckBox = QCheckBox("Show the booklet after saving")
        self.auto_open_check.toggled.connect(
            lambda checked: self._set_check_icon(self.auto_open_check, checked)
        )
        self.auto_open_check.toggled.connect(self.open_mode_check_set_enabled)
        after_layout.addWidget(self.auto_open_check)

        self.open_mode_check: QCheckBox = QCheckBox(
            "Open the PDF instead of just revealing it in Explorer"
        )
        self.open_mode_check.toggled.connect(
            lambda checked: self._set_check_icon(self.open_mode_check, checked)
        )
        after_layout.addWidget(self.open_mode_check)

        after_section.setWidget(after_content)
        self._add_section(sections_layout, after_section)

        # === Sheet size section ===
        sheet_section: SettingsGroup = SettingsGroup(
            "Sheet size", parent=sections_container
        )
        sheet_content: QWidget = QWidget()
        sheet_layout: QVBoxLayout = QVBoxLayout(sheet_content)
        sheet_layout.setContentsMargins(8, 8, 8, 8)
        sheet_layout.setSpacing(8)

        sheet_row: QWidget = QWidget()
        sheet_row_layout: QHBoxLayout = QHBoxLayout(sheet_row)
        sheet_row_layout.setContentsMargins(0, 0, 0, 0)
        sheet_row_layout.setSpacing(8)

        sheet_label: QLabel = QLabel("Sheet size:")
        sheet_label.setMinimumWidth(100)
        sheet_row_layout.addWidget(sheet_label)

        self.sheet_combo: QComboBox = QComboBox()
        for name in SHEET_SIZES:
            self.sheet_combo.addItem(name, name)
        sheet_row_layout.addWidget(self.sheet_combo, 1)
        sheet_row_layout.addStretch()

        sheet_layout.addWidget(sheet_row)

        sheet_info: QLabel = QLabel(
            "Landscape paper size of the imposed booklet sheets."
        )
        sheet_info.setWordWrap(True)
        sheet_layout.addWidget(sheet_info)

        sheet_section.setWidget(sheet_content)
        self._add_section(sections_layout, sheet_section)

        # === Log section ===
        log_section: SettingsGroup = SettingsGroup("Log", parent=sections_container)
        log_content: QWidget = QWidget()
        log_layout: QVBoxLayout = QVBoxLayout(log_content)
        log_layout.setContentsMargins(8, 8, 8, 8)
        log_layout.setSpacing(8)

        self.clear_log_check: QCheckBox = QCheckBox("Clear the log before each run")
        self.clear_log_check.toggled.connect(
            lambda checked: self._set_check_icon(self.clear_log_check, checked)
        )
        log_layout.addWidget(self.clear_log_check)

        log_section.setWidget(log_content)
        self._add_section(sections_layout, log_section)

        # === Queue section ===
        queue_section: SettingsGroup = SettingsGroup("Queue", parent=sections_container)
        queue_content: QWidget = QWidget()
        queue_layout: QVBoxLayout = QVBoxLayout(queue_content)
        queue_layout.setContentsMargins(8, 8, 8, 8)
        queue_layout.setSpacing(12)

        self.persist_queue_check: QCheckBox = QCheckBox("Persist job queue across sessions")
        self.persist_queue_check.toggled.connect(
            lambda checked: self._set_check_icon(self.persist_queue_check, checked)
        )
        queue_layout.addWidget(self.persist_queue_check)

        mode_row: QWidget = QWidget()
        mode_layout: QHBoxLayout = QHBoxLayout(mode_row)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(8)

        mode_label: QLabel = QLabel("After queue completes:")
        mode_label.setMinimumWidth(140)
        mode_layout.addWidget(mode_label)

        self.auto_open_mode_combo: QComboBox = QComboBox()
        self.auto_open_mode_combo.addItem("None", "none")
        self.auto_open_mode_combo.addItem("Last booklet", "last")
        self.auto_open_mode_combo.addItem("All booklets", "all")
        mode_layout.addWidget(self.auto_open_mode_combo, 1)

        queue_layout.addWidget(mode_row)

        queue_info: QLabel = QLabel(
            "What to open after the batch queue finishes. "
            "Requires 'Show the booklet after saving' in After saving section."
        )
        queue_info.setWordWrap(True)
        queue_layout.addWidget(queue_info)

        queue_section.setWidget(queue_content)
        self._add_section(sections_layout, queue_section)

        sections_layout.addStretch()

        # Accordion: everything starts collapsed; opening one closes the others
        for section in self._sections:
            section.set_collapsed(True)

        scroll_area.setWidget(sections_container)
        main_layout.addWidget(scroll_area)

        # Buttons
        button_layout: QHBoxLayout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        save_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="save_outline.svg",
            hover_icon="save_filled.svg",
            pressed_icon="save_check_filled.svg",
            normal_color=COLOR_GREEN,
            hover_color=COLOR_GREEN,
            pressed_color=COLOR_GREEN,
            icon_size=14,
            text="&Save",
        )
        save_btn.setFont(QFont(save_btn.font().family(), 10))
        save_btn.setProperty("SaveButton", True)
        save_btn.setFixedHeight(36)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setShortcut(QKeySequence("Ctrl+Return"))
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)

        cancel_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="cancel_outline.svg",
            hover_icon="cancel_outline.svg",
            pressed_icon="cancel.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_TEXT_PRIMARY,
            pressed_color=COLOR_RED,
            icon_size=14,
            text="&Cancel",
        )
        cancel_btn.setFont(QFont(cancel_btn.font().family(), 10))
        cancel_btn.setProperty("CancelButton", True)
        cancel_btn.setFixedHeight(36)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setShortcut(QKeySequence("Esc"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _build_folder_row(
        self,
        label_text: str,
        placeholder: str,
        browse_slot,
    ) -> tuple[QWidget, QLineEdit]:
        """Build a label + line edit + browse button row for a folder setting."""
        row: QWidget = QWidget()
        layout: QHBoxLayout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label: QLabel = QLabel(label_text)
        label.setMinimumWidth(100)
        layout.addWidget(label)

        edit: QLineEdit = QLineEdit()
        edit.setProperty("MainLineEdit", True)
        edit.setPlaceholderText(placeholder)
        layout.addWidget(edit, 1)

        browse_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="folder_outline.svg",
            hover_icon="folder.svg",
            pressed_icon="folder_open.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_TEXT_PRIMARY,
            pressed_color=THEME_TEXT_PRIMARY,
            icon_size=14,
        )
        browse_btn.setProperty("BrowseButton", True)
        browse_btn.setFixedHeight(32)
        browse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        browse_btn.clicked.connect(browse_slot)
        layout.addWidget(browse_btn)

        return row, edit

    def _add_section(self, layout: QVBoxLayout, section: SettingsGroup) -> None:
        """Register a section for accordion behavior and add it to the layout."""
        self._sections.append(section)
        section.collapsed.connect(
            lambda collapsed, s=section: self._on_section_toggled(s, collapsed)
        )
        layout.addWidget(section)

    def _on_section_toggled(self, source: SettingsGroup, collapsed: bool) -> None:
        """Collapse every other section when one is expanded (accordion)."""
        if collapsed:
            return
        for section in self._sections:
            if section is not source:
                section.set_collapsed(True)

    def load_settings(self) -> None:
        """Load persisted settings into the form."""
        index: int = self.accent_combo.findData(config.accent)
        self.accent_combo.setCurrentIndex(index if index >= 0 else 0)

        self.input_folder_edit.setText(config.default_input_dir)
        self.add_folder_edit.setText(config.default_folder_dir)
        view_index: int = self.view_mode_combo.findData(config.image_view_mode)
        self.view_mode_combo.setCurrentIndex(view_index if view_index >= 0 else 0)
        self.folder_edit.setText(config.default_output_dir)
        self.template_edit.setText(config.output_filename_template)
        self.confirm_overwrite_check.setChecked(config.confirm_overwrite)
        self.auto_open_check.setChecked(config.auto_open_output)
        self.open_mode_check.setChecked(config.open_output_mode == "open")
        self.open_mode_check.setEnabled(config.auto_open_output)
        self.clear_log_check.setChecked(config.clear_log_per_run)

        sheet_index: int = self.sheet_combo.findData(config.sheet_size)
        self.sheet_combo.setCurrentIndex(sheet_index if sheet_index >= 0 else 0)

        mode_index: int = self.auto_open_mode_combo.findData(config.auto_open_mode)
        self.auto_open_mode_combo.setCurrentIndex(mode_index if mode_index >= 0 else 1)

        self.persist_queue_check.setChecked(config.persist_queue)

        for check in (
            self.confirm_overwrite_check,
            self.auto_open_check,
            self.open_mode_check,
            self.clear_log_check,
            self.persist_queue_check,
        ):
            self._set_check_icon(check, check.isChecked())

    def browse_input_folder(self) -> None:
        """Open a directory picker for the default input folder."""
        path: str = QFileDialog.getExistingDirectory(
            self,
            "Choose default input folder",
            self.input_folder_edit.text() or "",
        )
        if path:
            self.input_folder_edit.setText(path)

    def browse_add_folder(self) -> None:
        """Open a directory picker for the Add Folder default."""
        path: str = QFileDialog.getExistingDirectory(
            self,
            "Choose default folder for Add Folder",
            self.add_folder_edit.text() or "",
        )
        if path:
            self.add_folder_edit.setText(path)

    def browse_output_folder(self) -> None:
        """Open a directory picker for the default output folder."""
        path: str = QFileDialog.getExistingDirectory(
            self,
            "Choose default output folder",
            self.folder_edit.text() or "",
        )
        if path:
            self.folder_edit.setText(path)

    def open_mode_check_set_enabled(self, checked: bool) -> None:
        """Enable the open-vs-reveal choice only when auto-show is on."""
        self.open_mode_check.setEnabled(checked)

    def _set_check_icon(self, check: QCheckBox, checked: bool) -> None:
        """Swap the checkbox icon to match its state (indicator is hidden)."""
        icon_name: str = "square_check_filled.svg" if checked else "square_check.svg"
        check.setIcon(get_icon(icon_name, color=self.accent_theme["border"]))

    def save_settings(self) -> None:
        """Persist the form and apply accent changes live, then close."""
        previous_accent: str = config.accent
        chosen_accent: str = self.accent_combo.currentData()

        config.accent = chosen_accent
        config.default_input_dir = self.input_folder_edit.text().strip()
        config.default_folder_dir = self.add_folder_edit.text().strip()
        config.image_view_mode = self.view_mode_combo.currentData()
        config.default_output_dir = self.folder_edit.text().strip()
        config.output_filename_template = (
            self.template_edit.text().strip() or "{stem}_booklet.pdf"
        )
        config.confirm_overwrite = self.confirm_overwrite_check.isChecked()
        config.auto_open_output = self.auto_open_check.isChecked()
        config.open_output_mode = (
            "open" if self.open_mode_check.isChecked() else "reveal"
        )
        config.clear_log_per_run = self.clear_log_check.isChecked()
        config.sheet_size = self.sheet_combo.currentData()
        config.persist_queue = self.persist_queue_check.isChecked()
        config.auto_open_mode = self.auto_open_mode_combo.currentData()

        if not config.save_settings():
            return

        if chosen_accent != previous_accent:
            AccentTheme.pin(chosen_accent)
            QApplication.instance().setStyleSheet(build_stylesheet())
            main_window = self.parent()
            if main_window is not None and hasattr(
                main_window, "_refresh_accent_icons"
            ):
                main_window._refresh_accent_icons()

        self.saved = True
        self.accept()
