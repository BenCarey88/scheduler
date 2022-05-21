"""Scheduler Qt application."""

import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api import constants as api_constants
from scheduler.api.common import user_prefs
from scheduler.api.edit import edit_log
# from scheduler.api.managers import ScheduleManager, TreeManager
from scheduler.api.project import Project

from . import constants as ui_constants
from .tabs import CalendarTab, HistoryTab, PlannerTab, TaskTab, TrackerTab
# from .tabs.notes_tab import NotesTab
# from .tabs.suggestions_tab import SuggestionsTab
from .utils import custom_message_dialog, set_style, simple_message_dialog


class SchedulerWindow(QtWidgets.QMainWindow):
    """Scheduler window class."""
    CURRENT_TAB_PREF = "current_tab"
    SPLITTER_SIZES = "splitter_sizes"

    def __init__(self, *args, **kwargs):
        """Initialise main window."""
        super(SchedulerWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Scheduler")
        self.resize(1600, 800)

        # TODO: need functionality here for if active project not set
        self.project = Project.read(user_prefs.get_active_project())

        # TODO: make consistent across repo 'tree root' /'task root'
        # self.tree_root = self.project.task_root
        # self.calendar = self.project.calendar
        # self.planner = self.project.planner
        # self.tracker = self.project.tracker
        self.project_user_prefs = self.project.user_prefs

        edit_log.open_edit_registry()
        self.setup_tabs()
        self.setup_menu()
        self.saved_edit = edit_log.latest_edit()
        self.autosaved_edit = edit_log.latest_edit()
        self.startTimer(ui_constants.SHORT_TIMER_INTERVAL)

    def setup_tabs(self):
        """Setup the tabs widget and different pages."""
        splitter = QtWidgets.QSplitter(self)
        self.setCentralWidget(splitter)
        splitter.setChildrenCollapsible(False)

        self.outliner_stack = QtWidgets.QStackedWidget(self)
        self.tabs_widget = QtWidgets.QTabWidget(self)
        splitter.addWidget(self.outliner_stack)
        splitter.addWidget(self.tabs_widget)

        splitter.splitterMoved.connect(self.on_splitter_moved)
        splitter.setSizes(
            user_prefs.get_app_user_pref(self.SPLITTER_SIZES, [1, 1])
        )

        self.tasks_tab = self.create_tab_and_outliner(TaskTab)
        self.planner_tab = self.create_tab_and_outliner(PlannerTab)
        self.calendar_tab = self.create_tab_and_outliner(CalendarTab)
        self.tracker_tab = self.create_tab_and_outliner(TrackerTab)
        self.history_tab = self.create_tab_and_outliner(HistoryTab)
        # self.suggestions_tab = self.create_tab_and_outliner(
        #     "Suggestions",
        #     SuggestionsTab
        # )
        # self.notes_tab = self.create_tab_and_outliner(
        #     "Notes",
        #     NotesTab
        # )

        self.tabs_widget.currentChanged.connect(self.on_tab_changed)
        self.tabs_widget.setCurrentIndex(
            user_prefs.get_app_user_pref(self.CURRENT_TAB_PREF, 0)
        )

    # TODO: neaten up args for this? Maybe add calendar to everything? 
    # Or remove this function altogether?
    def create_tab_and_outliner(self, tab_class, *args, **kwargs):
        """Create tab and outliner combo for given tab_type.

        Args:
            tab_name (str): name to use for tab.
            tab_class (class): BaseTab subclass to use for class.
            args (list): additional args to pass to tab init.
            kwargs (dict): additional kwargs to pass to tab init.

        Returns:
            (QtWidgets.QTabWidget): the tab widget.
        """
        tab = tab_class(
            self.project,
            *args,
            **kwargs
        )
        self.outliner_stack.addWidget(tab.outliner)
        tab_icon = QtGui.QIcon(
            os.path.join(
                os.path.dirname(__file__), "icons", "{0}.png".format(tab.name)
            ),
        )
        self.tabs_widget.addTab(
            tab,
            tab_icon,
            tab.name.capitalize()
        )
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

    def on_tab_changed(self, index):
        """Called when changing to different tab.

        Args:
            index (int): index of new tab.
        """
        user_prefs.set_app_user_pref(self.CURRENT_TAB_PREF, index)
        self.outliner_stack.setCurrentIndex(index)
        self.outliner_stack.currentWidget().update()
        self.tabs_widget.currentWidget().update()

    def on_splitter_moved(self, new_pos, index):
        """Called when splitter is moved.

        Args:
            new_pos (int): new position of splitter.
            index (int): index of splitter moved.
        """
        user_prefs.set_app_user_pref(
            self.SPLITTER_SIZES,
            [self.outliner_stack.width(), self.tabs_widget.width()]
        )

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

        return super(SchedulerWindow, self).keyPressEvent(event)

    def save(self):
        """Save scheduler data."""
        if self.saved_edit != edit_log.latest_edit():
            self.project.write()
        # self.notes_tab.save()

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
        if self.autosaved_edit != edit_log.latest_edit():
            self.project.autosave()

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
        # TODO: add user prefs saves to autosave function?
        user_prefs.save_app_user_prefs()
        # TODO: THIS NEEDS ERROR CATCHING:
        self.project.write_user_prefs()
        if self.saved_edit != edit_log.latest_edit():
            result = custom_message_dialog(
                "Unsaved Changes",
                buttons=[
                    ui_constants.YES_BUTTON,
                    ui_constants.NO_BUTTON,
                    ui_constants.CANCEL_BUTTON
                ],
                informative_text=(
                    "There are unsaved changes. Save before closing?"
                )
            )
            if result == ui_constants.CANCEL_BUTTON:
                event.ignore()
                return
            if result == ui_constants.YES_BUTTON:
                self.save()
            event.accept()

        # hacky, remove this when speed is less of an issue here
        if not api_constants.DEV_MODE:
            # TODO: maybe make this a prompted option rather than always done?
            # or at least give some indication it's happening?
            # and/or maybe also add a check for when last commit was (only do one
            # a day / one every few days / whatever)
            error = self.project.git_backup()
            if error:
                simple_message_dialog(
                    "Git backup failed for {0}".format(
                        self.project.root_directory
                    ),
                    informative_text=error
                )
        super(SchedulerWindow, self).closeEvent(event)


def run_application():
    """Open application window."""
    app = QtWidgets.QApplication(sys.argv)
    set_style(app, "application.qss")
    window = SchedulerWindow()
    window.showMaximized()
    app.exec_()
