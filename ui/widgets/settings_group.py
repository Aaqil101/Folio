"""
Collapsible settings group widget for Folio.
Ported from Obsidian-Forge (Blender-Launcher-V2 design patterns).
"""

# ----- Built-In Modules -----
from typing import List

# ----- PySide6 Modules -----
from PySide6.QtCore import QEvent, QObject, QSize, Qt, Signal, Slot
from PySide6.QtGui import QCursor, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QWidget,
)

# ----- Utils Modules -----
from utils.color import AccentTheme
from utils.constants import FONT_SIZE_HEADER
from utils.resources import get_icon, get_resource_path


class SettingsGroup(QFrame):
    """
    Collapsible group widget for organizing settings.

    Signals:
        collapsed(bool): Emitted when the group is collapsed/expanded
        checked(bool): Emitted when the checkbox is toggled (if checkable)
        action_clicked(): Emitted when the action button is clicked (if action button is set)
    """

    collapsed = Signal(bool)
    checked = Signal(bool)
    action_clicked = Signal()

    def __init__(
        self, label: str, *, checkable: bool = False, parent: QWidget | None = None
    ) -> None:
        """
        Create a collapsible settings group.

        Args:
            label: The group title text
            checkable: If True, shows a checkbox instead of plain label
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setProperty("SettingsGroup", True)

        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Get the app's accent color theme
        self.accent: dict[str, str] = AccentTheme.get()

        # Header row: the whole band (chevron + heading + empty space) toggles
        self._header = QFrame(self)
        self._header.setProperty("SettingsHeader", True)
        self._header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._header_layout = QHBoxLayout(self._header)
        self._header_layout.setContentsMargins(4, 2, 4, 2)
        self._header_layout.setSpacing(6)
        self._header.installEventFilter(self)

        # Collapse/expand button - compact size
        self.collapse_button = QPushButton(self._header)
        self.collapse_button.setProperty("CollapseButton", True)
        self.collapse_button.setFixedSize(18, 18)
        self.collapse_button.setIcon(
            get_icon("expand_less.svg", color=self.accent["border"])
        )
        self.collapse_button.setIconSize(QSize(10, 10))
        self.collapse_button.clicked.connect(self.toggle)
        self._header_layout.addWidget(self.collapse_button)

        # Label or checkbox
        self._checkable: bool = checkable
        if checkable:
            self.checkbutton = QCheckBox(self._header)
            self.checkbutton.setText(label)
            self.checkbutton.clicked.connect(self.checked.emit)
            self._header_layout.addWidget(self.checkbutton)
            self.label = None
        else:
            self.checkbutton = None
            self.label = QLabel(f"{label}", self._header)
            self.label.setProperty("SectionHeader", True)
            # Let header clicks fall through to the header frame's handler
            self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            # Load and apply OpenSans-SemiBold font
            font_id: int = QFontDatabase.addApplicationFont(
                get_resource_path("assets/fonts/OpenSans-SemiBold.ttf")
            )
            if font_id != -1:
                font_families: List[str] = QFontDatabase.applicationFontFamilies(
                    font_id
                )
                if font_families:
                    font = QFont(font_families[0])
                    font.setPointSize(FONT_SIZE_HEADER)
                    self.label.setFont(font)

            self._header_layout.addWidget(self.label)

        self._header_layout.addStretch(1)
        self._layout.addWidget(self._header, 0, 0, 1, 3)

        # Action button (optional, initially hidden)
        self.action_button = None

        self._widget = None
        self._collapsed = False

    @Slot(QWidget)
    def setWidget(self, w: QWidget) -> None:
        """Set the content widget of this group."""
        if self._widget == w:
            return

        if self._widget is not None:
            self._layout.removeWidget(self._widget)

        self._widget = w
        self._layout.addWidget(self._widget, 1, 0, 1, 3)

    @Slot(QLayout)
    def setLayout(self, layout: QLayout) -> None:
        """Set the content layout of this group."""
        if self._widget is not None:
            self._layout.removeWidget(self._widget)

        self._widget = QWidget()
        self._widget.setLayout(layout)
        self._layout.addWidget(self._widget, 1, 0, 1, 3)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Toggle the group when the header band is clicked."""
        if obj is self._header:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if (
                    event.button() == Qt.MouseButton.LeftButton
                    and self._header.rect().contains(event.position().toPoint())
                ):
                    self.toggle()
                    return True
        return super().eventFilter(obj, event)

    @Slot(bool)
    def set_collapsed(self, collapsed: bool) -> None:
        """Set the collapsed state."""
        if collapsed and not self._collapsed:
            self.collapse()
        elif not collapsed and self._collapsed:
            self.uncollapse()

    @Slot()
    def toggle(self) -> None:
        """Toggle between collapsed and expanded states."""
        self.set_collapsed(not self._collapsed)

    @Slot()
    def collapse(self) -> None:
        """Collapse the group to hide its content."""
        if self._widget is None:
            return

        self._widget.hide()
        self.collapse_button.setIcon(
            get_icon("expand_more.svg", color=self.accent["border"])
        )
        self._collapsed = True
        self.collapsed.emit(True)

        if self.parent():
            self.parent().updateGeometry()

    @Slot()
    def uncollapse(self) -> None:
        """Expand the group to show its content."""
        if self._widget is None:
            return

        self._widget.show()
        self.collapse_button.setIcon(
            get_icon("expand_less.svg", color=self.accent["border"])
        )
        self._collapsed = False
        self.collapsed.emit(False)

        if self.parent():
            self.parent().updateGeometry()

    def isCollapsed(self) -> bool:
        """Return whether the group is currently collapsed."""
        return self._collapsed

    def setChecked(self, checked: bool) -> None:
        """Set the checkbox state (if checkable)."""
        if self._checkable and self.checkbutton:
            self.checkbutton.setChecked(checked)

    def isChecked(self) -> bool:
        """Return the checkbox state (if checkable)."""
        if self._checkable and self.checkbutton:
            return self.checkbutton.isChecked()
        return False

    @Slot(str, str)
    def setActionButton(self, icon_name: str, tooltip: str = "") -> None:
        """
        Add an action button to the header.

        Args:
            icon_name: Name of the icon file (e.g., "edit.svg")
            tooltip: Tooltip text for the button
        """
        # Remove existing action button if any
        if self.action_button:
            self._header_layout.removeWidget(self.action_button)
            self.action_button.deleteLater()

        # Create new action button
        self.action_button = QPushButton(self._header)
        self.action_button.setProperty("CollapseButton", True)
        self.action_button.setFixedSize(20, 20)
        self.action_button.setIcon(get_icon(icon_name, color=self.accent["border"]))
        self.action_button.setIconSize(QSize(14, 14))
        self.action_button.setToolTip(tooltip)
        self.action_button.clicked.connect(self.action_clicked.emit)

        # Add to the header, after the heading
        self._header_layout.addWidget(self.action_button)
