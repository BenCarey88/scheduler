"""Scheduler Qt application."""

import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api import constants as api_constants
from scheduler.api.common import user_prefs
from scheduler.api.edit import edit_callbacks, edit_log
from scheduler.api.project import Project

from . import constants as ui_constants
from .tabs import SchedulerTab, HistoryTab, PlannerTab, TaskTab, TrackerTab
from .utils import custom_message_dialog, set_style, simple_message_dialog


class SchedulerWindow(QtWidgets.QMainWindow):
    """Scheduler window class."""
    CURRENT_TAB_PREF = "current_tab"
    SPLITTER_SIZES = "splitter_sizes"

    def __init__(self, project_directory=None):
        """Initialise main window.

        Args:
            project_directory (str or None): project directory to use, if set.
        """
        super(SchedulerWindow, self).__init__()
        self.setWindowTitle("Scheduler")
        self.resize(1600, 800)

        # TODO: need functionality here for if active project not set
        project_dir = project_directory or user_prefs.get_active_project()
        self.project = Project.read(project_dir)
        self.project_user_prefs = self.project.user_prefs

        self.setup_tabs()
        self.setup_menu()
        self.saved_edit = edit_log.latest_edit()
        self.autosaved_edit = edit_log.latest_edit()
        self.timer_id = self.startTimer(ui_constants.SHORT_TIMER_INTERVAL)
        edit_log.open_edit_registry()
        edit_callbacks.register_general_purpose_pre_callback(
            self,
            self.pre_edit_callback,
        )
        edit_callbacks.register_general_purpose_post_callback(
            self,
            self.post_edit_callback,
        )

    def setup_tabs(self):
        """Setup the tabs widget and different pages."""
        self.splitter = QtWidgets.QSplitter(self)
        self.setCentralWidget(self.splitter)
        self.splitter.setChildrenCollapsible(False)

        self.outliner_stack = QtWidgets.QStackedWidget(self)
        self.tabs_widget = QtWidgets.QTabWidget(self)
        self.splitter.addWidget(self.outliner_stack)
        self.splitter.addWidget(self.tabs_widget)
        self.current_active_tab = 0

        self.splitter.splitterMoved.connect(self.on_splitter_moved)
        self.splitter.setSizes(
            user_prefs.get_app_user_pref(self.SPLITTER_SIZES, [1, 1])
        )

        self.tasks_tab = self.create_tab_and_outliner(TaskTab)
        self.planner_tab = self.create_tab_and_outliner(PlannerTab)
        self.scheduler_tab = self.create_tab_and_outliner(SchedulerTab)
        self.tracker_tab = self.create_tab_and_outliner(TrackerTab)
        self.history_tab = self.create_tab_and_outliner(HistoryTab)

        self.tabs_widget.currentChanged.connect(self.on_tab_changed)
        self.tabs_widget.setCurrentIndex(
            user_prefs.get_app_user_pref(self.CURRENT_TAB_PREF, 0)
        )
        self.tabs_widget.currentWidget().set_active(True)

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
        self.outliner_stack.addWidget(tab.outliner_panel)
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

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        for tab_num in range(self.tabs_widget.count()):
            self.tabs_widget.widget(tab_num).pre_edit_callback(
                callback_type,
                *args
            )

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        for tab_num in range(self.tabs_widget.count()):
            self.tabs_widget.widget(tab_num).post_edit_callback(
                callback_type,
                *args
            )

    def on_tab_changed(self, index):
        """Called when changing to different tab.

        Args:
            index (int): index of new tab.
        """
        user_prefs.set_app_user_pref(self.CURRENT_TAB_PREF, index)
        self.tabs_widget.widget(self.current_active_tab).set_active(False)
        self.tabs_widget.currentWidget().set_active(True)
        self.current_active_tab = index
        self.outliner_stack.setCurrentIndex(index)
        self.tabs_widget.currentWidget().on_tab_changed()

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
        self.project.autosave()
        if self.saved_edit != edit_log.latest_edit():
            self.project.write()
            self.saved_edit = edit_log.latest_edit()
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
        if event.timerId() == self.timer_id:
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
            backup_git = simple_message_dialog("Backup scheduler data on git?")
            if backup_git:
                error = self.project.git_backup()
                if error:
                    simple_message_dialog(
                        "Git backup failed for {0}".format(
                            self.project.root_directory
                        ),
                        informative_text=error
                    )
        super(SchedulerWindow, self).closeEvent(event)


def run_application(project=None):
    """Open application window.

    Args:
        project (str or None): project directory to use, if set.
    """
    app = QtWidgets.QApplication(sys.argv)
    set_style(app, "application.qss")
    window = SchedulerWindow(project)
    window.showMaximized()
    app.exec_()
