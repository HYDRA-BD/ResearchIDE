"""Desktop Application Entrypoint for ResearchIDE."""
import sys
from pathlib import Path

# Ensure project root is present in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logger import app_logger


def main() -> int:
    """Launch ResearchIDE PySide6 desktop application."""
    # High-DPI scaling configuration
    QCoreApplication.setApplicationName("ResearchIDE")
    QCoreApplication.setOrganizationName("ResearchIDE")

    app = QApplication(sys.argv)

    app_logger.info("Starting ResearchIDE Desktop Suite...")
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
