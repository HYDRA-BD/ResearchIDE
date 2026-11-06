"""PySide6 Presentation Layer for ResearchIDE."""
from src.ui.main_window import MainWindow
from src.ui.theme import get_theme_stylesheet
from src.ui.ribbon import RibbonBar
from src.ui.dashboard import HomeDashboard
from src.ui.explorer import ProjectExplorer
from src.ui.workspace import DocumentWorkspace

__all__ = [
    "MainWindow",
    "get_theme_stylesheet",
    "RibbonBar",
    "HomeDashboard",
    "ProjectExplorer",
    "DocumentWorkspace",
]

