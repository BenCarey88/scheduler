"""Base Timetable Tab class, for tabs with a timetable element."""

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date

from scheduler.ui.widgets.navigation_panel import (
    NavigationPanel,
    DateType,
    ViewType,
)
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
            main_views_dict,
            date_type,
            view_type,
            parent=None):
        """Initialise tab.

        Args:
            name (str): name of tab (to pass to manager classes).
            project (Project): the project we're working on.
            main_views_dict (OrderedDict(tuple, QtGui.QAbstractItemView))):
                dict of main views keyed by date type and view type tuple.
            date_type (DateType): date type to start with.
            view_type (ViewType): view type to start with.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTimetableTab, self).__init__(
            name,
            project,
            parent=parent,
        )
        self.calendar = project.calendar
        self.date_type = date_type
        self.view_type = view_type
        calendar_period = NavigationPanel.get_current_calendar_period(
            project.calendar,
            self.date_type,
            self.WEEK_START_DAY,
        )
        self.main_views_dict = main_views_dict
        view_types_dict = OrderedDict()
        for date_type, view_type in main_views_dict.keys():
            view_types_dict.setdefault(date_type, []).append(view_type)

        self.navigation_panel = NavigationPanel(
            self.calendar,
            calendar_period,
            view_types_dict,
            parent=self,
        )
        self.main_view = main_views_dict.get((self.date_type, view_type))
        self.main_view.set_to_calendar_period(calendar_period)
        self.main_views_stack = QtWidgets.QStackedWidget()
        for view in self.main_views_dict.values():
            self.main_views_stack.addWidget(view)

        self.outer_layout.addWidget(self.navigation_panel)
        self.outer_layout.addWidget(self.main_views_stack)

        self.navigation_panel.CALENDAR_PERIOD_CHANGED_SIGNAL.connect(
            self.set_to_calendar_period
        )
        self.navigation_panel.DATE_TYPE_CHANGED_SIGNAL.connect(
            self.update_date_type
        )
        self.navigation_panel.VIEW_TYPE_CHANGED_SIGNAL.connect(
            self.update_view_type
        )

    def update(self):
        """Update widget."""
        self.main_view.update()

    def set_to_calendar_period(self, calendar_period):
        """Set main view to calendar period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set.
        """
        self.main_view.set_to_calendar_period(calendar_period)

    def update_date_type(self, date_type, calendar_period):
        """Change main view based on date type.

        Args:
            date_type (DateType): new date type to set.
            calendar_period (BaseCalendarPeriod): calendar period to set.
        """
        self.date_type = date_type
        self.main_view = self.main_views_dict.get((date_type, self.view_type))
        self.main_views_stack.setCurrentWidget(self.main_view)
        self.set_to_calendar_period(calendar_period)

    def update_view_type(self, view_type):
        """Change main view based on view type.

        Args:
            view_type (ViewType): new view type to set.
        """
        self.view_type = view_type
        self.main_view = self.main_views_dict.get((self.date_type, view_type))
        self.main_views_stack.setCurrentWidget(self.main_view)
        self.main_view.update()


class BaseTableView(QtWidgets.QTableView):
    """Base table view for all timetable tabs."""

    def __init__(
            self,
            name,
            project,
            timetable_model,
            parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            timetable_model (BaseTimetableModel): the model we're using for
                this view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTableView, self).__init__(parent=parent)
        self.tree_manager = project.get_tree_manager(name)
        self.tree_root = self.tree_manager.tree_root
        self.calendar = project.calendar
        self.setModel(timetable_model)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        raise NotImplementedError(
            "set to calendar period implemented in BaseTableView subclasses."
        )

    def update(self):
        """Update view."""
        self.viewport().update()
        self.horizontalHeader().viewport().update()


class BaseDayTableView(BaseTableView):
    """Base day table view for timetable tabs."""

    def __init__(
            self,
            name,
            project,
            timetable_day_model,
            parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            timetable_day_model (BaseDayModel): the model we're using for
                this view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseDayTableView, self).__init__(
            name,
            project,
            timetable_day_model,
            parent=parent
        )
        self.calendar_day = self.calendar.get_day(Date.now())
        self.set_to_calendar_period = self.set_to_day

    def set_to_day(self, calendar_day):
        """Set view to given calendar_day.

        Args:
            calendar_day (CalendarDay): calendar day to set to.
        """
        self.calendar_day = calendar_day
        self.model().set_calendar_day(calendar_day)
        self.update()


class BaseWeekTableView(BaseTableView):
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
        super(BaseWeekTableView, self).__init__(
            name,
            project,
            timetable_week_model,
            parent=parent
        )
        self.calendar_week = self.calendar.get_current_week()
        self.set_to_calendar_period = self.set_to_week

    def set_to_week(self, calendar_week):
        """Set view to given calendar_week.

        Args:
            calendar_week (CalendarWeek): calendar week to set to.
        """
        self.calendar_week = calendar_week
        self.model().set_calendar_week(calendar_week)
        self.update()
