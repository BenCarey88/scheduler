"""Timetable month model."""


from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, TimeDelta

from ._base_timetable_model import BaseTimetableModel


class BaseMonthModel(BaseTimetableModel):
    """Base model for month timetable."""

    def __init__(
            self,
            calendar,
            calendar_month=None,
            weekday_start=0,
            parent=None):
        """Initialise calendar month model.

        Args:
            calendar (Calendar): the calendar this is using.
            calendar_month (CalendarMonth or None): the calendar month this
                is modelling. If not given, use current month.
            weekday_start (int or str): week starting day, ie. day that
                the leftmost column should represent.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        if isinstance(weekday_start, str):
            weekday_start = Date.weekday_int_from_string(weekday_start)
        self.weekday_start = weekday_start
        if calendar_month is None:
            date = Date.now()
            calendar_month = calendar.get_month(date.year, date.month)
        num_rows = len(calendar_month.get_calendar_weeks(weekday_start))
        num_cols = Date.NUM_WEEKDAYS
        super(BaseMonthModel, self).__init__(
            calendar,
            calendar_month,
            num_rows,
            num_cols,
            parent=parent,
        )

    @property
    def calendar_month(self):
        """Get calendar month.

        Returns:
            (CalendarMonth): calendar month.
        """
        return self.calendar_period

    def set_calendar_month(self, calendar_month):
        """Set calendar month.

        Args:
            calendar_month (CalendarMonth): new calendar month to set.
        """
        self.num_rows = len(calendar_month.get_calendar_weeks())
        self.set_calendar_period(calendar_month)

    def set_week_start_day(self, week_start_day):
        """Set week start day to given day.

        Args:
            week_start_day (int or str): day week is considered to start from.
        """
        if isinstance(weekday_start, str):
            weekday_start = Date.weekday_int_from_string(weekday_start)
        self.weekday_start = weekday_start
        self.num_rows = len(
            self.calendar_month.get_calendar_weeks(weekday_start)
        )
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def day_from_row_and_column(self, row, column):
        """Get calendar day at given row and column.

        Args:
            row (int): row to check.
            column (int): column to check.

        Returns:
            (CalendarDay): calendar day at given cell in table.
        """
        month_start_date = self.calendar_month.start_day.date
        start_weekday = month_start_date.weekday
        start_column = (start_weekday - self.weekday_start) % Date.NUM_WEEKDAYS
        time_delta = TimeDelta(
            days=(column - start_column + row * Date.NUM_WEEKDAYS)
        )
        return self.calendar.get_day(month_start_date + time_delta)

    def data(self, index, role):
        """Get data for given item item and role.
        
        Args:
            index (QtCore.QModelIndex): index of item item.
            role (QtCore.Qt.Role): role we want data for.

        Returns:
            (QtCore.QVariant): data for given item and role.
        """
        if index.isValid():
            day = self.day_from_row_and_column(index.row(), index.column())
            if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
                return (
                    QtCore.Qt.AlignmentFlag.AlignTop |
                    QtCore.Qt.AlignmentFlag.AlignLeft
                )
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return day.date.ordinal_string()
        return QtCore.QVariant()

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        if index.isValid():
            day = self.day_from_row_and_column(index.row(), index.column())
            if day.calendar_month == self.calendar_month:
                return QtCore.Qt.ItemFlag.ItemIsEnabled
        return QtCore.Qt.ItemFlag.NoItemFlags            

    def headerData(self, section, orientation, role):
        """Get header data.
        
        Args:
            section (int): row/column we want header data for.
            orientation (QtCore.Qt.Orientaion): orientation of widget.
            role (QtCore.Qt.Role): role we want header data for.

        Returns:
            (QtCore.QVariant): header data.
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return Date.weekday_string_from_int(
                    section - self.weekday_start
                )
        return QtCore.QVariant()


class TrackerMonthModel(BaseMonthModel):
    """Month model used by tracker."""


class SchedulerMonthModel(BaseMonthModel):
    """Month model used by calendar."""
