"""Scheduler Qt application."""

import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api import constants as api_constants
from scheduler.api.edit import edit_log
from scheduler.api.tree.task_root import TaskRoot

from .constants import CANCEL_BUTTON, NO_BUTTON, TIMER_INTERVAL, YES_BUTTON
from .tabs.task_tab import TaskTab
from .tabs.timetable_tab import TimetableTab
from .tabs.suggestions_tab import SuggestionsTab
from .models.tree_manager import TreeManager
from .utils import custom_message_dialog
from .widgets.outliner import Outliner


class SchedulerWindow(QtWidgets.QMainWindow):
    """Scheduler window class."""

    def __init__(self, *args, **kwargs):
        """Initialise main window."""
        super(SchedulerWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Scheduler")
        self.resize(1600, 800)
        self.tree_root = TaskRoot.from_directory(
            api_constants.SCHEDULER_TASKS_DIRECTORY
        )
        edit_log.open_edit_registry()
        self.setup_tabs()
        self.setup_menu()
        self.startTimer(TIMER_INTERVAL)

    def setup_tabs(self):
        """Setup the tabs widget and different pages."""
        splitter = QtWidgets.QSplitter(self)
        self.setCentralWidget(splitter)
        splitter.setChildrenCollapsible(False)

        self.outliner_stack = QtWidgets.QStackedWidget(self)
        self.tabs_widget = QtWidgets.QTabWidget(self)
        splitter.addWidget(self.outliner_stack)
        splitter.addWidget(self.tabs_widget)

        self.create_tab_and_outliner("Tasks", TaskTab)
        self.create_tab_and_outliner("Timetable", TimetableTab)
        self.create_tab_and_outliner("Suggestions", SuggestionsTab)

        self.tabs_widget.currentChanged.connect(
            self.outliner_stack.setCurrentIndex
        )

    def create_tab_and_outliner(self, tab_name, tab_class):
        """Create tab and outliner combo for given tab_type.

        Args:
            tab_name (str): name to use for tab.
            tab_class (class): BaseTab subclass to use for class.
        """
        tab_tree_manager = TreeManager()
        outliner = Outliner(self.tree_root, tab_tree_manager)
        self.outliner_stack.addWidget(outliner)
        tab = tab_class(self.tree_root, tab_tree_manager, outliner)
        self.tabs_widget.addTab(tab, tab_name)

    def setup_menu(self):
        """Setup the menu actions."""
        menu_bar = self.menuBar()
        self.setMenuBar(menu_bar)
        
        file_menu = QtWidgets.QMenu("File", menu_bar)
        menu_bar.addMenu(file_menu)
        save_action = file_menu.addAction("Save")
        save_action.triggered.connect(self.save)
        
        edit_menu = QtWidgets.QMenu("Edit", menu_bar)
        menu_bar.addMenu(edit_menu)
        undo_action = edit_menu.addAction("Undo")
        undo_action.triggered.connect(self.undo)
        redo_action = edit_menu.addAction("Redo")
        redo_action.triggered.connect(self.redo)

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        modifiers = event.modifiers()

        if modifiers == QtCore.Qt.ControlModifier:
            if event.key() == QtCore.Qt.Key_S:
                self.save()
                edit_log.mark_edits_as_saved()
            elif event.key() == QtCore.Qt.Key_Z:
                self.undo()
            elif event.key() == QtCore.Qt.Key_Y:
                self.redo()
            # for debugging:
            elif event.key() == QtCore.Qt.Key_P:
                edit_log.print_edit_log(long=True)

        elif modifiers == (QtCore.Qt.ControlModifier|QtCore.Qt.ShiftModifier):
            if event.key() == QtCore.Qt.Key_Z:
                self.redo()

        super(SchedulerWindow, self).keyPressEvent(event)

    def save(self):
        """Save scheduler data."""
        self.tree_root.write()
        edit_log.mark_edits_as_saved()

    def undo(self):
        """Undo last action."""
        if edit_log.undo():
            self.update()

    def redo(self):
        """Redo last action."""
        if edit_log.redo():
            self.update()

    def update(self):
        """Update current tab and outliner."""
        self.tabs_widget.currentWidget().update()
        self.outliner_stack.currentWidget().update()

    def timerEvent(self, event):
        """Called every timer_interval. Used to make autosaves.

        Args:
            event (QtCore.QEvent): the timer event.
        """
        self.tree_root.write(api_constants.SCHEDULER_TASKS_AUTOSAVES_DIRECTORY)

    def closeEvent(self, event):
        """Called on closing: prompt user to save changes if not done yet.

        Args:
            event (QtCore.QEvent): the close event.
        """
        self.tree_root.write(api_constants.SCHEDULER_TASKS_AUTOSAVES_DIRECTORY)
        if edit_log.unsaved_edits():
            result = custom_message_dialog(
                "Unsaved Changes",
                buttons=[YES_BUTTON, NO_BUTTON, CANCEL_BUTTON],
                informative_text=(
                    "There are unsaved changes. Save before closing?"
                )
            )
            if result == CANCEL_BUTTON:
                event.ignore()
                return
            if result == YES_BUTTON:
                self.save()
            event.accept()
        super(SchedulerWindow, self).closeEvent(event)


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
    window.showMaximized()
    app.exec_()
