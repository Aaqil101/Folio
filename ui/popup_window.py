"""
Popup window component for Folio. Styled with Tokyo Night theme,
adapted from Obsidian-Forge's Blender-Launcher-V2 popup design.
"""

# ----- Built-In Modules -----
import textwrap
from enum import Enum

# ----- PySide6 Modules -----
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# ----- Utils Modules -----
from utils.color import (
    COLOR_GREEN,
    COLOR_LIGHT_BLUE,
    COLOR_RED,
    COLOR_YELLOW,
    THEME_TEXT_PRIMARY,
)
from utils.constants import FONT_FAMILY
from utils.resources import get_icon


class PopupIcon(Enum):
    """Icon types for popup windows."""

    WARNING = "popup/exclamation.svg"
    INFO = "popup/info.svg"
    ERROR = "popup/error.svg"
    SUCCESS = "popup/check.svg"
    NONE = None

    @property
    def default_color(self) -> str:
        """Get the default Tokyo Night color for this icon type."""
        color_map: dict[PopupIcon, str] = {
            PopupIcon.WARNING: COLOR_YELLOW,
            PopupIcon.INFO: COLOR_LIGHT_BLUE,
            PopupIcon.ERROR: COLOR_RED,
            PopupIcon.SUCCESS: COLOR_GREEN,
            PopupIcon.NONE: THEME_TEXT_PRIMARY,
        }
        return color_map.get(self, THEME_TEXT_PRIMARY)


class PopupWindow(QDialog):
    """
    Custom popup dialog with Tokyo Night theme styling.

    Signals:
        accepted: Emitted when OK/accept button is clicked
        cancelled: Emitted when Cancel button is clicked
        custom_signal: Emitted with button label when custom button is clicked
    """

    accepted = Signal()
    cancelled = Signal()
    custom_signal = Signal(str)

    def __init__(
        self,
        message: str,
        title: str = "Info",
        info_popup: bool = False,
        icon: PopupIcon = PopupIcon.INFO,
        icon_color: str | None = None,
        buttons: list[str] | None = None,
        parent: QWidget | None = None,
        auto_close_ms: int | None = None,
    ) -> None:
        """
        Create a popup dialog.

        Args:
            message: The message to display in the popup
            title: The title of the popup window (default: "Info")
            info_popup: If True, only shows OK button (default: False)
            icon: Icon to display (use PopupIcon enum)
            icon_color: Change the icon color (uses icon's default color if None)
            buttons: Optional list of button labels. If not provided:
                - info_popup=True: Shows only OK
                - info_popup=False: Shows OK and Cancel
            parent: Parent widget (optional)
            auto_close_ms: If provided, automatically close after this many milliseconds
        """
        super().__init__(parent)

        self.title: str = title
        self.message: str = message
        self.info_popup: bool = info_popup
        self.icon_color: str = (
            icon_color if icon_color is not None else icon.default_color
        )
        self.buttons: list[str] | None = buttons
        self.auto_close_ms: int | None = auto_close_ms
        self.remaining_ms: int | None = auto_close_ms
        self.countdown_label: QLabel | None = None
        self.countdown_timer: QTimer | None = None
        self.close_timer: QTimer | None = None

        # Configure dialog
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle(self.title)
        self.setMinimumSize(300, 100)

        # Remove minimize and maximize buttons
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowMinimizeButtonHint
            & ~Qt.WindowType.WindowMaximizeButtonHint
        )

        self._setup_ui(icon)
        self.adjustSize()
        self.setFixedSize(self.size())

        # Setup auto-close timer if specified
        if auto_close_ms is not None:
            self._setup_auto_close(auto_close_ms)

    def _setup_ui(self, icon: PopupIcon) -> None:
        """Setup the popup UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(6)

        # Icon and message layout
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(2, 2, 2, 0)
        content_layout.setSpacing(8)

        # Icon
        if icon != PopupIcon.NONE:
            icon_label = QLabel()
            icon_label.setScaledContents(True)
            icon_label.setFixedSize(20, 20)
            icon_label.setPixmap(
                get_icon(icon.value, color=self.icon_color).pixmap(20, 20)
            )
            content_layout.addWidget(icon_label)

        # Wrap message text manually (similar to Blender-Launcher approach)
        wrapped_lines = []
        for line in self.message.splitlines():
            if not line.strip():
                wrapped_lines.append("")
            else:
                wrapped: list[str] = textwrap.wrap(line, width=50)
                wrapped_lines.extend(wrapped)
        wrapped_message = "\n".join(wrapped_lines)

        message_label = QLabel(wrapped_message)
        message_label.setWordWrap(True)
        content_layout.addWidget(message_label)

        main_layout.addLayout(content_layout)
        main_layout.addSpacing(4)

        # Add countdown label if auto-close is enabled
        if self.auto_close_ms is not None:
            self.countdown_label = QLabel()
            self.countdown_label.setFont(QFont(FONT_FAMILY, 9))
            self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.countdown_label.setProperty("InfoBox", True)
            main_layout.addWidget(self.countdown_label)
            main_layout.addSpacing(2)

        # Add buttons
        self._add_buttons(main_layout)

    def _add_buttons(self, layout: QVBoxLayout) -> None:
        """Add appropriate buttons based on configuration."""
        if self.buttons:
            self._add_custom_buttons(layout)
        elif self.info_popup:
            self._add_info_button(layout)
        else:
            self._add_default_buttons(layout)

    def _add_custom_buttons(self, layout: QVBoxLayout) -> None:
        """Add custom buttons based on provided list."""
        if self.buttons is None:
            return

        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)

        if len(self.buttons) > 2:
            # Multiple custom buttons - emit custom_signal
            for label in self.buttons:
                button = self._create_button(label, self._custom_signal)
                button_layout.addWidget(button)
        elif len(self.buttons) == 2:
            # Two buttons: OK and Cancel
            ok_button = self._create_button(self.buttons[0], self._accept)
            cancel_button = self._create_button(self.buttons[1], self._cancel)
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
        else:
            # Single button: OK
            ok_button = self._create_button(self.buttons[0], self._accept)
            button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

    def _add_info_button(self, layout: QVBoxLayout) -> None:
        """Add single OK button for info popup."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)
        button_layout.addStretch()

        ok_button = self._create_button("&OK", self._accept)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

    def _add_default_buttons(self, layout: QVBoxLayout) -> None:
        """Add default OK and Cancel buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)
        button_layout.addStretch()

        ok_button = self._create_button("&OK", self._accept)
        cancel_button = self._create_button("&Cancel", self._cancel)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def _create_button(
        self,
        label: str,
        callback,
    ) -> QPushButton:
        """Create a button with appropriate styling."""
        button = QPushButton(label)
        button.setFont(QFont(FONT_FAMILY, 10))
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setProperty("BrowseButton", True)

        # Connect callback
        if callback == self._custom_signal:
            button.clicked.connect(lambda: callback(label))
        else:
            button.clicked.connect(callback)

        return button

    def _custom_signal(self, label: str) -> None:
        """Emit custom signal and close."""
        self.custom_signal.emit(label)
        self.accept()

    def _accept(self) -> None:
        """Emit accepted signal and close."""
        self.accepted.emit()
        self.accept()

    def _cancel(self) -> None:
        """Emit cancelled signal and close."""
        self.cancelled.emit()
        self.reject()

    def _setup_auto_close(self, auto_close_ms: int) -> None:
        """Setup auto-close timers and countdown display."""
        # Timer to close the popup
        self.close_timer = QTimer()
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.accept)
        self.close_timer.start(auto_close_ms)

        # Timer to update countdown display (updates every 100ms for smooth countdown)
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_timer.start(100)

        # Initial countdown update
        self._update_countdown()

    def _update_countdown(self) -> None:
        """Update the countdown label."""
        if self.countdown_label is None or self.close_timer is None:
            return

        # Get remaining time from the close timer
        remaining: int = self.close_timer.remainingTime()

        if remaining <= 0:
            # Stop the countdown timer when time is up
            if self.countdown_timer:
                self.countdown_timer.stop()
            return

        # Format the countdown display
        seconds: float = remaining / 1000.0
        if seconds >= 1:
            self.countdown_label.setText(f"Closing in {seconds:.1f}s...")
        else:
            self.countdown_label.setText(f"Closing in {remaining}ms...")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard events."""
        if event.key() == Qt.Key.Key_Escape and not self.info_popup:
            self._cancel()
        elif event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
            self._accept()
        else:
            super().keyPressEvent(event)
