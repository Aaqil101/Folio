"""Add/edit job dialog: pick an input PDF, freely set the output path.

The output path is validated live (required, .pdf suffix, existing folder)
and an inline warning blocks accept while an error is shown. Mirrors the
Settings dialog conventions (MainLineEdit fields, BrowseButton, Save/Cancel).

Image-set jobs (issue #7) swap the PDF browse row for a read-only summary
plus a Reorder button that reopens ImageSetDialog.
"""

# ----- Built-In Modules -----
from collections.abc import Callable
from pathlib import Path

# ----- PySide6 Modules -----
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QFont, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

# ----- UI Modules -----
from ui.image_set_dialog import ImageSetDialog

# ----- Utils Modules -----
from utils.color import COLOR_GREEN, THEME_TEXT_PRIMARY
from utils.config import config
from utils.hover_button import HoverIconButtonSVG
from utils.resources import get_icon


class JobDialog(QDialog):
    """Edit one queue job: input PDF (or image set) plus an editable output path."""

    def __init__(
        self,
        input_path: str,
        output_path: str,
        suggest: Callable[[str], str] | None = None,
        image_paths: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit job")
        self.setMinimumWidth(560)
        self._suggest = suggest
        self._image_paths: list[str] | None = (
            list(image_paths) if image_paths is not None else None
        )

        self._build_ui()
        if self._image_paths is not None:
            self._refresh_input_display()
        else:
            self.input_edit.setText(input_path)
        self.output_edit.setText(output_path)
        self.output_edit.textChanged.connect(self._update_warning)
        self._update_warning()

    @property
    def _is_image_job(self) -> bool:
        return self._image_paths is not None

    def _build_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # --- Input PDF / image-set row ---
        input_row: QWidget = QWidget()
        input_layout: QHBoxLayout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        input_label: QLabel = QLabel("Images:" if self._is_image_job else "Input PDF:")
        input_label.setMinimumWidth(90)
        input_layout.addWidget(input_label)

        self.input_edit: QLineEdit = QLineEdit()
        self.input_edit.setProperty("MainLineEdit", True)
        self.input_edit.setReadOnly(True)
        input_layout.addWidget(self.input_edit, 1)

        if self._is_image_job:
            reorder_btn: HoverIconButtonSVG = HoverIconButtonSVG(
                normal_icon="file.svg",
                hover_icon="file_filled.svg",
                normal_color=THEME_TEXT_PRIMARY,
                hover_color=THEME_TEXT_PRIMARY,
                icon_size=14,
                text="Reorder...",
            )
            reorder_btn.setProperty("BrowseButton", True)
            reorder_btn.setFixedHeight(32)
            reorder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            reorder_btn.clicked.connect(self._reorder_images)
            input_layout.addWidget(reorder_btn)
        else:
            input_browse: HoverIconButtonSVG = HoverIconButtonSVG(
                normal_icon="file.svg",
                hover_icon="file_filled.svg",
                normal_color=THEME_TEXT_PRIMARY,
                hover_color=THEME_TEXT_PRIMARY,
                icon_size=14,
            )
            input_browse.setProperty("BrowseButton", True)
            input_browse.setFixedHeight(32)
            input_browse.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            input_browse.clicked.connect(self._browse_input)
            input_layout.addWidget(input_browse)

        layout.addWidget(input_row)

        # --- Output PDF row ---
        output_row: QWidget = QWidget()
        output_layout: QHBoxLayout = QHBoxLayout(output_row)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(8)

        output_label: QLabel = QLabel("Output PDF:")
        output_label.setMinimumWidth(90)
        output_layout.addWidget(output_label)

        self.output_edit: QLineEdit = QLineEdit()
        self.output_edit.setProperty("MainLineEdit", True)
        self.output_edit.setPlaceholderText("Path for the finished booklet")
        output_layout.addWidget(self.output_edit, 1)

        output_browse: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="folder_outline.svg",
            hover_icon="folder.svg",
            pressed_icon="folder_open.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_TEXT_PRIMARY,
            pressed_color=THEME_TEXT_PRIMARY,
            icon_size=14,
        )
        output_browse.setProperty("BrowseButton", True)
        output_browse.setFixedHeight(32)
        output_browse.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        output_browse.clicked.connect(self._browse_output)
        output_layout.addWidget(output_browse)

        layout.addWidget(output_row)

        # --- Inline validation warning ---
        self.warning_label: QLabel = QLabel()
        self.warning_label.setObjectName("JobWarningLabel")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        # --- Buttons (mirror SettingsDialog) ---
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
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        cancel_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="cancel_outline.svg",
            hover_icon="cancel_outline.svg",
            pressed_icon="cancel.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_TEXT_PRIMARY,
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

        layout.addLayout(button_layout)

    @property
    def input_path(self) -> str:
        if self._is_image_job:
            return self._image_paths[0] if self._image_paths else ""
        return self.input_edit.text().strip()

    @property
    def image_paths(self) -> list[str] | None:
        """The image set for image jobs; None for PDF jobs."""
        if self._is_image_job:
            return list(self._image_paths or [])
        return None

    @property
    def output_path(self) -> str:
        return self.output_edit.text().strip()

    def _refresh_input_display(self) -> None:
        count = len(self._image_paths or [])
        self.input_edit.setText(f"{count} image{'s' if count != 1 else ''}")
        self.input_edit.setToolTip("\n".join(self._image_paths or []))
        self._update_warning()

    def _reorder_images(self) -> None:
        dialog = ImageSetDialog(self._image_paths or [], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._image_paths = dialog.image_paths
            self._refresh_input_display()

    def _browse_input(self) -> None:
        start: str = ""
        current: str = self.input_path
        if current and Path(current).parent.is_dir():
            start = str(Path(current).parent)
        elif config.default_input_dir and Path(config.default_input_dir).is_dir():
            start = config.default_input_dir
        path, _ = QFileDialog.getOpenFileName(
            self, "Select input PDF", start, "PDF files (*.pdf)"
        )
        if not path:
            return
        old_output: str = self.output_path
        self.input_edit.setText(path)
        # Re-suggest the output only if it is empty or still the old suggestion
        stale_suggestion = False
        if self._suggest:
            try:
                stale_suggestion = bool(current) and old_output == self._suggest(current)
            except ValueError:
                pass
            if not old_output or stale_suggestion:
                self.output_edit.setText(self._suggest(path))
        self._update_warning()

    def _browse_output(self) -> None:
        current: str = self.output_path
        start: str = current
        if current and not Path(current).parent.is_dir():
            start = config.default_output_dir or ""
        elif not current and config.default_output_dir:
            start = config.default_output_dir
        path, _ = QFileDialog.getSaveFileName(
            self, "Choose output path", start, "PDF files (*.pdf)"
        )
        if path:
            self.output_edit.setText(path)

    def _output_error(self) -> str:
        path: str = self.output_path
        if not path:
            return "Output path is required."
        suffix: str = Path(path).suffix
        if suffix and suffix.lower() != ".pdf":
            return "Output must be a .pdf file."
        parent: Path = Path(path).parent
        if str(parent) and not parent.is_dir():
            return f"Folder does not exist: {parent}"
        return ""

    def _validation_message(self) -> str:
        if self._is_image_job:
            if not self._image_paths:
                return "Add at least one image."
            missing = [p for p in self._image_paths if not Path(p).is_file()]
            if missing:
                return f"Image not found: {missing[0]}"
            return self._output_error()
        if not self.input_path:
            return "Choose an input PDF."
        if not Path(self.input_path).is_file():
            return f"Input PDF not found: {self.input_path}"
        return self._output_error()

    def _update_warning(self) -> None:
        message: str = self._validation_message()
        self.warning_label.setText(message)
        self.warning_label.setVisible(bool(message))

    def accept(self) -> None:
        output: str = self.output_path
        if output and not Path(output).suffix:
            self.output_edit.setText(output + ".pdf")
        message: str = self._validation_message()
        if message:
            self._update_warning()
            self.output_edit.setFocus()
            return
        super().accept()
