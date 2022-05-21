"""Timetable day model."""


from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date

from ._base_table_model import BaseTableModel


class BaseDayModel(BaseTableModel):
    """Base model for day timetable."""

    def __init__(self, calendar, calendar_day=None, parent=None):
        """Initialise calendar day model.

        Args:
            calendar (Calendar): the calendar this is using.
            calendar_day (CalendarDay or None): the calendar day this
                is modelling. If not given, use current day.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        calendar_day = calendar_day or calendar.get_day(Date.now())
        num_rows = int(
            (Date.DAY_END - Date.DAY_START) / self.TIME_INTERVAL
        )
        num_cols = 1
        super(BaseDayModel, self).__init__(
            calendar,
            calendar_day,
            num_rows,
            num_cols,
            parent=parent,
        )
        self.set_calendar_day = self.set_calendar_period

    @property
    def calendar_day(self):
        """Get calendar day.

        Returns:
            (CalendarDay): calendar day.
        """
        return self.calendar_period

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
                return self.calendar_day.header_name
        return QtCore.QVariant()


class TrackerDayModel(BaseDayModel):
    """Day model used by tracker."""
    TIME_INTERVAL = Date.DAY_END - Date.DAY_START


class SchedulerDayModel(BaseDayModel):
    """Day model used by calendar."""
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
                return self.calendar_day.header_name
            else:
                hour_float = Date.DAY_START + self.TIME_INTERVAL * section
                return self.convert_to_time(hour_float)
        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            if orientation == QtCore.Qt.Vertical:
                return (
                    QtCore.Qt.AlignmentFlag.AlignTop |
                    QtCore.Qt.AlignmentFlag.AlignHCenter
                )
        return QtCore.QVariant()
