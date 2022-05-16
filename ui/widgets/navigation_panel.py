"""Navigation panel for switching dates and view types on timetable views."""

from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date
from scheduler.api.timetable.calendar_period import (
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
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class ViewType(object):
    """Struct representing the different possible view types."""
    LIST = "list"
    TIMETABLE = "timetable"
    SUMMARY = "summary"


class NavigationPanel(QtWidgets.QWidget):
    """Date and view type avigation panel.

    Signals:
        WEEK_CHANGED_SIGNAL (CalendarWeek): emitted when week is changed in
            week view of panel. Argument is the new week.
    """
    CALENDAR_PERIOD_CHANGED_SIGNAL = QtCore.pyqtSignal(BaseCalendarPeriod)
    DATE_TYPE_CHANGED_SIGNAL = QtCore.pyqtSignal(str, BaseCalendarPeriod)
    VIEW_TYPE_CHANGED_SIGNAL = QtCore.pyqtSignal(str)

    def __init__(
            self,
            calendar,
            calendar_period,
            view_types_dict=None,
            parent=None):
        """Setup calendar main view.

        Args:
            calendar (Calendar): calendar item.
            calendar_period (BaseCalendarPeriod): current calendar period for
                panel. The type determines the date type of the view.
            view_types_dict (OrderedDict(DateType, list(ViewType) or None):
                dict associating a list of possible view types for each view
                date type.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(NavigationPanel, self).__init__(parent=parent)
        utils.set_style(self, "navigation_panel.qss")
        self.calendar = calendar
        self.calendar_period = calendar_period
        self.date_type = self.get_date_type(calendar_period)

        # add default view_types_dict for now
        self.view_types_dict = view_types_dict or OrderedDict([
            (DateType.DAY, [ViewType.TIMETABLE, ViewType.LIST]),
            (DateType.WEEK, [ViewType.TIMETABLE]),
            (DateType.MONTH, [ViewType.TIMETABLE]),
            (DateType.YEAR, [ViewType.TIMETABLE]),
        ])
        if not self.view_types_dict.get(self.date_type):
            raise Exception(
                "Date type {0} not allowed for this tab".format(self.date_type)
            )
        self.cached_view_types_dict = {}
        self.cached_calendar_periods = {}
        self.cached_weekday_start = 0

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

    def update(self):
        """Update widget."""
        self.date_label.setText(self.get_date_label())
        self.prev_weekday_button.setHidden(self.date_type != DateType.WEEK)
        self.next_weekday_button.setHidden(self.date_type != DateType.WEEK)

    @staticmethod
    def get_current_calendar_period(calendar, date_type, starting_weekday=0):
        """Get current calendar period.

        Args:
            calendar (Calendar): calendar to get from.
            date_type (DateType): type of calendar period to get.
            starting_weekday (str or int): starting weekday to use if date
                type is week.

        Returns:
            (BaseCalendarPeriod): the calendar period corresponding to the
                current date.
        """
        date = Date.now()
        if date_type == DateType.DAY:
            return calendar.get_day(date)
        if date_type == DateType.WEEK:
            return calendar.get_current_week(starting_weekday)
        if date_type == DateType.MONTH:
            return calendar.get_month(date.year, date.month)
        if date_type == DateType.YEAR:
            return calendar.get_year(date.year)

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
            return DateType.WEEK
        elif isinstance(calendar_period, CalendarMonth):
            return DateType.MONTH
        elif isinstance(calendar_period, CalendarYear):
            return DateType.YEAR

    # TODO: update this label to support day, month etc. viewtypes
    def get_date_label(self):
        """Get date label for current calendar period.

        Returns:
            (str): label to use for date.
        """
        if isinstance(self.calendar_period, CalendarDay):
            weekday_string = self.calendar_period.date.weekday_string()
            ordinal_string = self.calendar_period.date.ordinal_string()
            month_string = self.calendar_period.date.month_string()
            year_string = str(self.calendar_period.date.year)
            return " {0} {1} {2} {3}".format(
                weekday_string,
                ordinal_string,
                month_string,
                year_string,
            )

        elif isinstance(self.calendar_period, CalendarWeek):
            start_date = self.calendar_period.start_date
            end_date = self.calendar_period.end_date
            if start_date.month == end_date.month:
                return " {0} {1}".format(
                    start_date.month_string(short=False),
                    start_date.year
                )
            elif start_date.year == end_date.year:
                return " {0} - {1} {2}".format(
                    start_date.month_string(),
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

        elif isinstance(self.calendar_period, CalendarMonth):
            start_date = self.calendar_period.start_day.date
            return " {0} {1}".format(
                start_date.month_string(),
                start_date.year,
            )

        elif isinstance(self.calendar_period, CalendarYear):
            return str(self.calendar_period.year)

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

        elif self.date_type == DateType.DAY:
            if not isinstance(period, CalendarDay):
                self.calendar_period = period.start_day

        elif self.date_type == DateType.WEEK:
            if isinstance(period, CalendarDay):
                self.calendar_period = self.calendar.get_week_containing_date(
                    period.date,
                    self.cached_weekday_start,
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
        if self.date_type != DateType.WEEK:
            return
        self.calendar_period = self.calendar_period.week_starting_prev_day()
        self.update()
        self.CALENDAR_PERIOD_CHANGED_SIGNAL.emit(self.calendar_period)

    def change_to_next_weekday(self):
        """Set calendar week view to use next week."""
        if self.date_type != DateType.WEEK:
            return
        self.calendar_period = self.calendar_period.week_starting_next_day()
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
            self.date_type_dropdown.setCurrentText(self.view_type)
        self.view_type = self.view_type_dropdown.currentText()
        self.cached_view_types_dict[self.date_type] = self.view_type
        self.update()
        self.DATE_TYPE_CHANGED_SIGNAL.emit(date_type, self.calendar_period)

    def change_view_type(self, view_type):
        """Change view type."""
        self.view_type = view_type
        self.cached_view_types_dict[self.date_type] = self.view_type
        self.VIEW_TYPE_CHANGED_SIGNAL.emit(view_type)
