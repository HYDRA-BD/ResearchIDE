"""Consistent Academic Design System and Theme Stylesheets for PySide6."""

DARK_THEME_QSS = """
QMainWindow, QWidget#CentralWidget {
    background-color: #1e1e24;
    color: #e0e0e6;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QMenuBar {
    background-color: #18181c;
    color: #dcdce0;
    border-bottom: 1px solid #2d2d34;
    padding: 2px 8px;
}

QMenuBar::item:selected {
    background-color: #2a2a32;
    border-radius: 4px;
}

QMenu {
    background-color: #222228;
    color: #e0e0e6;
    border: 1px solid #363640;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #2d5da1;
    color: #ffffff;
}

/* Ribbon Container */
QFrame#RibbonContainer {
    background-color: #18181c;
    border-bottom: 1px solid #2d2d34;
}

QTabWidget#RibbonTabs::pane {
    border: none;
    background-color: #1e1e24;
    padding: 4px;
}

QTabBar::tab {
    background-color: #18181c;
    color: #a0a0aa;
    padding: 8px 16px;
    font-weight: 500;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1e1e24;
    color: #4daafc;
    border-bottom: 2px solid #4daafc;
}

QTabBar::tab:hover:!selected {
    color: #e0e0e6;
    background-color: #24242c;
}

/* Ribbon Buttons */
QPushButton.RibbonBtn {
    background-color: transparent;
    color: #dcdce0;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 12px;
    text-align: center;
    font-size: 12px;
}

QPushButton.RibbonBtn:hover {
    background-color: #2a2a34;
    border-color: #3e3e4a;
}

QPushButton.RibbonBtn:pressed {
    background-color: #343442;
}

/* Primary Action Buttons */
QPushButton.PrimaryBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton.PrimaryBtn:hover {
    background-color: #1d4ed8;
}

QPushButton.PrimaryBtn:pressed {
    background-color: #1e40af;
}

/* Sidebar & Trees */
QTreeView, QListView, QListWidget {
    background-color: #18181c;
    color: #dcdce0;
    border: 1px solid #2d2d34;
    border-radius: 4px;
    outline: none;
}

QTreeView::item:hover, QListWidget::item:hover {
    background-color: #262630;
}

QTreeView::item:selected, QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

/* Status Bar */
QStatusBar {
    background-color: #141418;
    color: #8e8e98;
    border-top: 1px solid #25252c;
    font-size: 11px;
}

/* Dock Widgets */
QDockWidget {
    titlebar-close-icon: url(close.png);
    titlebar-normal-icon: url(undock.png);
    color: #dcdce0;
    font-weight: 600;
}

QDockWidget::title {
    background-color: #1c1c22;
    padding: 6px;
    border-bottom: 1px solid #2a2a32;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #18181c;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #3e3e48;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #545462;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

LIGHT_THEME_QSS = """
QMainWindow, QWidget#CentralWidget {
    background-color: #f8fafc;
    color: #1e293b;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QMenuBar {
    background-color: #ffffff;
    color: #334155;
    border-bottom: 1px solid #e2e8f0;
    padding: 2px 8px;
}

QMenuBar::item:selected {
    background-color: #f1f5f9;
    border-radius: 4px;
}

QMenu {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QFrame#RibbonContainer {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}

QTabBar::tab {
    background-color: #ffffff;
    color: #64748b;
    padding: 8px 16px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #f8fafc;
    color: #2563eb;
    border-bottom: 2px solid #2563eb;
}

QPushButton.RibbonBtn {
    background-color: transparent;
    color: #334155;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 12px;
}

QPushButton.RibbonBtn:hover {
    background-color: #f1f5f9;
    border-color: #cbd5e1;
}

QPushButton.PrimaryBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: 600;
}

QStatusBar {
    background-color: #ffffff;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
}
"""

def get_theme_stylesheet(theme_name: str = "dark") -> str:
    """Return theme stylesheet string for PySide6 application."""
    if theme_name.lower() == "light":
        return LIGHT_THEME_QSS
    return DARK_THEME_QSS

