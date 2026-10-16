# ----- Built-In Modules-----
# Style modules are imported explicitly, not discovered at runtime. The old
# pkgutil.iter_modules() scan over ui.styles.__path__ worked from source but
# silently produced an empty stylesheet in a frozen (PyInstaller) app: the
# path points inside the PYZ archive where there is no directory to list, and
# computed import names (importlib with an f-string) keep the modules out of
# the bundle entirely — the window fell back to bare Fusion styling. Plain
# import statements are the one form PyInstaller's static analysis always
# sees. When adding a style module, list it here too (alphabetical, folio
# last so its app-specific rules win ties).
from ui.styles import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableView,
    QTextEdit,
    QToolButton,
    QToolTip,
    QTreeView,
    QWidget,
    folio,
)

_STYLE_MODULES = (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableView,
    QTextEdit,
    QToolButton,
    QToolTip,
    QTreeView,
    QWidget,
    folio,
)


def build_stylesheet() -> str:
    """
    Combines every style module's QSS into one application stylesheet.

    Modules are listed explicitly (see the note above for why runtime
    discovery was removed); each must expose a qss() function.
    """
    styles = []
    for module in _STYLE_MODULES:
        if hasattr(module, "qss"):
            styles.append(module.qss())

    return "\n".join(styles)
