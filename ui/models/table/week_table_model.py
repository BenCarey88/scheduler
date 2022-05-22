"""Week timetable model."""


from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date

from ._base_table_model import BaseTableModel


class BaseWeekModel(BaseTableModel):
    """Base model for week timetable."""

    def __init__(
            self,
            calendar,
            calendar_week=None,
            num_days=7,
            parent=None):
        """Initialise calendar week model.

        Args:
            calendar (Calendar): the calendar this is using.
            calendar_week (CalendarWeek or None): the calendar week this
                is modelling. If not give, use current week.
            num_days (int): length of week to use, in case week isn't given.
                This allows us to do multi-day views or even single day
                views using the same model.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        if calendar_week is not None and num_days != calendar_week.length:
            raise ValueError(
                "num_days must match week length if week is given"
            )
        if calendar_week is None:
            calendar_week = calendar.get_current_week(length=num_days)
        num_rows = int(
            (Date.DAY_END - Date.DAY_START) / self.TIME_INTERVAL
        )
        num_cols = calendar_week.length
        super(BaseWeekModel, self).__init__(
            calendar,
            calendar_week,
            num_rows,
            num_cols,
            parent=parent,
        )
        self.set_calendar_week = self.set_calendar_period

    @property
    def calendar_week(self):
        """Get calendar week.

        Returns:
            (CalendarWeek): calendar week.
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
                return self.calendar_week.get_day_at_index(section).header_name
        return QtCore.QVariant()


class TrackerWeekModel(BaseWeekModel):
    """Week model used by tracker."""
    TIME_INTERVAL = Date.DAY_END - Date.DAY_START


class SchedulerWeekModel(BaseWeekModel):
    """Week model used by calendar."""
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
                return self.calendar_week.get_day_at_index(section).header_name
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
