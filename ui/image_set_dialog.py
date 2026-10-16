"""Image-set dialog: review and reorder the images of one queue job (issue #7).

Opened whenever images enter the queue (Add picker or drag & drop) and
again when editing an image job. The caller supplies the order as-is —
natural filename order on first ingest, the job's current order when
reopened — so a previous manual reorder is never discarded. The user
drags rows in the list view, or nudges the selection with Alt+Up/Down
(list) / Alt+Left/Right (thumbnails) or the move buttons (the selection
wraps to the opposite end when no step is free; plain arrow keys only
walk the highlight and also wrap at the ends), adds/removes images, or
re-sorts by name. Thumbnail view is reorder by buttons/shortcuts only
(drag is disabled there). The returned order is the page order of the
booklet. The opening layout follows config.image_view_mode ("list" or
"thumbnails"); toggling inside the dialog does not persist.
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
from ui.reorder import drop_event_moved

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
            and event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down)
        ):
            # Rows are vertical: Alt+Up/Down reorders (matching axis).
            self._dialog._move_selected(
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
            # loops 1 <-> 12); column navigation is useless in this dialog
            # and made the arrows feel dead at the edges.
            count = self.rowCount()
            if count:
                row = self.currentIndex().row()
                if row < 0:
                    row = 0 if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Right) else count - 1
                elif event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Right):
                    row = (row + 1) % count
                else:
                    row = (row - 1 + count) % count
                col = self.currentColumn()
                self.setCurrentIndex(self.model().index(row, col if col >= 0 else 0))
                self.selectRow(row)
                event.accept()
                return
        super().keyPressEvent(event)


class _ImageGrid(QListWidget):
    """Icon-mode grid of tiles; reorder via buttons/shortcuts only."""

    def __init__(self, dialog: "ImageSetDialog", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dialog = dialog

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
        if event.modifiers() == Qt.KeyboardModifier.NoModifier and event.key() in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
        ):
            # Plain arrows jump between tiles and wrap at the ends.
            count = self.count()
            if count:
                row = self.currentRow()
                if row < 0:
                    row = 0 if event.key() == Qt.Key.Key_Right else count - 1
                elif event.key() == Qt.Key.Key_Right:
                    row = (row + 1) % count
                else:
                    row = (row - 1 + count) % count
                item = self.item(row)
                if item is not None:
                    self.setCurrentRow(row)
                    self.clearSelection()
                    item.setSelected(True)
                    event.accept()
                    return
        super().keyPressEvent(event)


class ImageSetDialog(QDialog):
    """Order a set of images; accepted order becomes the booklet's pages."""

    def __init__(self, paths: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Arrange images")
        self.setMinimumSize(970, 640)

        self._view_mode: str = config.image_view_mode
        self._thumb_cache: dict[str, QPixmap | None] = {}

        self._build_ui()
        # Keep the caller's order: _prompt_image_job() hands over a
        # natural-sorted list for a fresh set, while _reorder_job_images()
        # and JobDialog pass the job's current order — re-sorting here
        # would throw a manual reorder away on every reopen.
        self._apply_paths([str(p) for p in paths])

    # ----- UI -----

    def _build_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        hint: QWidget = QWidget()
        hint_layout: QHBoxLayout = QHBoxLayout(hint)
        hint_layout.setContentsMargins(0, 0, 0, 0)
        self.hint_label: QLabel = QLabel()
        hint_layout.addWidget(self.hint_label)
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
        self._update_hint()

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
        # Drag reorder is deliberately OFF in the thumbnail view (user
        # decision after the real-window eyeball pass: Qt's IconMode drop
        # handling misbehaved in practice). Reordering there is via the
        # move buttons / Alt+Left / Alt+Right; the list view keeps
        # pointer-drag reorder. Static locks every tile in its cell so a
        # stray press-drag never leaves a tile floating mid-grid.
        self.grid.setMovement(QListWidget.Movement.Static)
        self.grid.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
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
        self._update_move_tooltips()

        self.sort_btn: QPushButton = QPushButton("Sort by name", self)
        self.sort_btn.setProperty("BrowseButton", True)
        self.sort_btn.setFixedHeight(32)
        self.sort_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.sort_btn.clicked.connect(self._sort_by_name)
        row_buttons.addWidget(self.sort_btn)

        row_buttons.addStretch()
        layout.addLayout(row_buttons)

        # Alt+arrow reorders along each view's flow: Alt+Up/Down in the
        # list (rows are vertical), Alt+Left/Right in thumbnails (tiles run
        # horizontally). All four are registered dialog-wide (WindowShortcut)
        # so a press still lands when focus sits on a button; the handler
        # ignores the keys on the wrong axis for the active view.
        self._move_shortcuts: list[QShortcut] = []
        for sequence, key in (
            ("Alt+Up", Qt.Key.Key_Up),
            ("Alt+Down", Qt.Key.Key_Down),
            ("Alt+Left", Qt.Key.Key_Left),
            ("Alt+Right", Qt.Key.Key_Right),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(lambda k=key: self._move_for_key(k))
            self._move_shortcuts.append(shortcut)

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

    def _update_hint(self) -> None:
        """The hint matches what the active view actually supports."""
        if self._view_mode == "thumbnails":
            self.hint_label.setText(
                "Use Alt+Left / Alt+Right or the arrow buttons to set the "
                "page order. Arrow keys jump between images and wrap around "
                "at the ends. The first item becomes page 1."
            )
        else:
            self.hint_label.setText(
                "Drag rows or press Alt+Up / Alt+Down to set the page order. "
                "Arrow keys move the highlight and wrap around at the ends. "
                "The first item becomes page 1."
            )

    def _update_move_tooltips(self) -> None:
        """The move buttons name the shortcut of the active view's axis."""
        if self._view_mode == "thumbnails":
            self.move_left_btn.setToolTip("Move left (Alt+Left)")
            self.move_right_btn.setToolTip("Move right (Alt+Right)")
        else:
            self.move_left_btn.setToolTip("Move up (Alt+Up)")
            self.move_right_btn.setToolTip("Move down (Alt+Down)")

    def _set_view(self, mode: str) -> None:
        if mode == self._view_mode:
            return
        paths: list[str] = self.image_paths
        self._view_mode = mode
        self._stack.setCurrentWidget(self.grid if mode == "thumbnails" else self.table)
        self._apply_paths(paths)
        self._update_hint()
        self._update_move_tooltips()

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

    def _move_for_key(self, key: int) -> None:
        """Alt+arrow move, axis-matched to the active view.

        List rows are vertical (Alt+Up/Down); thumbnail tiles run
        horizontally (Alt+Left/Right). The wrong axis is ignored.
        """
        if self._view_mode == "thumbnails":
            if key == Qt.Key.Key_Left:
                self._move_selected(-1)
            elif key == Qt.Key.Key_Right:
                self._move_selected(1)
        elif key == Qt.Key.Key_Up:
            self._move_selected(-1)
        elif key == Qt.Key.Key_Down:
            self._move_selected(1)

    def _move_selected(self, delta: int) -> None:
        """Shift the selected rows one step left (-1) or right (+1).

        When no row of the selection can step freely (every row is at the
        edge or blocked by its own selection neighbour), the whole block
        wraps to the opposite end, keeping its internal order — the list
        behaves like a ring.
        """
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
        # Remember which image the cursor sits on: the rebuild below wipes
        # the views' current item, and without this the next plain arrow
        # starts from -1 and jumps to the first/last tile. Prefer the row
        # the user is working with (current, if it's part of the move) over
        # a stale current left behind by earlier navigation.
        if self._stack.currentWidget() is self.grid:
            anchor_row = self.grid.currentRow()
        else:
            anchor_row = self.table.currentIndex().row()
        if anchor_row not in selected:
            anchor_row = min(selected)
        anchor_path = current[anchor_row]
        if delta < 0:
            if all(r == 0 or (r - 1) in selected for r in rows):
                # No free step left: send the block to the end.
                block = [current[r] for r in rows]
                remaining = [p for i, p in enumerate(current) if i not in selected]
                current = remaining + block
                selected = set(range(len(remaining), count))
            else:
                for row in rows:  # ascending: each free step left
                    if row == 0 or (row - 1) in selected:
                        continue
                    current[row - 1], current[row] = current[row], current[row - 1]
                    selected.discard(row)
                    selected.add(row - 1)
        else:
            if all(r == count - 1 or (r + 1) in selected for r in rows):
                # No free step right: send the block to the front.
                block = [current[r] for r in rows]
                remaining = [p for i, p in enumerate(current) if i not in selected]
                current = block + remaining
                selected = set(range(len(block)))
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
        # Put the cursor back on the same image so the next arrow key
        # steps from there instead of leaping to an end.
        new_row = current.index(anchor_path) if anchor_path is not None else -1
        if new_row < 0 and selected:
            new_row = max(selected)
        if new_row >= 0:
            if self._stack.currentWidget() is self.grid:
                # NoUpdate: don't clobber the restored multi-selection.
                self.grid.setCurrentRow(
                    new_row, QItemSelectionModel.SelectionFlag.NoUpdate
                )
            else:
                # NoUpdate via the selection model: QTableWidget's own
                # setCurrentIndex replaces the selection with the new row.
                col = self.table.currentColumn()
                self.table.selectionModel().setCurrentIndex(
                    self.table.model().index(new_row, col if col >= 0 else 0),
                    QItemSelectionModel.SelectionFlag.NoUpdate,
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
