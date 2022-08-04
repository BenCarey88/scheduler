"""Base Calendar Tab class, for tabs with a calendar element."""

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date
from scheduler.api.calendar.calendar_period import CalendarWeek

from scheduler.ui.widgets.navigation_panel import NavigationPanel
from .base_tab import BaseTab


class BaseCalendarTab(BaseTab):
    """Base tab used for calendar classes.

    This tab consists of a navigation panel at the top and a view below.
    Subclasses must implement their own view. The bases of these views
    can be found in the base_calendar_view module.
    """
    VIEWS_KEY = "views"
    MAPPINGS_PREF = "date_view_mappings"
    START_DATE_TYPE_PREF = "date_type"
    START_VIEW_TYPE_PREF = "view_type"
    WEEK_START_PREF = "week_start_day"
    WEEK_START_DAY = Date.SAT

    def __init__(
            self,
            name,
            project,
            main_views_dict,
            date_type,
            view_type,
            use_full_period_names=False,
            parent=None):
        """Initialise tab.

        Args:
            name (str): name of tab (to pass to manager classes).
            project (Project): the project we're working on.
            main_views_dict (OrderedDict(tuple, BaseCalendarView))): dict of
                main views keyed by date type and view type tuple.
            date_type (DateType): date type to start with, if none set in
                user prefs.
            view_type (ViewType): view type to start with, if none set in
                user prefs.
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
        self.user_prefs = project.user_prefs
        self.calendar = project.calendar

        # get starting date and view types
        saved_date_type = self.user_prefs.get_attribute(
            [self.name, self.VIEWS_KEY, self.START_DATE_TYPE_PREF]
        )
        if saved_date_type is None:
            saved_date_type = date_type
        saved_view_type = self.user_prefs.get_attribute(
            [self.name, self.VIEWS_KEY, self.START_VIEW_TYPE_PREF]
        )
        if saved_view_type is None:
            saved_view_type = view_type
        if (saved_date_type, saved_view_type) in main_views_dict:
            date_type = saved_date_type
            view_type = saved_view_type
        self.date_type = date_type
        self.view_type = view_type
        date_view_mappings = self.user_prefs.get_attribute(
            [self.name, self.VIEWS_KEY, self.MAPPINGS_PREF],
        )

        weekday_start = self.user_prefs.get_attribute(
            [self.name, self.VIEWS_KEY, self.WEEK_START_PREF],
            self.WEEK_START_DAY,
        )
        calendar_period = NavigationPanel.get_current_calendar_period(
            project.calendar,
            self.date_type,
            weekday_start,
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
            weekday_start=weekday_start,
            default_mappings=date_view_mappings,
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
        self.main_view.set_active(True)

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
        if isinstance(calendar_period, CalendarWeek):
            self.user_prefs.set_attribute(
                [self.name, self.VIEWS_KEY, self.WEEK_START_PREF],
                calendar_period.start_date.weekday,
            )
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
        self.main_view.set_active(False)
        self.main_view = self.main_views_dict.get((date_type, view_type))
        self.main_view.set_active(True)
        self.main_view.on_view_changed()
        self.main_views_stack.setCurrentWidget(self.main_view)
        self._update_day_change_buttons()
        self.set_to_calendar_period(calendar_period)
        self.user_prefs.set_attribute(
            [self.name, self.VIEWS_KEY, self.START_DATE_TYPE_PREF],
            date_type,
        )
        self.user_prefs.set_attribute(
            [self.name, self.VIEWS_KEY, self.START_VIEW_TYPE_PREF],
            view_type,
        )

    def update_view_type(self, view_type, calendar_period):
        """Change main view based on view type.

        Args:
            view_type (ViewType): new view type to set.
            calendar_period (BaseCalendarPeriod): calendar period to set.
        """
        self.view_type = view_type
        self.main_view.set_active(False)
        self.main_view = self.main_views_dict.get((self.date_type, view_type))
        self.main_view.set_active(True)
        self.main_view.on_view_changed()
        self.main_views_stack.setCurrentWidget(self.main_view)
        self._update_day_change_buttons()
        self.set_to_calendar_period(calendar_period)
        self.user_prefs.set_attribute(
            [self.name, self.VIEWS_KEY, self.START_VIEW_TYPE_PREF],
            view_type,
        )
        self.user_prefs.set_attribute(
            [self.name, self.VIEWS_KEY, self.MAPPINGS_PREF, self.date_type],
            view_type,
        )

    def _update_day_change_buttons(self):
        """Update day change buttons in navigation panel according to view."""
        hide_day_change = self.main_view.hide_day_change_buttons
        if hide_day_change != self.navigation_panel.day_change_buttons_hidden:
            self.navigation_panel.set_day_change_buttons_visibility(
                hide_day_change
            )

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(BaseCalendarTab, self).pre_edit_callback(callback_type, *args)
        for view in self.main_views_dict.values():
            view.pre_edit_callback(callback_type, *args)

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(BaseCalendarTab, self).post_edit_callback(callback_type, *args)
        for view in self.main_views_dict.values():
            view.post_edit_callback(callback_type, *args)

    def on_tab_changed(self):
        """Callback for when we change to this tab."""
        super(BaseCalendarTab, self).on_tab_changed()
        self.main_view.on_view_changed()

    def on_outliner_filter_changed(self, *args):
        """Callback for what to do when filter is changed in outliner."""
        super(BaseCalendarTab, self).on_outliner_filter_changed(*args)
        self.main_view.on_outliner_filter_changed()
