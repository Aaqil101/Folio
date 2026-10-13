"""Folio - main entry point. A PySide6 application that turns PDFs into print-ready booklets."""

# ----- Built-In Modules -----
import sys

# ----- PySide6 Modules -----
from PySide6.QtWidgets import QApplication

# ----- UI Modules -----
from ui.main_window import MainWindow
from ui.styles.build_styles import build_stylesheet

# ----- Utils Modules -----
from utils.color import AccentTheme
from utils.config import config
from utils.resources import get_icon


def main() -> None:
    """Boot the application and show the main window."""
    app: QApplication = QApplication(sys.argv)
    app.setApplicationName("Folio")
    app.setStyle("Fusion")
    app.setWindowIcon(get_icon("application/folio.svg", color="#7aa2f7"))
    if config.accent != "random":
        AccentTheme.pin(config.accent)
    app.setStyleSheet(build_stylesheet())

    window: MainWindow = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
