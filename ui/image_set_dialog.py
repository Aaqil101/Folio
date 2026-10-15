"""Image-set dialog: review and reorder the images of one queue job (issue #7).

Opened whenever images enter the queue (Add picker or drag & drop) and
again when editing an image job. Images default to natural filename order;
the user drags rows (list view) or tiles (thumbnail view) to reorder,
nudges the selection with Alt+Left/Alt+Right or the move buttons,
adds/removes images, or re-sorts by name. The returned order is the page
order of the booklet. The opening layout follows config.image_view_mode
("list" or "thumbnails"); toggling inside the dialog does not persist.
"""

# ----- Built-In Modules -----
from pathlib import Path

# ----- PySide6 Modules -----
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QSize, Qt
from PySide6.QtGui import (
    QCursor,
    QDropEvent,
    QFont,
    QImage,
    QKeyEvent,
    QKeySequence,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# ----- Pillow Modules -----
from PIL import Image, ImageOps

# ----- Core Modules -----
from core.image_booklet import IMAGE_EXTENSIONS, _read_image_meta, natural_sort

# ----- UI Modules -----
from ui.reorder import drop_event_moved, drop_event_moved_grid

# ----- Utils Modules -----
from utils.color import COLOR_GREEN, THEME_TEXT_PRIMARY
from utils.config import config
from utils.hover_button import HoverIconButtonSVG
from utils.resources import get_icon

# Shared file-dialog filter: "Images (*.jpg *.png ...)"
IMAGE_FILTER: str = "Image files ({extensions})".format(
    extensions=" ".join(f"*{ext}" for ext in sorted(IMAGE_EXTENSIONS))
)

THUMBNAIL_SIZE: int = 96

# One grid cell: icon + margins horizontally, icon + filename lines vertically.
# Used for both setGridSize() and each item's sizeHint — an invalid sizeHint
# makes QListView compute a too-small rect (icon + label get clipped).
TILE_SIZE = QSize(THUMBNAIL_SIZE + 24, THUMBNAIL_SIZE + 44)


class _ImageTable(QTableWidget):
    """Table that only allows row reordering, not column reordering."""

    def __init__(self, dialog: "ImageSetDialog", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dialog = dialog

    def dropEvent(self, event: QDropEvent) -> None:
        if not drop_event_moved(self, event):
            super().dropEvent(event)
            return
        self._dialog._renumber()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if (
            event.modifiers() & Qt.KeyboardModifier.AltModifier
            and event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right)
        ):
            self._dialog._move_selected(
                -1 if event.key() == Qt.Key.Key_Left else 1
            )
            event.accept()
            return
        super().keyPressEvent(event)


class _ImageGrid(QListWidget):
    """Icon-mode grid that reorders tiles on drop (Static movement)."""

    def __init__(self, dialog: "ImageSetDialog", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dialog = dialog

    def dropEvent(self, event: QDropEvent) -> None:
        # No super() fallback: InternalMove already rejects external drags in
        # dragEnterEvent, and QListView::dropEvent hard-crashes on a foreign
        # source event (verified offscreen) — ignore anything unhandled.
        if not drop_event_moved_grid(self, event):
            event.ignore()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if (
            event.modifiers() & Qt.KeyboardModifier.AltModifier
            and event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right)
        ):
            self._dialog._move_selected(
                -1 if event.key() == Qt.Key.Key_Left else 1
            )
            event.accept()
            return
        super().keyPressEvent(event)


class ImageSetDialog(QDialog):
    """Order a set of images; accepted order becomes the booklet's pages."""

    def __init__(self, paths: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Arrange images")
        self.setMinimumSize(940, 620)

        self._view_mode: str = config.image_view_mode
        self._thumb_cache: dict[str, QPixmap | None] = {}

        self._build_ui()
        self._apply_paths(
            [str(p) for p in natural_sort([Path(p) for p in paths])]
        )

    # ----- UI -----

    def _build_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        hint: QWidget = QWidget()
        hint_layout: QHBoxLayout = QHBoxLayout(hint)
        hint_layout.setContentsMargins(0, 0, 0, 0)
        hint_label: QLabel = QLabel(
            "Drag to set the booklet page order. "
            "The first item becomes page 1."
        )
        hint_layout.addWidget(hint_label)
        hint_layout.addStretch()

        self.list_btn: QToolButton = QToolButton(hint)
        self.list_btn.setCheckable(True)
        self.list_btn.setAutoExclusive(True)
        self.list_btn.setIcon(get_icon("view_list.svg", color=THEME_TEXT_PRIMARY))
        self.list_btn.setIconSize(QSize(16, 16))
        self.list_btn.setToolTip("List view")
        self.list_btn.setProperty("ViewToggle", True)
        self.list_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.list_btn.clicked.connect(lambda: self._set_view("list"))
        hint_layout.addWidget(self.list_btn)

        self.thumb_btn: QToolButton = QToolButton(hint)
        self.thumb_btn.setCheckable(True)
        self.thumb_btn.setAutoExclusive(True)
        self.thumb_btn.setIcon(
            get_icon("view_thumbnail.svg", color=THEME_TEXT_PRIMARY)
        )
        self.thumb_btn.setIconSize(QSize(16, 16))
        self.thumb_btn.setToolTip("Thumbnail view")
        self.thumb_btn.setProperty("ViewToggle", True)
        self.thumb_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.thumb_btn.clicked.connect(lambda: self._set_view("thumbnails"))
        hint_layout.addWidget(self.thumb_btn)

        self.list_btn.setChecked(self._view_mode == "list")
        self.thumb_btn.setChecked(self._view_mode == "thumbnails")

        layout.addWidget(hint)

        self._stack: QStackedWidget = QStackedWidget()

        self.table = _ImageTable(self)
        self.table.setObjectName("ImageSetTable")
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Filename", "Size", "DPI"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionsMovable(False)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 70)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        self.table.setDragDropOverwriteMode(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._stack.addWidget(self.table)

        self.grid: _ImageGrid = _ImageGrid(self)
        self.grid.setObjectName("ImageSetGrid")
        self.grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.grid.setFlow(QListWidget.Flow.LeftToRight)
        self.grid.setWrapping(True)
        self.grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.grid.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        # IconMode defaults to Free movement: the tile follows the cursor
        # anywhere and stays where it is dropped instead of re-flowing into
        # the grid. Static keeps every tile locked in its cell; a drop only
        # reorders the model and the view re-lays the grid out itself.
        # IMPORTANT: setMovement(Static) resets dragEnabled/dragDropMode in
        # Qt, so it must run BEFORE setDragDropMode or dragging dies.
        self.grid.setMovement(QListWidget.Movement.Static)
        self.grid.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        # setMovement(Static) turns viewport acceptDrops off; setDragDropMode
        # only re-enables it on the view, and AcceptDropsChange is skipped when
        # the view flag is already True — so the viewport stays drop-dead and
        # real drops never reach dropEvent. Re-enable it explicitly.
        self.grid.viewport().setAcceptDrops(True)
        self.grid.setDragDropOverwriteMode(False)
        self.grid.setIconSize(QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        self.grid.setGridSize(TILE_SIZE)
        self.grid.setWordWrap(True)
        self.grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._stack.addWidget(self.grid)

        if self._view_mode == "thumbnails":
            self._stack.setCurrentWidget(self.grid)

        layout.addWidget(self._stack, 1)

        # --- Row-editing buttons ---
        row_buttons: QHBoxLayout = QHBoxLayout()
        row_buttons.setSpacing(8)

        self.add_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="file.svg",
            hover_icon="file_filled.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_TEXT_PRIMARY,
            icon_size=14,
            text="Add images...",
        )
        self.add_btn.setProperty("BrowseButton", True)
        self.add_btn.setFixedHeight(32)
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.clicked.connect(self._add_images)
        row_buttons.addWidget(self.add_btn)

        self.remove_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="trash_outline.svg",
            hover_icon="trash.svg",
            pressed_icon="trash.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_TEXT_PRIMARY,
            pressed_color=THEME_TEXT_PRIMARY,
            icon_size=14,
            text="Remove",
        )
        self.remove_btn.setProperty("BrowseButton", True)
        self.remove_btn.setFixedHeight(32)
        self.remove_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.remove_btn.clicked.connect(self._remove_selected)
        row_buttons.addWidget(self.remove_btn)

        self.move_left_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="move_left.svg",
            hover_icon="move_left.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_TEXT_PRIMARY,
            icon_size=14,
        )
        self.move_left_btn.setProperty("BrowseButton", True)
        self.move_left_btn.setFixedSize(32, 32)
        self.move_left_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.move_left_btn.setToolTip("Move left (Alt+Left)")
        self.move_left_btn.clicked.connect(lambda: self._move_selected(-1))
        row_buttons.addWidget(self.move_left_btn)

        self.move_right_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="move_right.svg",
            hover_icon="move_right.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_TEXT_PRIMARY,
            icon_size=14,
        )
        self.move_right_btn.setProperty("BrowseButton", True)
        self.move_right_btn.setFixedSize(32, 32)
        self.move_right_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.move_right_btn.setToolTip("Move right (Alt+Right)")
        self.move_right_btn.clicked.connect(lambda: self._move_selected(1))
        row_buttons.addWidget(self.move_right_btn)

        self.sort_btn: QPushButton = QPushButton("Sort by name", self)
        self.sort_btn.setProperty("BrowseButton", True)
        self.sort_btn.setFixedHeight(32)
        self.sort_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.sort_btn.clicked.connect(self._sort_by_name)
        row_buttons.addWidget(self.sort_btn)

        row_buttons.addStretch()
        layout.addLayout(row_buttons)

        # Alt+Left/Alt+Right on the dialog (WindowShortcut): fires whichever
        # view has focus — the table also swallows Alt+arrows as cell
        # navigation, so both views additionally handle it in keyPressEvent.
        self._move_left_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        self._move_left_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self._move_left_shortcut.activated.connect(
            lambda: self._move_selected(-1)
        )
        self._move_right_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        self._move_right_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self._move_right_shortcut.activated.connect(
            lambda: self._move_selected(1)
        )

        # --- Dialog buttons (mirror JobDialog) ---
        button_layout: QHBoxLayout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        done_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="save_outline.svg",
            hover_icon="save_filled.svg",
            pressed_icon="save_check_filled.svg",
            normal_color=COLOR_GREEN,
            hover_color=COLOR_GREEN,
            pressed_color=COLOR_GREEN,
            icon_size=14,
            text="&Done",
        )
        done_btn.setFont(QFont(done_btn.font().family(), 10))
        done_btn.setProperty("SaveButton", True)
        done_btn.setFixedHeight(36)
        done_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        done_btn.setShortcut(QKeySequence("Ctrl+Return"))
        done_btn.clicked.connect(self.accept)
        button_layout.addWidget(done_btn)

        cancel_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="cancel_outline.svg",
            hover_icon="cancel_outline.svg",
            pressed_icon="cancel.svg",
            normal_color=THEME_TEXT_PRIMARY,
            hover_color=THEME_TEXT_PRIMARY,
            pressed_color=THEME_TEXT_PRIMARY,
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

    # ----- Rows -----

    def _add_row(self, path: Path) -> None:
        row: int = self.table.rowCount()
        self.table.insertRow(row)

        order_item = QTableWidgetItem()
        order_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.setItem(row, 0, order_item)

        name_item = QTableWidgetItem(path.name)
        name_item.setToolTip(str(path))
        name_item.setData(Qt.ItemDataRole.UserRole, str(path))
        self.table.setItem(row, 1, name_item)

        size_text: str = "—"
        dpi_text: str = "—"
        try:
            width_px, height_px, dpi_value, _rotate = _read_image_meta(path)
            size_text = f"{width_px} × {height_px}"
            dpi_text = f"{dpi_value:.0f}" if dpi_value else "—"
        except ValueError:
            size_text = "unreadable"
        size_item = QTableWidgetItem(size_text)
        size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, size_item)

        dpi_item = QTableWidgetItem(dpi_text)
        dpi_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, dpi_item)

    def _renumber(self) -> None:
        """Keep the # column in sync with the visual row order."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                item.setText(str(row + 1))

    def _thumbnail(self, path: str) -> QPixmap | None:
        if path in self._thumb_cache:
            return self._thumb_cache[path]
        pixmap: QPixmap | None = None
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image)
                image.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE))
                if image.mode != "RGBA":
                    image = image.convert("RGBA")
                data: bytes = image.tobytes()
                qimage = QImage(
                    data,
                    image.width,
                    image.height,
                    image.width * 4,
                    QImage.Format.Format_RGBA8888,
                )
                pixmap = QPixmap.fromImage(qimage)
        except Exception:
            pixmap = None
        self._thumb_cache[path] = pixmap
        return pixmap

    def _grid_item(self, path: str) -> QListWidgetItem:
        item = QListWidgetItem(Path(path).name)
        item.setData(Qt.ItemDataRole.UserRole, path)
        item.setSizeHint(TILE_SIZE)
        meta: str = ""
        try:
            width_px, height_px, dpi_value, _rotate = _read_image_meta(Path(path))
            meta = f"{width_px} × {height_px}"
            if dpi_value:
                meta += f" · {dpi_value:.0f} dpi"
        except ValueError:
            meta = "unreadable"
        item.setToolTip(f"{path}\n{meta}")
        pixmap = self._thumbnail(path)
        if pixmap is not None:
            item.setIcon(pixmap)
        return item

    def _apply_paths(self, paths: list[str]) -> None:
        """Make both views show exactly the given order."""
        self.table.setRowCount(0)
        for path in paths:
            self._add_row(Path(path))
        self._renumber()
        self.grid.clear()
        for path in paths:
            self.grid.addItem(self._grid_item(path))

    def _set_view(self, mode: str) -> None:
        if mode == self._view_mode:
            return
        paths: list[str] = self.image_paths
        self._view_mode = mode
        self._stack.setCurrentWidget(self.grid if mode == "thumbnails" else self.table)
        self._apply_paths(paths)

    # ----- Actions -----

    def _add_images(self) -> None:
        start: str = ""
        current = self.image_paths
        if current and Path(current[0]).parent.is_dir():
            start = str(Path(current[0]).parent)
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add images", start, IMAGE_FILTER
        )
        existing = {p.lower() for p in current}
        for path in natural_sort([Path(p) for p in paths]):
            if str(path).lower() not in existing:
                current.append(str(path))
                existing.add(str(path).lower())
        self._apply_paths(current)

    def _remove_selected(self) -> None:
        current: list[str] = self.image_paths
        if self._stack.currentWidget() is self.grid:
            drop = {
                str(item.data(Qt.ItemDataRole.UserRole))
                for item in self.grid.selectedItems()
            }
            remaining = [p for p in current if p not in drop]
        else:
            rows = {index.row() for index in self.table.selectedIndexes()}
            remaining = [p for r, p in enumerate(current) if r not in rows]
        self._apply_paths(remaining)

    def _sort_by_name(self) -> None:
        paths = natural_sort([Path(p) for p in self.image_paths])
        self._apply_paths([str(p) for p in paths])

    def _move_selected(self, delta: int) -> None:
        """Shift the selected rows one step left (-1) or right (+1)."""
        current: list[str] = self.image_paths
        count: int = len(current)
        if count < 2:
            return
        if self._stack.currentWidget() is self.grid:
            rows: list[int] = sorted(
                {self.grid.row(item) for item in self.grid.selectedItems()}
            )
        else:
            rows = sorted({index.row() for index in self.table.selectedIndexes()})
        if not rows:
            return
        selected: set[int] = set(rows)
        if delta < 0:
            for row in rows:  # ascending: each free step left
                if row == 0 or (row - 1) in selected:
                    continue
                current[row - 1], current[row] = current[row], current[row - 1]
                selected.discard(row)
                selected.add(row - 1)
        else:
            for row in reversed(rows):  # descending: each free step right
                if row == count - 1 or (row + 1) in selected:
                    continue
                current[row + 1], current[row] = current[row], current[row + 1]
                selected.discard(row)
                selected.add(row + 1)
        self._apply_paths(current)
        # Keep the moved rows selected so the user can keep tapping the button
        if self._stack.currentWidget() is self.grid:
            for row in sorted(selected):
                item = self.grid.item(row)
                if item is not None:
                    item.setSelected(True)
        else:
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

    # ----- Result -----

    @property
    def image_paths(self) -> list[str]:
        """Images in the current order of the active view."""
        if self._stack.currentWidget() is self.grid:
            paths: list[str] = []
            for row in range(self.grid.count()):
                item = self.grid.item(row)
                if item is None:
                    continue
                paths.append(str(item.data(Qt.ItemDataRole.UserRole)))
            return paths
        paths = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item is None:
                continue
            stored = item.data(Qt.ItemDataRole.UserRole)
            paths.append(str(stored if stored else item.toolTip()))
        return paths

    def accept(self) -> None:
        if not self.image_paths:
            self.reject()
            return
        super().accept()
