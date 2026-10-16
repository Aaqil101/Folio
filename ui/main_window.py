# ----- Built-In Modules -----
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# ----- PySide6 Modules -----
from PySide6.QtCore import (
    QEvent,
    QItemSelection,
    QItemSelectionModel,
    QModelIndex,
    QPoint,
    QRect,
    QSize,
    Qt,
)
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QFontMetrics,
    QKeyEvent,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# ----- Core Modules -----
from core.booklet_imposition import build_booklet
from core.calculation import calculate_pages
from core.image_booklet import (
    IMAGE_EXTENSIONS,
    build_image_booklet,
    collect_images,
    is_image_path,
    natural_sort,
)
from core.page_info import count_pages
from core.verify_booklet import BookletVerificationError

# ----- UI Modules -----
from ui.about_dialog import AboutDialog
from ui.image_set_dialog import ImageSetDialog
from ui.job_dialog import JobDialog
from ui.log_window import LogWindow
from ui.popup_window import PopupIcon, PopupWindow
from ui.reorder import drop_event_moved
from ui.settings import SettingsDialog

# ----- Utils Modules -----
from utils.color import (
    COLOR_GREEN,
    COLOR_RED,
    COLOR_YELLOW,
    THEME_TEXT_PRIMARY,
    AccentTheme,
    accent_selection_bg,
)
from utils.config import config
from utils.constants import SHEET_SIZES
from utils.hover_button import HoverIconButtonSVG
from utils.resources import get_icon

STATUS_TIMEOUT_MS: int = 5000

# Add/drag-drop picker filter: PDFs plus every supported image type
_FILE_DIALOG_FILTER: str = "PDF and image files (*.pdf {extensions})".format(
    extensions=" ".join(f"*{ext}" for ext in sorted(IMAGE_EXTENSIONS))
)


@dataclass
class BookletJob:
    input_path: str
    output_path: str
    input_pages: int | None = None
    image_paths: list[str] | None = None

    @property
    def is_image_job(self) -> bool:
        return bool(self.image_paths)


class _ProgressPipe:
    """Forward build_booklet()'s printed progress lines into the status bar."""

    def __init__(self, window: "MainWindow") -> None:
        self._window = window
        self._original = sys.stdout
        self._buffer = ""

    def __enter__(self) -> "_ProgressPipe":
        sys.stdout = self
        return self

    def __exit__(self, *exc: object) -> None:
        sys.stdout = self._original
        self._show(self._buffer)
        self._buffer = ""

    def write(self, text: str) -> int:
        self._original.write(text)
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._show(line)
        return len(text)

    def flush(self) -> None:
        self._original.flush()

    def _show(self, line: str) -> None:
        line = line.strip()
        if not line:
            return
        status: str = line if len(line) <= 90 else line[:87] + "..."
        self._window._status(status)
        self._window.log_window.append_line(line)
        QApplication.processEvents()


class MainWindow(QMainWindow):
    """Main window: queue multiple PDFs, each with input/output, create booklets in batch."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Folio")
        self.setMinimumSize(700, 500)
        self.setAcceptDrops(True)

        self.jobs: list[BookletJob] = []
        self.log_window: LogWindow = LogWindow(self)
        self._batch_running: bool = False
        self._path_states: list[tuple[bool, bool]] = []

        central: QWidget = QWidget()
        root: QVBoxLayout = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        root.addWidget(self._build_table(), 1)
        root.addLayout(self._build_footer())
        self.setCentralWidget(central)
        self.statusBar()

        self.installEventFilter(self)

        # Alt+Up/Alt+Down move the selected job(s) — wired twice on purpose,
        # same as the image dialog: these window-level shortcuts catch a press
        # even when focus sits on a toolbar button, while the table's
        # keyPressEvent branch covers direct key delivery; each path consumes
        # the event so they never double-fire.
        self._move_shortcuts: list[QShortcut] = []
        for sequence, key in (
            ("Alt+Up", Qt.Key.Key_Up),
            ("Alt+Down", Qt.Key.Key_Down),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(
                lambda k=key: self._move_selected_jobs(-1 if k == Qt.Key.Key_Up else 1)
            )
            self._move_shortcuts.append(shortcut)

        self._load_queue()
        self._refresh_table()

    def _build_header(self) -> QFrame:
        """One header bar: job toolbar left, divider, app buttons right."""
        header: QFrame = QFrame()
        header.setObjectName("HeaderBar")
        header.setFixedHeight(44)

        layout: QHBoxLayout = QHBoxLayout(header)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        accent: dict[str, str] = AccentTheme.get()

        self.add_btn = HoverIconButtonSVG(
            normal_icon="file.svg",
            hover_icon="file_filled.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=accent["border"],
            icon_size=18,
            text=" Add File",
        )
        self.add_btn.setToolTip("Add PDFs or images (Ctrl+N)")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_job)
        layout.addWidget(self.add_btn)

        self.folder_btn = HoverIconButtonSVG(
            normal_icon="folder_outline.svg",
            hover_icon="folder.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=accent["border"],
            icon_size=18,
            text=" Add Folder",
        )
        self.folder_btn.setToolTip("Add a folder of PDFs/images")
        self.folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.folder_btn.clicked.connect(self._add_folder)
        layout.addWidget(self.folder_btn)

        self.edit_btn = HoverIconButtonSVG(
            normal_icon="edit.svg",
            hover_icon="edit.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=accent["border"],
            icon_size=18,
            text=" Edit",
        )
        self.edit_btn.setToolTip("Edit selected job (Enter/F2)")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._edit_selected_job)
        layout.addWidget(self.edit_btn)

        self.delete_btn = HoverIconButtonSVG(
            normal_icon="trash_outline.svg",
            hover_icon="trash.svg",
            normal_color=COLOR_RED,
            hover_color=COLOR_RED,
            icon_size=18,
            text=" Delete",
        )
        self.delete_btn.setToolTip("Delete selected job(s) (Del)")
        self.delete_btn.setProperty("RemoveButton", True)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_selected_jobs)
        layout.addWidget(self.delete_btn)

        self.clear_btn = HoverIconButtonSVG(
            normal_icon="trash_blank.svg",
            hover_icon="trash.svg",
            normal_color=COLOR_RED,
            hover_color=COLOR_RED,
            icon_size=18,
            text=" Clear All",
        )
        self.clear_btn.setToolTip("Clear all jobs")
        self.clear_btn.setProperty("RemoveButton", True)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._clear_all_jobs)
        layout.addWidget(self.clear_btn)

        self.refresh_btn = HoverIconButtonSVG(
            normal_icon="refresh.svg",
            hover_icon="refresh.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=accent["border"],
            icon_size=18,
            text=" Refresh",
        )
        self.refresh_btn.setToolTip("Re-check paths and page counts (F5)")
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.clicked.connect(lambda: self._recheck_paths(recount=True))
        layout.addWidget(self.refresh_btn)

        layout.addStretch()

        divider: QFrame = QFrame()
        divider.setObjectName("HeaderSeparator")
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setFixedHeight(20)
        layout.addWidget(divider)

        settings_button: QToolButton = QToolButton()
        settings_button.setIcon(get_icon("settings.svg"))
        settings_button.setProperty("MainToolButton", True)
        settings_button.setIconSize(QSize(20, 20))
        settings_button.setToolTip("Settings")
        settings_button.setFixedSize(32, 32)
        settings_button.clicked.connect(self._open_settings)
        layout.addWidget(settings_button)

        log_button: QToolButton = QToolButton()
        log_button.setIcon(get_icon("log.svg", color=THEME_TEXT_PRIMARY))
        log_button.setProperty("MainToolButton", True)
        log_button.setIconSize(QSize(20, 20))
        log_button.setToolTip("Log")
        log_button.setFixedSize(32, 32)
        log_button.clicked.connect(self._toggle_log)
        layout.addWidget(log_button)

        about_button: QToolButton = QToolButton()
        about_button.setIcon(get_icon("about.svg"))
        about_button.setProperty("MainToolButton", True)
        about_button.setIconSize(QSize(20, 20))
        about_button.setToolTip("About")
        about_button.setFixedSize(32, 32)
        about_button.clicked.connect(self._open_about)
        layout.addWidget(about_button)

        return header

    class _JobTable(QTableWidget):
        """Table that only allows row reordering, not column reordering."""

        def __init__(self, window: "MainWindow", parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self._window = window

        def dropEvent(self, event: QDropEvent) -> None:
            if not drop_event_moved(self, event):
                super().dropEvent(event)
                return
            self._window._sync_jobs_after_reorder()

        def keyPressEvent(self, event: QKeyEvent) -> None:
            if (
                event.modifiers() & Qt.KeyboardModifier.AltModifier
                and event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down)
            ):
                # Rows are vertical: Alt+Up/Down reorders (matching axis).
                self._window._move_selected_jobs(
                    -1 if event.key() == Qt.Key.Key_Up else 1
                )
                event.accept()
                return
            if event.modifiers() == Qt.KeyboardModifier.NoModifier and event.key() in (
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
                Qt.Key.Key_Left,
                Qt.Key.Key_Right,
            ):
                # Plain arrows walk the rows and wrap at the ends (the highlight
                # loops 1 <-> N); column navigation is useless in this table
                # and made the arrows feel dead at the edges.
                count = self.rowCount()
                if count:
                    row = self.currentIndex().row()
                    if row < 0:
                        row = (
                            0
                            if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Right)
                            else count - 1
                        )
                    elif event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Right):
                        row = (row + 1) % count
                    else:
                        row = (row - 1 + count) % count
                    col = self.currentColumn()
                    self.setCurrentIndex(
                        self.model().index(row, col if col >= 0 else 0)
                    )
                    self.selectRow(row)
                    event.accept()
                    return
            super().keyPressEvent(event)

    class _PathDelegate(QStyledItemDelegate):
        """Two-line path cell: filename on top, dimmed folder below — never truncated."""

        ROW_HEIGHT: int = 40

        def initStyleOption(
            self, option: QStyleOptionViewItem, index: QModelIndex
        ) -> None:
            super().initStyleOption(option, index)
            option.textElideMode = Qt.TextElideMode.ElideMiddle

        def sizeHint(
            self, option: QStyleOptionViewItem, index: QModelIndex
        ) -> QSize:
            return QSize(120, self.ROW_HEIGHT)

        def paint(
            self, painter, option: QStyleOptionViewItem, index: QModelIndex
        ) -> None:
            style = (
                option.widget.style()
                if option.widget is not None
                else QApplication.style()
            )
            selected = bool(option.state & QStyle.StateFlag.State_Selected)
            background = QStyleOptionViewItem(option)
            background.text = ""
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, background, painter)
            if selected:
                # QSS ::item:selected never lands on this custom drawControl path
                # (the native palette highlight shows through instead) — paint the
                # shared opaque selection fill ourselves, under the text below.
                painter.fillRect(option.rect, QColor(accent_selection_bg()))

            text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
            if not text:
                return
            path = Path(text)
            filename: str = path.name
            label = index.data(Qt.ItemDataRole.UserRole + 1)
            if isinstance(label, str) and label:
                filename = label
            folder: str = str(path.parent)

            brush = index.data(Qt.ItemDataRole.ForegroundRole)
            if isinstance(brush, QBrush):
                color = brush.color()
            elif isinstance(brush, QColor):
                color = brush
            else:
                color = QColor(THEME_TEXT_PRIMARY)
            if selected:
                color = QColor(THEME_TEXT_PRIMARY)

            rect = option.rect
            name_font = QFont(option.font)
            folder_font = QFont(option.font)
            if name_font.pointSizeF() > 1:
                folder_font.setPointSizeF(name_font.pointSizeF() - 1)

            painter.save()
            painter.setClipRect(rect)

            painter.setFont(name_font)
            painter.setPen(color)
            name_fm = QFontMetrics(name_font)
            name_rect = QRect(rect.left() + 8, rect.top() + 4, rect.width() - 16, name_fm.height())
            painter.drawText(
                name_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                name_fm.elidedText(filename, Qt.TextElideMode.ElideMiddle, name_rect.width()),
            )

            painter.setFont(folder_font)
            folder_color = QColor(color)
            folder_color.setAlpha(140)
            painter.setPen(folder_color)
            folder_fm = QFontMetrics(folder_font)
            folder_rect = QRect(rect.left() + 8, name_rect.bottom(), rect.width() - 16, folder_fm.height())
            painter.drawText(
                folder_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                folder_fm.elidedText(folder, Qt.TextElideMode.ElideMiddle, folder_rect.width()),
            )

            painter.restore()

    def _build_table(self) -> _JobTable:
        self.table = self._JobTable(self)
        self.table.setObjectName("JobTable")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Input", "Pages", "Output PDF"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionsMovable(
            False
        )  # prevent column reordering
        self.table.setColumnWidth(1, 110)
        path_delegate = self._PathDelegate(self.table)
        self.table.setItemDelegateForColumn(0, path_delegate)
        self.table.setItemDelegateForColumn(2, path_delegate)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        self.table.setDragDropOverwriteMode(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(self._PathDelegate.ROW_HEIGHT)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.installEventFilter(self)

        viewport = self.table.viewport()
        viewport.installEventFilter(self)

        self._empty_label = QLabel(
            "Drag PDFs or images here or click + Add", viewport
        )
        self._empty_label.setObjectName("EmptyStateLabel")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._empty_label.hide()

        return self.table

    def _build_footer(self) -> QHBoxLayout:
        footer: QHBoxLayout = QHBoxLayout()
        footer.setContentsMargins(16, 12, 16, 16)
        footer.setSpacing(12)

        self.status_label = QLabel("0 jobs queued")
        self.status_label.setObjectName("QueueStatusLabel")
        footer.addWidget(self.status_label)

        footer.addStretch()

        accent: dict[str, str] = AccentTheme.get()
        self.generate_btn = HoverIconButtonSVG(
            normal_icon="save_outline.svg",
            hover_icon="save_filled.svg",
            pressed_icon="save_check_filled.svg",
            normal_color=COLOR_GREEN,
            hover_color=COLOR_GREEN,
            pressed_color=COLOR_GREEN,
            icon_size=18,
            text=" Create booklets",
        )
        self.generate_btn.setProperty("SaveButton", True)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.clicked.connect(self._create_booklets)
        footer.addWidget(self.generate_btn)

        return footer

    def _suggested_output(self, input_path: str) -> Path:
        """Suggest an output path for input_path, honouring settings."""
        return self._suggest_from(Path(input_path).stem, input_path)

    def _suggested_image_output(self, image_paths: list[str]) -> Path:
        """Suggest an output path for an image set.

        Uses the shared parent folder's name when every image lives in
        the same folder; otherwise the first image's stem.
        """
        parents = {str(Path(p).parent) for p in image_paths}
        if len(parents) == 1:
            stem: str = Path(image_paths[0]).parent.name or Path(image_paths[0]).stem
        else:
            stem = Path(image_paths[0]).stem
        return self._suggest_from(stem, image_paths[0])

    def _suggest_from(self, stem: str, like_path: str) -> Path:
        """Render the filename template for `stem` next to `like_path`."""
        template: str = config.output_filename_template.strip()
        try:
            name: str = template.format(stem=stem) if template else ""
        except (KeyError, IndexError, ValueError):
            name = ""
        if not name:
            name = f"{stem}_booklet.pdf"
        if not Path(name).suffix:
            name += ".pdf"
        suggested: Path = Path(like_path).with_name(name)
        default_dir: str = config.default_output_dir
        if default_dir and Path(default_dir).is_dir():
            suggested = Path(default_dir) / suggested.name
        return suggested

    @staticmethod
    def _job_input_ok(job: BookletJob) -> bool:
        """True when the job's input PDF / every image in its set exists."""
        if job.image_paths:
            return bool(job.image_paths) and all(
                Path(p).is_file() for p in job.image_paths
            )
        return bool(job.input_path) and Path(job.input_path).is_file()

    def _load_queue(self) -> None:
        if not config.persist_queue:
            return
        cfg = config
        queue_data = cfg.settings.get("job_queue", [])
        for item in queue_data:
            if not (isinstance(item, dict) and "input" in item and "output" in item):
                continue
            images = item.get("images")
            if isinstance(images, list) and images:
                image_paths = [str(p) for p in images]
                self.jobs.append(
                    BookletJob(
                        image_paths[0],
                        item["output"],
                        len(image_paths),
                        image_paths,
                    )
                )
            else:
                self.jobs.append(
                    BookletJob(
                        item["input"], item["output"], count_pages(item["input"])
                    )
                )

    def _save_queue(self) -> None:
        if not config.persist_queue:
            # Drop any previously persisted queue so it cannot linger
            if config.settings.pop("job_queue", None) is not None:
                config.save_settings()
            return
        entries = []
        for job in self.jobs:
            entry = {"input": job.input_path, "output": job.output_path}
            if job.image_paths:
                entry["images"] = list(job.image_paths)
            entries.append(entry)
        config.settings["job_queue"] = entries
        config.save_settings()

    def _refresh_table(self) -> None:
        self.table.setRowCount(len(self.jobs))
        states: list[tuple[bool, bool]] = []
        for row, job in enumerate(self.jobs):
            input_ok: bool = self._job_input_ok(job)
            output_ok: bool = Path(job.output_path).exists()
            states.append((input_ok, output_ok))

            input_item = QTableWidgetItem(job.input_path)
            input_tip = job.input_path
            if job.image_paths:
                rest = len(job.image_paths) - 1
                if rest:
                    input_item.setData(
                        Qt.ItemDataRole.UserRole + 1,
                        f"{Path(job.image_paths[0]).name} +{rest}",
                    )
                input_tip = (
                    f"Image set ({len(job.image_paths)}):\n"
                    + "\n".join(job.image_paths)
                )
            if not input_ok:
                input_item.setForeground(QBrush(QColor(COLOR_RED)))
                input_tip += "\nFile not found."
            input_item.setToolTip(input_tip)
            input_item.setFlags(input_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            input_item.setData(Qt.ItemDataRole.UserRole, id(job))
            self.table.setItem(row, 0, input_item)

            pages_text, pages_tip = self._page_summary(job)
            pages_item = QTableWidgetItem(pages_text)
            pages_item.setToolTip(pages_tip)
            pages_item.setFlags(pages_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            pages_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, pages_item)

            output_item = QTableWidgetItem(job.output_path)
            output_tip = job.output_path
            if output_ok:
                output_item.setForeground(QBrush(QColor(COLOR_YELLOW)))
                output_tip += "\nAlready exists — Folio will ask before overwriting."
            output_item.setToolTip(output_tip)
            output_item.setFlags(output_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, output_item)

        self._path_states = states
        self._update_empty_state()
        self._update_status_label()
        self._update_toolbar_buttons()
        self._update_generate_button()

    def _page_summary(self, job: BookletJob) -> tuple[str, str]:
        """Pages-cell text and tooltip for a job's input page count."""
        if job.input_pages is None:
            return (
                "—",
                "Page count unavailable (missing, corrupt, or password-protected).",
            )
        padded: int = calculate_pages(job.input_pages)
        out_pages: int = padded // 2
        duplex: int = padded // 4
        blanks: int = padded - job.input_pages
        blank_note: str = (
            f" ({blanks} blank{'s' if blanks != 1 else ''})" if blanks else ""
        )
        tooltip: str = (
            f"{job.input_pages} pages → {padded} padded{blank_note} → "
            f"{out_pages} booklet pages → {duplex} duplex sheet{'s' if duplex != 1 else ''}"
        )
        return f"{job.input_pages} → {out_pages}", tooltip

    def _position_empty_label(self) -> None:
        self._empty_label.setGeometry(self.table.viewport().rect())

    def _update_empty_state(self) -> None:
        empty = self.table.rowCount() == 0
        if empty:
            self._position_empty_label()
            self._empty_label.raise_()
        self._empty_label.setVisible(empty)

    def _valid_job_count(self) -> int:
        """Jobs with both paths set whose input PDF / images exist on disk."""
        return sum(
            1
            for j in self.jobs
            if j.input_path and j.output_path and self._job_input_ok(j)
        )

    def _update_status_label(self) -> None:
        count = len(self.jobs)
        valid = self._valid_job_count()
        self.status_label.setText(
            f"{count} job{'s' if count != 1 else ''} queued ({valid} valid)"
        )

    def _update_toolbar_buttons(self) -> None:
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
        has_rows = self.table.rowCount() > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.clear_btn.setEnabled(has_rows)
        self.refresh_btn.setEnabled(has_rows)

    def _update_generate_button(self) -> None:
        self.generate_btn.setEnabled(self._valid_job_count() > 0)

    def _sync_jobs_after_reorder(self) -> None:
        """Reorder self.jobs to match the visual row order after a drag-drop move.

        Rows are matched by the job id stamped in each input item's UserRole
        data, so duplicated jobs (same paths) stay distinct objects.
        """
        jobs_by_id = {id(job): job for job in self.jobs}
        new_jobs: list[BookletJob] = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            job = jobs_by_id.get(item.data(Qt.ItemDataRole.UserRole)) if item else None
            if job is None:
                self._refresh_table()
                return
            new_jobs.append(job)
        if len(new_jobs) == len(self.jobs):
            self.jobs = new_jobs
            self._save_queue()
        # Rebuild so the table matches the new order exactly
        self._refresh_table()

    def _move_selected_jobs(self, delta: int) -> None:
        """Shift the selected jobs one step up (-1) or down (+1).

        When no row of the selection can step freely (every row is at the
        edge or blocked by its own selection neighbour), the whole block
        wraps to the opposite end, keeping its internal order — the queue
        behaves like a ring, same as the image-set dialog.
        """
        if self._batch_running:
            return
        count: int = len(self.jobs)
        if count < 2:
            return
        rows: list[int] = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()}
        )
        if not rows:
            return
        selected: set[int] = set(rows)
        jobs: list[BookletJob] = list(self.jobs)
        # Remember which job the cursor sits on (prefer one inside the
        # selection over a stale current left by earlier navigation) so the
        # next plain arrow steps from there after the rebuild.
        anchor_row: int = self.table.currentIndex().row()
        if anchor_row not in selected:
            anchor_row = min(selected)
        anchor_job: BookletJob = jobs[anchor_row]
        if delta < 0:
            if all(r == 0 or (r - 1) in selected for r in rows):
                # No free step up: send the block to the end.
                block = [jobs[r] for r in rows]
                remaining = [j for i, j in enumerate(jobs) if i not in selected]
                jobs = remaining + block
                selected = set(range(len(remaining), count))
            else:
                for row in rows:  # ascending: each free step up
                    if row == 0 or (row - 1) in selected:
                        continue
                    jobs[row - 1], jobs[row] = jobs[row], jobs[row - 1]
                    selected.discard(row)
                    selected.add(row - 1)
        else:
            if all(r == count - 1 or (r + 1) in selected for r in rows):
                # No free step down: send the block to the front.
                block = [jobs[r] for r in rows]
                remaining = [j for i, j in enumerate(jobs) if i not in selected]
                jobs = block + remaining
                selected = set(range(len(block)))
            else:
                for row in reversed(rows):  # descending: each free step down
                    if row == count - 1 or (row + 1) in selected:
                        continue
                    jobs[row + 1], jobs[row] = jobs[row], jobs[row + 1]
                    selected.discard(row)
                    selected.add(row + 1)
        self.jobs = jobs
        self._save_queue()
        self._refresh_table()
        # Keep the moved jobs selected and the cursor on the same job so the
        # next arrow key steps from there instead of leaping to an end.
        selection = self.table.selectionModel()
        selection.clearSelection()
        flags = (
            QItemSelectionModel.SelectionFlag.Select
            | QItemSelectionModel.SelectionFlag.Rows
        )
        model = self.table.model()
        for row in sorted(selected):
            selection.select(
                QItemSelection(model.index(row, 0), model.index(row, 0)),
                flags,
            )
        new_anchor: int = next(
            (i for i, j in enumerate(jobs) if j is anchor_job), -1
        )
        if new_anchor < 0 and selected:
            new_anchor = max(selected)
        if new_anchor >= 0:
            # NoUpdate via the selection model: setCurrentIndex would
            # replace the selection with the new row.
            selection.setCurrentIndex(
                model.index(new_anchor, 0),
                QItemSelectionModel.SelectionFlag.NoUpdate,
            )

    def _on_selection_changed(self) -> None:
        self._update_toolbar_buttons()

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        if col in (0, 2):
            self._edit_job(row)

    def _show_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        menu.setObjectName("JobContextMenu")
        row = self.table.rowAt(pos.y())

        # Right-clicking an unselected row selects it, so Move Up/Down and
        # the other row actions target what was clicked (a multi-selection
        # that already contains the row is left alone).
        if row >= 0 and row not in {
            index.row() for index in self.table.selectionModel().selectedRows()
        }:
            self.table.clearSelection()
            self.table.selectRow(row)

        add_action = QAction(get_icon("file.svg"), "Add File", self)
        add_action.setShortcut(QKeySequence("Ctrl+N"))
        add_action.triggered.connect(self._add_job)
        menu.addAction(add_action)

        add_folder_action = QAction(get_icon("folder.svg"), "Add Folder", self)
        add_folder_action.triggered.connect(self._add_folder)
        menu.addAction(add_folder_action)

        if row >= 0:
            menu.addSeparator()
            edit_action = QAction(get_icon("edit.svg"), "Edit Job", self)
            edit_action.setShortcut(QKeySequence("Enter"))
            edit_action.triggered.connect(lambda: self._edit_job(row))
            menu.addAction(edit_action)

            if 0 <= row < len(self.jobs) and self.jobs[row].image_paths:
                reorder_action = QAction(
                    get_icon("view_list.svg"), "Reorder Images", self
                )
                reorder_action.triggered.connect(
                    lambda: self._reorder_job_images(row)
                )
                menu.addAction(reorder_action)

            move_up_action = QAction(get_icon("expand_less.svg"), "Move Up", self)
            move_up_action.setShortcut(QKeySequence("Alt+Up"))
            move_up_action.triggered.connect(lambda: self._move_selected_jobs(-1))
            menu.addAction(move_up_action)

            move_down_action = QAction(get_icon("expand_more.svg"), "Move Down", self)
            move_down_action.setShortcut(QKeySequence("Alt+Down"))
            move_down_action.triggered.connect(lambda: self._move_selected_jobs(1))
            menu.addAction(move_down_action)

            dup_action = QAction(get_icon("file_filled.svg"), "Duplicate Job", self)
            dup_action.triggered.connect(lambda: self._duplicate_job(row))
            menu.addAction(dup_action)

            del_action = QAction(get_icon("trash.svg"), "Delete Job", self)
            del_action.setShortcut(QKeySequence("Del"))
            del_action.triggered.connect(lambda: self._delete_job(row))
            menu.addAction(del_action)

        menu.addSeparator()
        refresh_action = QAction(get_icon("refresh.svg"), "Refresh Paths", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(lambda: self._recheck_paths(recount=True))
        menu.addAction(refresh_action)

        clear_action = QAction(get_icon("trash_blank.svg"), "Clear All", self)
        clear_action.triggered.connect(self._clear_all_jobs)
        menu.addAction(clear_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _add_job(self) -> None:
        if self._batch_running:
            return
        start_dir = ""
        if config.default_input_dir and Path(config.default_input_dir).is_dir():
            start_dir = config.default_input_dir
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add PDFs or images to queue", start_dir, _FILE_DIALOG_FILTER
        )
        if not paths:
            return
        self._ingest_paths(paths)

    def _add_folder(self) -> None:
        if self._batch_running:
            return
        start_dir = ""
        preferred = config.default_folder_dir or config.default_input_dir
        if preferred and Path(preferred).is_dir():
            start_dir = preferred
        folder = QFileDialog.getExistingDirectory(self, "Add folder", start_dir)
        if not folder:
            return
        self._ingest_paths([folder])

    @staticmethod
    def _expand_folder(folder: Path) -> list[str]:
        """Folder contents as ingestible paths: PDFs (natural-sorted) then images."""
        pdfs = natural_sort(
            [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"]
        )
        images = collect_images([str(folder)])
        return [str(p) for p in pdfs + images]

    def _ingest_paths(self, paths: list[str]) -> None:
        """Turn picked/dropped files and folders into queue jobs.

        Folders expand recursively: PDFs become one job each, images are
        grouped into a single image-set job (AC: one imposed PDF per set)
        after a reorder pass. A folder with nothing supported is reported
        in the status bar.
        """
        files: list[str] = []
        empty_folders: list[str] = []
        for entry in paths:
            path = Path(entry)
            if not path.is_dir():
                files.append(entry)
                continue
            expanded = self._expand_folder(path)
            if expanded:
                files.extend(expanded)
            else:
                empty_folders.append(path.name)
        pdfs = [p for p in files if not is_image_path(p)]
        images = [str(p) for p in natural_sort([Path(p) for p in files if is_image_path(p)])]
        for path in pdfs:
            output = str(self._suggested_output(path))
            self.jobs.append(BookletJob(path, output, count_pages(path)))
        if images:
            self._prompt_image_job(images)
        self._refresh_table()
        self._save_queue()
        if empty_folders:
            self._status(
                "No PDFs or images in: " + ", ".join(empty_folders)
            )

    def _prompt_image_job(self, image_paths: list[str]) -> None:
        """Open the reorder dialog and enqueue one job for the image set."""
        dialog = ImageSetDialog(image_paths, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        ordered: list[str] = dialog.image_paths
        output = str(self._suggested_image_output(ordered))
        self.jobs.append(
            BookletJob(ordered[0], output, len(ordered), ordered)
        )

    def _reorder_job_images(self, row: int) -> None:
        """Reopen the reorder dialog for an existing image-set job."""
        if self._batch_running or not (0 <= row < len(self.jobs)):
            return
        job = self.jobs[row]
        if not job.image_paths:
            return
        dialog = ImageSetDialog(job.image_paths, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        ordered: list[str] = dialog.image_paths
        if not ordered:
            return
        job.image_paths = ordered
        job.input_path = ordered[0]
        job.input_pages = len(ordered)
        self._refresh_table()
        self._save_queue()

    def _edit_job(self, row: int) -> None:
        if row < 0 or row >= len(self.jobs):
            return
        job = self.jobs[row]

        dialog = JobDialog(
            job.input_path,
            job.output_path,
            suggest=lambda path: str(self._suggested_output(path)),
            image_paths=job.image_paths,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        job.image_paths = dialog.image_paths
        job.input_path = dialog.input_path
        job.output_path = dialog.output_path
        if job.image_paths:
            job.input_pages = len(job.image_paths)
        else:
            job.input_pages = count_pages(job.input_path)
        self._refresh_table()
        self._save_queue()

    def _edit_selected_job(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            self._edit_job(rows[0].row())

    def _duplicate_job(self, row: int) -> None:
        if row < 0 or row >= len(self.jobs):
            return
        job = self.jobs[row]
        self.jobs.insert(
            row + 1,
            BookletJob(
                job.input_path,
                job.output_path,
                job.input_pages,
                list(job.image_paths) if job.image_paths else None,
            ),
        )
        self._refresh_table()
        self._save_queue()

    def _delete_job(self, row: int) -> None:
        if 0 <= row < len(self.jobs):
            del self.jobs[row]
            self._refresh_table()
            self._save_queue()

    def _delete_selected_jobs(self) -> None:
        if self._batch_running:
            return
        rows = sorted(
            [r.row() for r in self.table.selectionModel().selectedRows()], reverse=True
        )
        for row in rows:
            if 0 <= row < len(self.jobs):
                del self.jobs[row]
        self._refresh_table()
        self._save_queue()

    def _clear_all_jobs(self) -> None:
        if not self.jobs:
            return
        reply = QMessageBox.question(
            self,
            "Clear all jobs",
            "Remove all jobs from the queue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.jobs.clear()
            self._refresh_table()
            self._save_queue()

    def _status(self, message: str) -> None:
        """Show a transient status-bar message; clears after STATUS_TIMEOUT_MS."""
        self.statusBar().showMessage(message, STATUS_TIMEOUT_MS)

    def _recheck_paths(self, recount: bool) -> None:
        """Re-validate job paths, optionally re-counting input pages.

        Auto re-checks (recount=False, window focus) only rebuild the table
        when an existence state actually changed, so a selection isn't lost
        on every focus gain. Manual refreshes (button, menu, F5) always
        rebuild and refresh the Pages column. Auto reports only on change
        (and clears a resolved warning); manual always reports.
        """
        if self._batch_running:
            return
        missing: int = 0
        states: list[tuple[bool, bool]] = []
        for job in self.jobs:
            input_ok: bool = self._job_input_ok(job)
            states.append((input_ok, Path(job.output_path).exists()))
            if not input_ok:
                missing += 1
                job.input_pages = None
            elif recount:
                if job.image_paths:
                    job.input_pages = len(job.image_paths)
                else:
                    job.input_pages = count_pages(job.input_path)

        changed: bool = states != self._path_states
        if recount or changed:
            self._refresh_table()

        total: int = len(self.jobs)
        if missing and (recount or changed):
            self._status(
                f"Checked {total} job{'s' if total != 1 else ''} — "
                f"{missing} file{'s' if missing != 1 else ''} missing"
            )
        elif recount and total:
            self._status(
                f"Checked {total} job{'s' if total != 1 else ''} — all files found"
            )
        elif changed and not recount:
            self.statusBar().clearMessage()

    def _create_booklets(self) -> None:
        if self._batch_running:
            return
        valid_jobs = [j for j in self.jobs if j.input_path and j.output_path]
        if not valid_jobs:
            return

        # Guard against re-entry: _ProgressPipe pumps processEvents() mid-build
        self._batch_running = True
        self.table.setEnabled(False)
        self.add_btn.setEnabled(False)
        self.folder_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)

        try:
            if config.clear_log_per_run:
                self.log_window.clear()

            sheet_size = SHEET_SIZES.get(config.sheet_size, SHEET_SIZES["A4"])
            successes: list[BookletJob] = []

            for i, job in enumerate(valid_jobs, 1):
                job_label: str = (
                    f"{len(job.image_paths)} images"
                    if job.image_paths
                    else Path(job.input_path).name
                )
                self._status(f"Processing {i}/{len(valid_jobs)}: {job_label}")
                QApplication.processEvents()

                stamp = datetime.now().strftime("%H:%M:%S")
                self.log_window.append_line(
                    f"=== [{i}/{len(valid_jobs)}] Creating booklet from {job_label} ({stamp}) ==="
                )

                if config.confirm_overwrite and Path(job.output_path).exists():
                    confirm = PopupWindow(
                        message=f"{Path(job.output_path).name} already exists.\nOverwrite it?",
                        title="Overwrite existing file?",
                        icon=PopupIcon.WARNING,
                        parent=self,
                    )
                    if confirm.exec() != QDialog.DialogCode.Accepted:
                        self.log_window.append_line(
                            f"SKIPPED: {job.input_path} (user cancelled overwrite)"
                        )
                        self._status(f"Skipped {job.input_path}")
                        continue

                try:
                    with _ProgressPipe(self):
                        if job.image_paths:
                            build_image_booklet(
                                job.image_paths,
                                job.output_path,
                                sheet_size=sheet_size,
                            )
                        else:
                            build_booklet(
                                job.input_path,
                                job.output_path,
                                sheet_size=sheet_size,
                            )
                except BookletVerificationError as error:
                    self.log_window.append_line(f"FAILED: {job.input_path} — {error}")
                    PopupWindow(
                        message=f"{error}\n\nThe booklet was not saved. Fix the source PDF and try again.",
                        title="Verification failed",
                        icon=PopupIcon.ERROR,
                        info_popup=True,
                        parent=self,
                    ).exec()
                    continue
                except Exception as error:
                    self.log_window.append_line(f"ERROR: {job.input_path} — {error}")
                    PopupWindow(
                        message=str(error) or repr(error),
                        title="Could not create booklet",
                        icon=PopupIcon.ERROR,
                        info_popup=True,
                        parent=self,
                    ).exec()
                    continue

                successes.append(job)
                self.log_window.append_line(
                    f"SUCCESS: Booklet saved to {job.output_path}"
                )

            if not successes:
                self._status("Queue completed — no booklets created")
                return

            self._status(
                f"Queue completed — {len(successes)}/{len(valid_jobs)} booklets created"
            )

            if config.auto_open_output and successes:
                mode = config.auto_open_mode
                targets = []
                if mode == "last":
                    targets = [successes[-1]]
                elif mode == "all":
                    targets = successes

                for job in targets:
                    if config.open_output_mode == "open":
                        self._open_with_default_app(job.output_path)
                    else:
                        self._reveal_in_explorer(job.output_path)
        finally:
            self._batch_running = False
            self.table.setEnabled(True)
            self.add_btn.setEnabled(True)
            self.folder_btn.setEnabled(True)
            self._update_toolbar_buttons()
            self._update_generate_button()

    @staticmethod
    def _reveal_in_explorer(path: str) -> None:
        target: Path = Path(path).resolve()
        if os.name == "nt":
            try:
                subprocess.Popen(["explorer", "/select,", str(target)])
                return
            except OSError:
                pass
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target.parent)))

    @staticmethod
    def _open_with_default_app(path: str) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).resolve())))

    def _refresh_accent_icons(self) -> None:
        accent = AccentTheme.get()
        for btn in (
            self.add_btn,
            self.folder_btn,
            self.edit_btn,
            self.delete_btn,
            self.clear_btn,
            self.refresh_btn,
        ):
            btn.hover_color = accent["border"]
            btn.pressed_color = accent["border"]
            btn.hover_icon = get_icon(btn.hover_icon_name, color=accent["border"])
            btn.pressed_icon = get_icon(btn.pressed_icon_name, color=accent["border"])
        self.generate_btn.hover_color = COLOR_GREEN

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()
        if dialog.saved:
            self._refresh_table()

    def _toggle_log(self) -> None:
        if self.log_window.isVisible():
            self.log_window.hide()
        else:
            self.log_window.show()
            self.log_window.raise_()

    @staticmethod
    def _files_from_mime(mime) -> list[str]:
        """Local folders, PDFs and image paths from a drag-drop mime payload."""
        return [
            url.toLocalFile()
            for url in mime.urls()
            if url.isLocalFile()
            and (
                Path(url.toLocalFile()).is_dir()
                or url.toLocalFile().lower().endswith(".pdf")
                or is_image_path(url.toLocalFile())
            )
        ]

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._files_from_mime(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        files = self._files_from_mime(event.mimeData())
        if not files:
            event.ignore()
            return
        self._ingest_paths(files)
        event.acceptProposedAction()

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Type.WindowActivate:
            self._recheck_paths(recount=False)
            return False
        if obj is self.table.viewport() and event.type() == QEvent.Type.Resize:
            self._position_empty_label()
            return False
        if obj in (self, self.table) and event.type() == QEvent.Type.KeyPress:
            # A modal dialog (edit job, popups) owns keyboard input
            if QApplication.activeModalWidget() is not None:
                return False
            key = event.key()
            modifiers = event.modifiers()
            if (
                key in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                and modifiers & Qt.KeyboardModifier.ControlModifier
            ):
                self._create_booklets()
                return True
            if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self._delete_selected_jobs()
                return True
            if key == Qt.Key.Key_N and modifiers & Qt.KeyboardModifier.ControlModifier:
                self._add_job()
                return True
            if key == Qt.Key.Key_F5:
                self._recheck_paths(recount=True)
                return True
            if key in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_F2):
                rows = self.table.selectionModel().selectedRows()
                if rows:
                    self._edit_job(rows[0].row())
                return True
        return super().eventFilter(obj, event)
