"""Base Timetable Tab class, for tabs with a timetable element."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date

from scheduler.ui.widgets.navigation_panel import NavigationPanel
from .base_tab import BaseTab


class BaseTimetableTab(BaseTab):
    """Base tab used for timetable class.

    This tab consists of a navigation panel at the top and a table view below.
    Subclasses must implement their own table view.
    """
    WEEK_START_DAY = Date.SAT

    def __init__(
            self,
            name,
            project,
            main_view,
            parent=None):
        """Initialise tab.

        Args:
            name (str): name of tab (to pass to manager classes).
            project (Project): the project we're working on.
            main_view (QtGui.QAbstractItemView): main_view to provide
                timetable view of items.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTimetableTab, self).__init__(
            name,
            project,
            parent=parent,
        )
        self.calendar = project.calendar
        calendar_week = self.calendar.get_current_week(
            starting_day=self.WEEK_START_DAY
        )

        self.navigation_panel = NavigationPanel(
            self.calendar,
            calendar_week,
            parent=self
        )
        self.main_view = main_view
        self.main_view.set_to_week(calendar_week)
        self.outer_layout.addWidget(self.navigation_panel)
        self.outer_layout.addWidget(self.main_view)

        self.navigation_panel.WEEK_CHANGED_SIGNAL.connect(
            self.main_view.set_to_week
        )

    def update(self):
        """Update widget."""
        self.main_view.viewport().update()


class BaseWeekTableView(QtWidgets.QTableView):
    """Base week table view for timetable tabs."""

    def __init__(
            self,
            name,
            project,
            timetable_week_model,
            parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            timetable_week_model (BaseWeekModel): the model we're using for
                this view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseWeekTableView, self).__init__(parent=parent)
        self.tree_manager = project.get_tree_manager(name)
        self.tree_root = self.tree_manager.tree_root
        self.calendar = project.calendar
        self.calendar_week = self.calendar.get_current_week()
        self.setModel(timetable_week_model)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def set_to_week(self, calendar_week):
        """Set view to given calendar_week.

        Args:
            calendar_week (CalendarWeek): calendar week to set to.
        """
        self.calendar_week = calendar_week
        self.model().set_calendar_week(calendar_week)
        self.viewport().update()
        self.horizontalHeader().viewport().update()
