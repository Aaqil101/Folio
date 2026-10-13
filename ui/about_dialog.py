"""About dialog for Folio. Ported from Obsidian-Forge with Tokyo Night styling."""

# ----- PySide6 Modules -----
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

# ----- Utils Modules -----
from utils.color import (
    COLOR_CYAN,
    COLOR_LIGHT_BLUE,
    COLOR_PURPLE,
    COLOR_RED,
    THEME_TEXT_PRIMARY,
)
from utils.constants import (
    APP_NAME,
    APP_VERSION,
    AUTHOR,
    DESCRIPTION,
    WEBSITE_URL,
)
from utils.hover_button import HoverIconButtonSVG
from utils.resources import get_icon


class GlowingLine(QFrame):
    """A horizontal line with a glowing gradient effect."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(2)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor(COLOR_PURPLE))
        gradient.setColorAt(0.5, QColor(COLOR_LIGHT_BLUE))
        gradient.setColorAt(1.0, QColor(COLOR_CYAN))

        pen = QPen()
        pen.setBrush(gradient)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(0, 1, self.width(), 1)


class FeatureItem(QWidget):
    """A single feature item with icon and text."""

    def __init__(
        self, icon_name: str, text: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        layout.addStretch()

        icon_label: QLabel = QLabel()
        icon_label.setPixmap(get_icon(icon_name).pixmap(QSize(16, 16)))
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)

        text_label: QLabel = QLabel(text)
        text_label.setObjectName("FeatureText")
        layout.addWidget(text_label)

        layout.addStretch()


class AboutDialog(QDialog):
    """A stylish about dialog for Folio."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(350, 450)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setup_ui()
        self.center_on_parent()

    def setup_ui(self) -> None:
        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container: QFrame = QFrame()
        container.setObjectName("AboutContainer")

        shadow: QGraphicsDropShadowEffect = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        container.setGraphicsEffect(shadow)

        container_layout: QVBoxLayout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(8)

        header_widget: QWidget = QWidget()
        header_layout: QVBoxLayout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label: QLabel = QLabel()
        icon_label.setPixmap(
            get_icon("application/folio.svg", color=THEME_TEXT_PRIMARY).pixmap(
                QSize(72, 72)
            )
        )
        icon_label.setStyleSheet("background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)

        app_name_label: QLabel = QLabel(APP_NAME)
        app_name_label.setObjectName("AppName")
        app_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(app_name_label)

        version_widget: QWidget = QWidget()
        version_layout: QHBoxLayout = QHBoxLayout(version_widget)
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version_label: QLabel = QLabel(f"v{APP_VERSION}")
        version_label.setObjectName("Version")
        version_layout.addWidget(version_label)
        header_layout.addWidget(version_widget)

        container_layout.addWidget(header_widget)

        container_layout.addWidget(GlowingLine())

        desc_label: QLabel = QLabel(DESCRIPTION)
        desc_label.setObjectName("Description")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        container_layout.addWidget(desc_label)

        features_frame: QFrame = QFrame()
        features_frame.setObjectName("FeaturesFrame")

        features_layout: QVBoxLayout = QVBoxLayout(features_frame)
        features_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.setContentsMargins(4, 4, 4, 4)
        features_layout.setSpacing(2)

        features_title: QLabel = QLabel("Features")
        features_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_title.setObjectName("FeaturesTitle")
        features_layout.addWidget(features_title)

        features: list[tuple[str, str]] = [
            ("file.svg", "Two-up booklet imposition"),
            ("check_bold.svg", "Sheet-by-sheet verification"),
            ("folder_open.svg", "Drag and drop PDFs"),
        ]

        for icon, text in features:
            features_layout.addWidget(FeatureItem(icon, text))

        container_layout.addWidget(features_frame)

        author_widget: QWidget = QWidget()
        author_layout: QHBoxLayout = QHBoxLayout(author_widget)
        author_layout.setContentsMargins(0, 0, 0, 0)
        author_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_layout.setSpacing(6)

        created_label: QLabel = QLabel("Created with")
        created_label.setObjectName("Created")
        author_layout.addWidget(created_label)

        heart_label: QLabel = QLabel("\u2665")
        heart_label.setObjectName("Heart")
        author_layout.addWidget(heart_label)

        by_label: QLabel = QLabel(f"by {AUTHOR}")
        by_label.setObjectName("By")
        author_layout.addWidget(by_label)

        container_layout.addWidget(author_widget)

        website_label: QLabel = QLabel(
            f'<a href="{WEBSITE_URL}" style="color: {COLOR_LIGHT_BLUE};">{WEBSITE_URL}</a>'
        )
        website_label.setObjectName("Website")
        website_label.setOpenExternalLinks(True)
        website_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        website_label.setCursor(Qt.CursorShape.PointingHandCursor)
        container_layout.addWidget(website_label)

        container_layout.addStretch()

        close_btn: HoverIconButtonSVG = HoverIconButtonSVG(
            normal_icon="cancel_outline.svg",
            hover_icon="cancel_outline.svg",
            hover_color=f"{THEME_TEXT_PRIMARY}",
            pressed_icon="cancel.svg",
            pressed_color=f"{COLOR_RED}",
            icon_size=14,
            text="&Close",
        )
        close_btn.setObjectName("AboutCloseButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)

        btn_layout: QHBoxLayout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        container_layout.addLayout(btn_layout)

        main_layout.addWidget(container)

    def center_on_parent(self) -> None:
        if self.parent():
            parent_geometry = self.parent().geometry()
            dialog_geometry = self.geometry()

            x = (
                parent_geometry.x()
                + (parent_geometry.width() - dialog_geometry.width()) // 2
            )
            y = (
                parent_geometry.y()
                + (parent_geometry.height() - dialog_geometry.height()) // 2
            )

            self.move(x, y)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)
