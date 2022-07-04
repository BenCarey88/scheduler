"""Base Calendar Tab class, for tabs with a calendar element."""

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date

from scheduler.ui.widgets.navigation_panel import DateType, NavigationPanel
from .base_tab import BaseTab


class BaseCalendarTab(BaseTab):
    """Base tab used for calendar classes.

    This tab consists of a navigation panel at the top and a view below.
    Subclasses must implement their own view. The bases of these views
    can be found in the base_calendar_view module.
    """
    WEEK_START_DAY = Date.SAT

    def __init__(
            self,
            name,
            project,
            main_views_dict,
            date_type,
            view_type,
            hide_day_change_buttons=False,
            use_full_period_names=False,
            parent=None):
        """Initialise tab.

        Args:
            name (str): name of tab (to pass to manager classes).
            project (Project): the project we're working on.
            main_views_dict (OrderedDict(tuple, QtGui.QAbstractItemView))):
                dict of main views keyed by date type and view type tuple.
            date_type (DateType): date type to start with.
            view_type (ViewType): view type to start with.
            hide_day_change_buttons (bool): if True, always hide the day change
                buttons that switch the week views to start on a different day.
            use_full_period_names (bool): if True, use long names for periods
                in navigation bar.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        if (date_type, view_type) not in main_views_dict.keys():
            raise ValueError(
                "date_type and view_type tuple ({0}, {1}) not in "
                "main_views_dict".format(date_type, view_type)
            )
        super(BaseCalendarTab, self).__init__(
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
            start_view_type=self.view_type,
            hide_day_change_buttons=hide_day_change_buttons,
            use_full_period_names=use_full_period_names,
            parent=self,
        )
        self.main_view = main_views_dict.get((self.date_type, self.view_type))
        if not self.main_view:
            raise Exception(
                "Cannot initialise {0} with (date, view) == ({1}, {2})"
                "".format(
                    self.__class__.__name__,
                    self.date_type,
                    self.view_type
                )
            )
        self.main_view.set_to_calendar_period(calendar_period)
        self.main_views_stack = QtWidgets.QStackedWidget()
        for view in self.main_views_dict.values():
            self.main_views_stack.addWidget(view)
            view.setup()
        self.main_views_stack.setCurrentWidget(self.main_view)

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
        super(BaseCalendarTab, self).update()

    def set_to_calendar_period(self, calendar_period):
        """Set main view to calendar period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set.
        """
        self.main_view.set_to_calendar_period(calendar_period)

    def update_date_type(self, date_type, view_type, calendar_period):
        """Change main view based on date type.

        Args:
            date_type (DateType): new date type to set.
            view_type (ViewType): view type of new date type.
            calendar_period (BaseCalendarPeriod): calendar period to set.
        """
        self.date_type = date_type
        self.view_type = view_type
        self.main_view = self.main_views_dict.get((date_type, view_type))
        self.main_views_stack.setCurrentWidget(self.main_view)
        self.set_to_calendar_period(calendar_period)

    def update_view_type(self, view_type, calendar_period):
        """Change main view based on view type.

        Args:
            view_type (ViewType): new view type to set.
            calendar_period (BaseCalendarPeriod): calendar period to set.
        """
        self.view_type = view_type
        self.main_view = self.main_views_dict.get((self.date_type, view_type))
        self.main_views_stack.setCurrentWidget(self.main_view)
        self.set_to_calendar_period(calendar_period)
