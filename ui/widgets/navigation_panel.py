"""Navigation panel for switching dates and view types on timetable views."""

from calendar import weekday
from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, TimeDelta
from scheduler.api.calendar import (
    BaseCalendarPeriod,
    CalendarDay,
    CalendarWeek,
    CalendarMonth,
    CalendarYear,
)

from scheduler.ui import utils


class DateType(object):
    """Struct representing the different possible date spans for a view."""
    DAY = "day"
    THREE_DAYS = "three days"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class ViewType(object):
    """Struct representing the different possible view types."""
    LIST = "list"
    MULTILIST = "multi-list"
    TIMETABLE = "timetable"
    SUMMARY = "summary"
    HYBRID = "hybrid"


class NavigationPanel(QtWidgets.QWidget):
    """Date and view type avigation panel.

    Signals:
        WEEK_CHANGED_SIGNAL (CalendarWeek): emitted when week is changed in
            week view of panel. Argument is the new week.
    """
    CALENDAR_PERIOD_CHANGED_SIGNAL = QtCore.pyqtSignal(BaseCalendarPeriod)
    DATE_TYPE_CHANGED_SIGNAL = QtCore.pyqtSignal(str, str, BaseCalendarPeriod)
    VIEW_TYPE_CHANGED_SIGNAL = QtCore.pyqtSignal(str, BaseCalendarPeriod)

    def __init__(
            self,
            calendar,
            calendar_period,
            view_types_dict,
            start_view_type=None,
            default_mappings=None,
            weekday_starts=None,
            hide_day_change_buttons=False,
            use_full_period_names=False,
            use_week_for_day=False,
            parent=None):
        """Setup calendar main view.

        Args:
            calendar (Calendar): calendar object.
            calendar_period (BaseCalendarPeriod): current calendar period for
                panel. The type determines the date type of the view.
            view_types_dict (OrderedDict(DateType, list(ViewType)): dict
                associating a list of possible view types for each view date
                type.
            start_view_type (ViewType or None): start view type, if given.
            default_mappings (dict or None): default mappings of date type
                and view types, if given.
            weekday_starts (dict(DateType, str or int)): default starting
                weekday to use for each date type that uses calendar weeks.
            day_change_buttons_hidden (bool): if True, always hide the day
                change buttons that switch the week views to start on a
                different day.
            use_full_period_names (bool): if True, use long names for periods.
            use_week_for_day (bool): if True, use calendar week item to
                represent a calendar day in the navigation panel. In practice,
                I don't intend to use this, as I think it's easier for the
                navigation panel to always return the relevant period and take
                care of switching type if needed in the view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(NavigationPanel, self).__init__(parent=parent)
        utils.set_style(self, "navigation_panel.qss")
        self.calendar = calendar
        self.calendar_period = calendar_period
        self.date_type = self.get_date_type(calendar_period)
        self.day_change_buttons_hidden = hide_day_change_buttons
        self.use_full_period_names = use_full_period_names
        self.use_week_for_day = use_week_for_day
        if use_week_for_day and isinstance(calendar_period, CalendarDay):
            raise Exception(
                "Can't use CalendarDay with use_week_for_day flag."
            )

        self.view_types_dict = view_types_dict
        if not self.view_types_dict.get(self.date_type):
            raise Exception(
                "Date type {0} not allowed for this tab".format(self.date_type)
            )
        self.cached_view_types_dict = default_mappings or {}
        self.cached_calendar_periods = {}
        self.cached_weekday_starts = {}
        if weekday_starts is None:
            weekday_starts = {}
        for date_type in (DateType.WEEK, DateType.THREE_DAYS):
            weekday_start = weekday_starts.get(date_type, 0)
            if isinstance(weekday_start, str):
                weekday_start = Date.weekday_int_from_string(weekday_start)
            self.cached_weekday_starts[date_type] = weekday_start

        self.setFixedHeight(30)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.date_label = QtWidgets.QLabel(self.get_date_label())
        prev_button = QtWidgets.QPushButton("<<")
        next_button = QtWidgets.QPushButton(">>")
        self.prev_weekday_button = QtWidgets.QPushButton("<")
        self.next_weekday_button = QtWidgets.QPushButton(">")
        self.prev_weekday_button.setFixedWidth(30)
        self.next_weekday_button.setFixedWidth(30)
        self.date_type_dropdown = QtWidgets.QComboBox()
        self.date_type_dropdown.setModel(
            QtCore.QStringListModel(list(self.view_types_dict.keys()))
        )
        self.date_type_dropdown.setCurrentText(self.date_type)
        self.view_type_dropdown = QtWidgets.QComboBox()
        self.view_type_dropdown.setModel(
            QtCore.QStringListModel(self.view_types_dict.get(self.date_type))
        )
        if (start_view_type and
                start_view_type in self.view_types_dict.get(self.date_type)):
            self.view_type_dropdown.setCurrentText(start_view_type)
        self.view_type = self.view_type_dropdown.currentText()

        layout.addWidget(self.date_label)
        layout.addStretch()
        layout.addWidget(self.prev_weekday_button)
        layout.addWidget(prev_button)
        layout.addWidget(next_button)
        layout.addWidget(self.next_weekday_button)
        layout.addStretch()
        layout.addWidget(self.date_type_dropdown)
        layout.addWidget(self.view_type_dropdown)

        prev_button.clicked.connect(self.change_to_prev_period)
        next_button.clicked.connect(self.change_to_next_period)
        self.prev_weekday_button.clicked.connect(
            self.change_to_prev_weekday
        )
        self.next_weekday_button.clicked.connect(
            self.change_to_next_weekday
        )
        self.date_type_dropdown.currentTextChanged.connect(
            self.change_date_type
        )
        self.view_type_dropdown.currentTextChanged.connect(
            self.change_view_type
        )
        self.update()

    def update(self):
        """Update widget."""
        self.date_label.setText(self.get_date_label())
        self.prev_weekday_button.setHidden(
            self.day_change_buttons_hidden or
            self.date_type not in [DateType.THREE_DAYS, DateType.WEEK]
        )
        self.next_weekday_button.setHidden(
            self.day_change_buttons_hidden or
            self.date_type not in [DateType.THREE_DAYS, DateType.WEEK]
        )
        super(NavigationPanel, self).update()

    @staticmethod
    def get_current_calendar_period(
            calendar,
            date_type,
            starting_weekday=0,
            use_week_for_day=False):
        """Get current calendar period.

        Args:
            calendar (Calendar): calendar to get from.
            date_type (DateType): type of calendar period to get.
            starting_weekday (str or int): starting weekday to use if date
                type is week.
            use_week_for_day (bool): if True, we use a one day week in place
                of a calendar day, to allow it to make use of a week model.

        Returns:
            (BaseCalendarPeriod): the calendar period corresponding to the
                current date.
        """
        period_type = {
            DateType.DAY: CalendarWeek if use_week_for_day else CalendarDay,
            DateType.THREE_DAYS: CalendarWeek,
            DateType.WEEK: CalendarWeek,
            DateType.MONTH: CalendarMonth,
            DateType.YEAR: CalendarYear,
        }.get(date_type)
        if not period_type:
            raise NotImplementedError(
                "Can't run get_current_calendar_period with date_type {0}"
                "".format(date_type)
            )
        length = {
            DateType.DAY: 1,
            DateType.THREE_DAYS: 3,
        }.get(date_type, 7)
        starting_weekday = {
            DateType.THREE_DAYS: Date.now().weekday,
        }.get(date_type, starting_weekday)
        return calendar.get_current_period(
            period_type,
            starting_weekday,
            length,
        )

    @staticmethod
    def get_date_type(calendar_period):
        """Get date type corresponding to given calendar period.

        Args:
            calendar_period (BaseCalendarPeriod): the calendar period.

        Returns:
            (DateType): the date type.
        """
        if isinstance(calendar_period, CalendarDay):
            return DateType.DAY
        elif isinstance(calendar_period, CalendarWeek):
            if calendar_period.length == 7:
                return DateType.WEEK
            elif calendar_period.length == 3:
                return DateType.THREE_DAYS
            elif calendar_period.length == 1:
                return DateType.DAY
        elif isinstance(calendar_period, CalendarMonth):
            return DateType.MONTH
        elif isinstance(calendar_period, CalendarYear):
            return DateType.YEAR
        raise Exception(
            "cannot find date type for calendar period {0}".format(
                calendar_period.name
            )
        )

    def get_date_label(self, calendar_period=None):
        """Get date label for current calendar period.

        Args:
            calendar_period (BaseCalendarPeriod or None): calendar period
                to get label for. If None, use self.calendar_period.

        Returns:
            (str): label to use for date.
        """
        if calendar_period is None:
            calendar_period = self.calendar_period

        if isinstance(calendar_period, CalendarDay):
            weekday_string = calendar_period.date.weekday_string()
            ordinal_string = calendar_period.date.ordinal_string()
            month_string = calendar_period.date.month_string()
            year_string = str(calendar_period.date.year)
            if self.use_full_period_names:
                return " {0} {1} {2} {3}".format(
                    weekday_string,
                    ordinal_string,
                    month_string,
                    year_string,
                )
            else:
                return " {0} {1}".format(month_string, year_string)

        elif isinstance(calendar_period, CalendarWeek):
            # calendar day
            if calendar_period.length == 1:
                return self.get_date_label(calendar_period.start_day)

            # 3 days or calendar week
            start_date = calendar_period.start_date
            end_date = calendar_period.end_date
            if start_date.month == end_date.month:
                if self.use_full_period_names:
                    return " {0} {1} - {2} {3} {4} {5}".format(
                        start_date.weekday_string(),
                        start_date.ordinal_string(),
                        end_date.weekday_string(),
                        end_date.ordinal_string(),
                        start_date.month_string(short=False),
                        start_date.year,
                    )
                else:
                    return " {0} {1}".format(
                        start_date.month_string(short=False),
                        start_date.year,
                    )

            elif start_date.year == end_date.year:
                if self.use_full_period_names:
                    return " {0} {1} {2} - {3} {4} {5} {6}".format(
                        start_date.weekday_string(),
                        start_date.ordinal_string(),
                        start_date.month_string(),
                        end_date.weekday_string(),
                        end_date.ordinal_string(),
                        end_date.month_string(),
                        start_date.year,
                    )
                else:
                    return " {0} - {1} {2}".format(
                        start_date.month_string(),
                        end_date.month_string(),
                        start_date.year,
                    )

            else:
                if self.use_full_period_names:
                    return " {0} {1} {2} {3} - {4} {5} {6} {7}".format(
                        start_date.weekday_string(),
                        start_date.ordinal_string(),
                        start_date.month_string(),
                        end_date.year,
                        end_date.weekday_string(),
                        end_date.ordinal_string(),
                        end_date.month_string(),
                        start_date.year,
                    )
                else:
                    return " {0} {1} - {2} {3}".format(
                        start_date.month_string(),
                        start_date.year,
                        end_date.month_string(),
                        end_date.year,
                    )

        elif isinstance(calendar_period, CalendarMonth):
            start_date = calendar_period.start_day.date
            return " {0} {1}".format(
                start_date.month_string(),
                start_date.year,
            )

        elif isinstance(calendar_period, CalendarYear):
            return str(calendar_period.year)

    def _update_calendar_period(self):
        """Update calendar period to match current date type.

        Note that we don't emit CALENDAR_PERIOD_CHANGED_SIGNAL here because
        this is called after changing date type which emits DATE_TYPE_CHANGED
        instead, and this should be handled separately.
        """
        period = self.calendar_period
        cached_period = self.cached_calendar_periods.get(self.date_type)
        if (cached_period and period.contains(cached_period)):
            # use cached period if it's contained in current one
            self.calendar_period = cached_period

        # TODO: this logic doesn't really work - the week containing date thing
        # needs to be revisited for 1-day weeks.
        elif self.date_type == DateType.DAY:
            if self.use_week_for_day and isinstance(period, CalendarWeek):
                self.calendar_period = self.calendar.get_week_containing_date(
                    period.start_date,
                    self.cached_weekday_starts.get(DateType.WEEK),
                    length=1,
                )
            elif (self.use_week_for_day and
                        isinstance(period, (CalendarMonth, CalendarYear))):
                    self.calendar_period = period.get_start_week(
                        self.cached_weekday_starts.get(DateType.WEEK),
                        length=1,
                    )
            elif not isinstance(period, CalendarDay):
                self.calendar_period = period.start_day

        elif self.date_type == DateType.THREE_DAYS:
            if isinstance(period, CalendarDay):
                self.calendar_period = self.calendar.get_week_containing_date(
                    period.date,
                    self.cached_weekday_starts.get(DateType.THREE_DAYS),
                    length=3,
                )
            elif isinstance(period, CalendarWeek):
                self.calendar_period = self.calendar.get_week_containing_date(
                    period.start_date,
                    self.cached_weekday_starts.get(DateType.THREE_DAYS),
                    length=3,
                )
            elif isinstance(period, (CalendarMonth, CalendarYear)):
                self.calendar_period = period.get_start_week(
                    self.cached_weekday_starts.get(DateType.THREE_DAYS),
                    length=3,
                )

        elif self.date_type == DateType.WEEK:
            if isinstance(period, CalendarDay):
                self.calendar_period = self.calendar.get_week_containing_date(
                    period.date,
                    self.cached_weekday_starts.get(DateType.WEEK),
                )
            if isinstance(period, CalendarWeek):
                self.calendar_period = self.calendar.get_week_containing_date(
                    period.start_date,
                    self.cached_weekday_starts.get(DateType.WEEK),
                )
            elif isinstance(period, (CalendarMonth, CalendarYear)):
                self.calendar_period = period.get_start_week(
                    self.cached_weekday_start
                )

        elif self.date_type == DateType.MONTH:
            if isinstance(period, CalendarDay):
                self.calendar_period = period.calendar_month
            if isinstance(period, CalendarWeek):
                self.calendar_period = period.start_day.calendar_month
            elif isinstance(period, CalendarYear):
                self.calendar_period = self.calendar.get_month(period.year, 1)

        elif self.date_type == DateType.YEAR:
            if isinstance(period, (CalendarDay, CalendarMonth)):
                self.calendar_period = period.calendar_year
            elif isinstance(period, CalendarWeek):
                self.calendar_period = period.start_day.calendar_year

        else:
            raise Exception(
                "DateType {0} not currently supported".format(self.date_type)
            )

    def change_to_prev_period(self):
        """Set calendar view to use previous period."""
        self.calendar_period = self.calendar_period.prev()
        self.update()
        self.CALENDAR_PERIOD_CHANGED_SIGNAL.emit(self.calendar_period)

    def change_to_next_period(self):
        """Set calendar view to use next period."""
        self.calendar_period = self.calendar_period.next()
        self.update()
        self.CALENDAR_PERIOD_CHANGED_SIGNAL.emit(self.calendar_period)

    def change_to_prev_weekday(self):
        """Set calendar week view to use previous week."""
        if not isinstance(self.calendar_period, CalendarWeek):
            return
        self.calendar_period = self.calendar_period.week_starting_prev_day()
        self.cached_weekday_starts[self.date_type] -= 1
        self.update()
        self.CALENDAR_PERIOD_CHANGED_SIGNAL.emit(self.calendar_period)

    def change_to_next_weekday(self):
        """Set calendar week view to use next week."""
        if not isinstance(self.calendar_period, CalendarWeek):
            return
        self.calendar_period = self.calendar_period.week_starting_next_day()
        self.cached_weekday_starts[self.date_type] += 1
        self.update()
        self.CALENDAR_PERIOD_CHANGED_SIGNAL.emit(self.calendar_period)

    def change_date_type(self, date_type):
        """Change view date type."""
        # cache old calendar period
        self.cached_calendar_periods[self.date_type] = self.calendar_period
        # switch date
        self.date_type = date_type
        # now update to new calendar period
        self._update_calendar_period()
        allowed_view_types = self.view_types_dict[date_type]
        with utils.suppress_signals(self.view_type_dropdown):
            self.view_type_dropdown.setModel(
                QtCore.QStringListModel(allowed_view_types)
            )
            if date_type in self.cached_view_types_dict:
                self.view_type_dropdown.setCurrentText(
                    self.cached_view_types_dict[date_type]
                )
            elif self.view_type in allowed_view_types:
                self.view_type_dropdown.setCurrentText(self.view_type)
        self.view_type = self.view_type_dropdown.currentText()
        self.cached_view_types_dict[self.date_type] = self.view_type
        self.update()
        self.DATE_TYPE_CHANGED_SIGNAL.emit(
            date_type,
            self.view_type,
            self.calendar_period,
        )

    def change_view_type(self, view_type):
        """Change view type."""
        self.view_type = view_type
        self.cached_view_types_dict[self.date_type] = self.view_type
        self.VIEW_TYPE_CHANGED_SIGNAL.emit(view_type, self.calendar_period)

    def set_day_change_buttons_visibility(self, value):
        """Hide or unhide day change buttons.

        Args:
            value (bool): whether to hide or unhide.
        """
        self.day_change_buttons_hidden = value
        self.update()
