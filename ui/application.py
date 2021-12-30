"""Scheduler Qt application."""

import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api import constants as api_constants
from scheduler.api.common.date_time import Date
from scheduler.api.timetable.calendar import Calendar
from scheduler.api.timetable.calendar_period import CalendarDay
from scheduler.api.edit import edit_log
from scheduler.api.tree.task_root import TaskRoot

from .constants import CANCEL_BUTTON, NO_BUTTON, TIMER_INTERVAL, YES_BUTTON

from .tabs.notes_tab import NotesTab
from .tabs.task_tab import TaskTab
from .tabs.timetable_tab import TimetableTab
from .tabs.tracker_tab import TrackerTab
from .tabs.suggestions_tab import SuggestionsTab

from .models.tree_manager import TreeManager
from .utils import custom_message_dialog, set_style
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

        self.calendar = Calendar.from_directory(
            api_constants.SCHEDULER_CALENDAR_DIRECTORY,
            self.tree_root
        )
        # self.calendar._add_day(
        #     CalendarDay(self.calendar, Date(2022, 1, 1))
        # )
        print (self.calendar.to_dict())
        self.calendar.write(api_constants.SCHEDULER_CALENDAR_DIRECTORY)

        edit_log.open_edit_registry()
        self.setup_tabs()
        self.setup_menu()
        self.saved_edit_id = edit_log.current_edit_id()
        self.autosaved_edit_id = edit_log.current_edit_id()
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

        self.tasks_tab = self.create_tab_and_outliner(
            "Tasks",
            TaskTab
        )
        self.timetable_tab = self.create_tab_and_outliner(
            "Timetable",
            TimetableTab
        )
        self.tracker_tab = self.create_tab_and_outliner(
            "Tracker",
            TrackerTab
        )
        self.suggestions_tab = self.create_tab_and_outliner(
            "Suggestions",
            SuggestionsTab
        )
        self.notes_tab = self.create_tab_and_outliner(
            "Notes",
            NotesTab
        )

        self.tabs_widget.currentChanged.connect(
            self.outliner_stack.setCurrentIndex
        )
        self.tabs_widget.setCurrentIndex(2)

    def create_tab_and_outliner(self, tab_name, tab_class):
        """Create tab and outliner combo for given tab_type.

        Args:
            tab_name (str): name to use for tab.
            tab_class (class): BaseTab subclass to use for class.

        Returns:
            (QtWidgets.QTabWidget): the tab widgter.
        """
        tab_tree_manager = TreeManager()
        outliner = Outliner(self.tree_root, tab_tree_manager)
        self.outliner_stack.addWidget(outliner)
        tab = tab_class(self.tree_root, tab_tree_manager, outliner)
        self.tabs_widget.addTab(tab, tab_name)
        return tab

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
        if self.saved_edit_id != edit_log.current_edit_id():
            self.tree_root.write()
            self.saved_edit_id = edit_log.current_edit_id()
        self.notes_tab.save()

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

    def _autosave(self):
        """Autosave backup file if needed."""
        if self.autosaved_edit_id != edit_log.current_edit_id():
            self.tree_root.write(
                api_constants.SCHEDULER_TASKS_AUTOSAVES_DIRECTORY
            )
            self.autosaved_edit_id = edit_log.current_edit_id()

    def timerEvent(self, event):
        """Called every timer_interval. Used to make autosaves.

        Args:
            event (QtCore.QEvent): the timer event.
        """
        self._autosave()

    def closeEvent(self, event):
        """Called on closing: prompt user to save changes if not done yet.

        Args:
            event (QtCore.QEvent): the close event.
        """
        self._autosave()
        if self.saved_edit_id != edit_log.current_edit_id():
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
                self.tree_root.write()
                self.notes_tab.save()
            event.accept()
        super(SchedulerWindow, self).closeEvent(event)


def run_application():
    """Open application window."""
    app = QtWidgets.QApplication(sys.argv)
    set_style(app, "stylesheet.qss")
    window = SchedulerWindow()
    window.showMaximized()
    app.exec_()
