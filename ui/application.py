"""Scheduler Qt application."""

import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.task_data import TaskData

from .tabs.task_tab import TaskTab
from .tabs.timetable_tab import TimetableTab
from .tabs.suggestions_tab import SuggestionsTab


class SchedulerWindow(QtWidgets.QMainWindow):
    """Scheduler window class."""

    def __init__(self, *args, **kwargs):
        """Initialise main window."""
        super(SchedulerWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Scheduler")
        self.resize(1600, 800)
        path = "C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\tasks\\projects.json"
        self.task_data = TaskData.from_file(path)
        self.tree_root = self.task_data.get_tree_root()
        self.setup_tabs()
        self.setup_menu()

    def setup_tabs(self):
        """Setup the tabs widget and different pages."""
        self.tabs_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs_widget)
        self.tasks_tab = TaskTab(self.tree_root, self)
        self.tabs_widget.addTab(self.tasks_tab, "Tasks")
        self.timetable_tab = TimetableTab(self.tree_root, self)
        self.tabs_widget.addTab(self.timetable_tab, "Timetable")
        self.suggestions_tab = SuggestionsTab(self.tree_root, self)
        self.tabs_widget.addTab(self.suggestions_tab, "Suggestions")

    def setup_menu(self):
        """Setup the menu actions."""
        menu_bar = self.menuBar()
        self.setMenuBar(menu_bar)
        file_menu = QtWidgets.QMenu("File", menu_bar)
        menu_bar.addMenu(file_menu)
        save_action = file_menu.addAction("Save")
        save_action.triggered.connect(self.save)

    def save(self):
        """Save scheduler data."""
        self.tasks_tab.outliner.task_data.write()


def set_style(app):
    """Set style from style/stylesheet.qss on app.

    Args:
        app (QtWidgets.QApplication): Qt Application.
    """
    stylesheet_path = os.path.join(
        os.path.dirname(__file__), "style", "stylesheet.qss"
    )
    with open(stylesheet_path, "r") as stylesheet_file:
        stylesheet = stylesheet_file.read()
    app.setStyleSheet(stylesheet)


def run_application():
    """Open application window."""
    app = QtWidgets.QApplication(sys.argv)
    set_style(app)
    window = SchedulerWindow()
    window.show()
    app.exec_()
