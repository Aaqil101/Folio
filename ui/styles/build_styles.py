# ----- Built-In Modules-----
import importlib
import pkgutil

# ----- UI Modules-----
import ui.styles


def build_stylesheet() -> str:
    """
    Dynamically imports all style modules and combines their QSS stylesheets.
    Automatically discovers new style files as the project grows.
    """
    styles = []
    styles_package = ui.styles
    styles_path: str = styles_package.__path__[0]

    # Iterate through all modules in the styles package
    for _, module_name, _ in pkgutil.iter_modules([styles_path]):
        # Skip this build_styles module itself
        if module_name == "build_styles":
            continue

        # Dynamically import the module
        module = importlib.import_module(f"ui.styles.{module_name}")

        # If the module has a qss() function, call it and add to styles
        if hasattr(module, "qss"):
            styles.append(module.qss())

    return "\n".join(styles)