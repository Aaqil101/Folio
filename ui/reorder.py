"""Shared row-reorder helpers for Folio's InternalMove tables (issue #7).

Qt's built-in QTableWidget drag-and-drop cannot reorder reliably: drops on
the empty area below the last row are not targeted, center-of-row drops take
the take/set path that blanks the source row, and a manual move must suppress
the clearOrRemove() that QAbstractItemView::startDrag() runs afterwards (the
dropEventMoved flag lives inside Qt's dropEvent, which a subclass override
bypasses). Both problems are solved here: the drop handler moves rows itself,
clears the selection so the later clearOrRemove() no-ops, and accepts the
event with the proposed (move) action.
"""

# ----- PySide6 Modules -----
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
)


def target_row_for_drop(
    view: QTableWidget, y: float, indicator: QAbstractItemView.DropIndicatorPosition
) -> int:
    """Row index where a drop at viewport y should insert the dragged rows."""
    count: int = view.rowCount()
    row: int = view.rowAt(int(y))
    if row < 0:
        for r in range(count):
            if y < view.visualRect(view.model().index(r, 0)).top():
                return r
        return count
    if indicator == QAbstractItemView.DropIndicatorPosition.BelowItem:
        return row + 1
    return row


def move_rows(view: QTableWidget, rows: list[int], target: int) -> None:
    """Move the given rows so the block starts at target (cell data intact)."""
    selected: list[int] = sorted(set(rows))
    target -= sum(1 for r in selected if r < target)
    taken: list[list] = []
    for r in reversed(selected):
        cells: list = [
            view.takeItem(r, col) for col in range(view.columnCount())
        ]
        view.removeRow(r)
        taken.append(cells)
    taken.reverse()
    for offset, items in enumerate(taken):
        view.insertRow(target + offset)
        for col, item in enumerate(items):
            if item is not None:
                view.setItem(target + offset, col, item)


def drop_event_moved(view: QTableWidget, event: QDropEvent) -> bool:
    """Handle an internal row drag-drop in place; False = caller falls back
    to the default dropEvent (external source)."""
    if event.source() != view:
        return False
    rows: list[int] = sorted({index.row() for index in view.selectedIndexes()})
    if not rows:
        event.ignore()
        return True
    # dropIndicatorPosition() is a QAbstractItemView method, not a QDropEvent one
    target: int = target_row_for_drop(
        view, event.position().y(), view.dropIndicatorPosition()
    )
    move_rows(view, rows, target)
    view.clearSelection()
    event.acceptProposedAction()
    return True


def drop_event_moved_grid(view: QListWidget, event: QDropEvent) -> bool:
    """Handle an internal tile drag-drop in an IconMode QListWidget.

    Same contract as drop_event_moved: moves the selection ourselves and
    returns False for an external source. In IconMode there is no useful
    above/below indicator, so the block is inserted at the item under the
    cursor (dropped on empty space = append). Static movement keeps the
    tiles in their cells; this handler is what actually reorders them.
    """
    if event.source() != view:
        return False
    items: list[QListWidgetItem] = view.selectedItems()
    if not items:
        event.ignore()
        return True
    rows: list[int] = sorted({view.row(item) for item in items})
    index = view.indexAt(event.position().toPoint())
    target: int = index.row() if index.isValid() else view.count()
    target -= sum(1 for r in rows if r < target)
    taken: list[QListWidgetItem] = []
    for r in reversed(rows):
        taken.append(view.takeItem(r))
    taken.reverse()
    for offset, item in enumerate(taken):
        view.insertItem(target + offset, item)
    view.clearSelection()
    event.acceptProposedAction()
    return True
