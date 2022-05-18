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


class TrackerYearModel(BaseYearModel):
    """Year model used by tracker."""


class CalendarYearModel(BaseYearModel):
    """Year model used by calendar."""
