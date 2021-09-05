"""Scheduler Qt application."""

import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.task import Task
from .task_model import TaskModel
from .task_view import TaskView
from .timetable_view import TimetableView


class SchedulerWindow(QtWidgets.QMainWindow):
    """Scheduler window class."""

    def __init__(self, *args, **kwargs):
        """Initialise main window."""
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Scheduler")
        self.resize(1600, 800)
        self.setup_tabs()
        self.setup_menu()

    def setup_tabs(self):
        """Setup the tabs widget and different pages."""
        self.tabs_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs_widget)
        self.tasks_tab = TaskView(self)
        self.tabs_widget.addTab(self.tasks_tab, "Tasks")
        self.timetable_tab = TimetableView(self)
        self.tabs_widget.addTab(self.timetable_tab, "Timetable")

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
        self.tasks_tab.outliner.tasks_data.write()


def run_application():
    """Open application window."""
    app = QtWidgets.QApplication(sys.argv)
    window = SchedulerWindow()
    window.show()
    app.exec_()
