"""Timetable year model."""


from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, TimeDelta

from ._base_timetable_model import BaseTimetableModel


class BaseYearModel(BaseTimetableModel):
    """Base model for year timetable."""

    def __init__(
            self,
            calendar,
            calendar_year=None,
            parent=None):
        """Initialise calendar year model.

        Args:
            calendar (Calendar): the calendar this is using.
            calendar_year (CalendarYear or None): the calendar year this
                is modelling. If not given, use current year.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        if calendar_year is None:
            calendar_year = calendar.get_year(Date.now().year)
        num_rows = 3
        num_cols = 4
        super(BaseYearModel, self).__init__(
            calendar,
            calendar_year,
            num_rows,
            num_cols,
            parent=parent,
        )
        self.set_calendar_year = self.set_calendar_period

    @property
    def calendar_year(self):
        """Get calendar year.

        Returns:
            (CalendarYear): calendar year.
        """
        return self.calendar_period

    def month_from_row_and_column(self, row, column):
        """Get month at given row and column.

        Args:
            row (int): row to check.
            column (int): column to check.

        Returns:
            (CalendarMonth): calendar month.
        """
        month_num = column + row * self.num_cols + 1
        return self.calendar.get_month(
            self.calendar_year.year,
            month_num
        )

    def data(self, index, role):
        """Get data for given item item and role.
        
        Args:
            index (QtCore.QModelIndex): index of item item.
            role (QtCore.Qt.Role): role we want data for.

        Returns:
            (QtCore.QVariant): data for given item and role.
        """
        if index.isValid():
            calendar_month = self.month_from_row_and_column(
                index.row(),
                index.column()
            )
            if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
                return (
                    QtCore.Qt.AlignmentFlag.AlignTop |
                    QtCore.Qt.AlignmentFlag.AlignLeft
                )
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return calendar_month.name
        return QtCore.QVariant()


class TrackerYearModel(BaseYearModel):
    """Year model used by tracker."""


class SchedulerYearModel(BaseYearModel):
    """Year model used by calendar."""
