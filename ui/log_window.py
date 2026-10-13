"""Non-modal log window: streams imposition progress and run history."""

# ----- PySide6 Modules -----
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class LogWindow(QWidget):
    """Accumulates log lines and shows them in a toggleable side window.

    append_line() works while the window is hidden, so closing it (X or the
    header toggle) never loses history; the Clear button resets it.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Folio Log")
        self.setWindowFlags(Qt.WindowType.Window)
        self.setMinimumSize(560, 320)

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.text: QTextEdit = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.text, 1)

        button_row: QHBoxLayout = QHBoxLayout()
        button_row.addStretch()

        clear_button: QPushButton = QPushButton("Clear")
        clear_button.setProperty("BrowseButton", True)
        clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_button.clicked.connect(self.text.clear)
        button_row.addWidget(clear_button)

        layout.addLayout(button_row)

    def append_line(self, line: str) -> None:
        """Append one log line and scroll to the bottom."""
        self.text.moveCursor(QTextCursor.End)
        self.text.insertPlainText(f"{line}\n")
        scrollbar = self.text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self) -> None:
        """Reset the log (same as the Clear button)."""
        self.text.clear()
