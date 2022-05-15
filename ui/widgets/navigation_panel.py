"""Navigation panel for switching dates and view types on timetable views."""

from typing import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date
from scheduler.api.timetable.calendar_period import CalendarWeek

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
    WEEK_CHANGED_SIGNAL = QtCore.pyqtSignal(CalendarWeek)
    DATE_TYPE_CHANGED = QtCore.pyqtSignal(str)
    VIEW_TYPE_CHANGED = QtCore.pyqtSignal(str)

    def __init__(
            self,
            calendar,
            calendar_week,
            view_types_dict=None,
            parent=None):
        """Setup calendar main view.

        Args:
            calendar (Calendar): calendar item.
            calendar_week (CalendarWeek): current calendar week for panel.
            view_types_dict (OrderedDict(DateType, list(ViewType) or None):
                dict associating a list of possible view types for each view
                date type.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(NavigationPanel, self).__init__(parent=parent)
        # utils.set_style(self, "navigation_panel.qss")
        self.calendar = calendar
        self.calendar_week = calendar_week

        # add default view_types_dict for now
        self.view_types_dict = view_types_dict or OrderedDict([
            (DateType.DAY, [ViewType.TIMETABLE, ViewType.LIST]),
            (DateType.WEEK, [ViewType.TIMETABLE]),
        ])
        self.cached_view_types_dict = {}

        self.setFixedHeight(30)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.date_label = QtWidgets.QLabel(self.get_date_label())
        prev_week_button = QtWidgets.QPushButton("<")
        next_week_button = QtWidgets.QPushButton(">")
        self.date_type_dropdown = QtWidgets.QComboBox()
        self.date_type_dropdown.setModel(
            QtCore.QStringListModel(list(self.view_types_dict.keys()))
        )
        self.view_type_dropdown = QtWidgets.QComboBox()
        self.view_type_dropdown.setModel(
            QtCore.QStringListModel(
                list(self.view_types_dict.values())[0]
            )
        )
        self.date_type = self.date_type_dropdown.currentText()
        self.view_type = self.view_type_dropdown.currentText()

        layout.addWidget(self.date_label)
        layout.addStretch()
        layout.addWidget(prev_week_button)
        layout.addWidget(next_week_button)
        layout.addStretch()
        layout.addWidget(self.date_type_dropdown)
        layout.addWidget(self.view_type_dropdown)

        prev_week_button.clicked.connect(self.change_to_prev_week)
        next_week_button.clicked.connect(self.change_to_next_week)
        self.date_type_dropdown.currentTextChanged.connect(
            self.change_date_type
        )
        self.view_type_dropdown.currentTextChanged.connect(
            self.change_view_type
        )

    # TODO: update this label to support day, month etc. viewtypes
    def get_date_label(self):
        """Get date label for current week.

        Returns:
            (str): label to use for date.
        """
        start_date = self.calendar_week.start_date
        end_date = self.calendar_week.end_date
        if start_date.month == end_date.month:
            return " {0} {1}".format(
                Date.month_string_from_int(start_date.month, short=False),
                start_date.year
            )
        elif start_date.year == end_date.year:
            return " {0} - {1} {2}".format(
                Date.month_string_from_int(start_date.month),
                Date.month_string_from_int(end_date.month),
                start_date.year
            )
        else:
            return " {0} {1} - {2} {3}".format(
                Date.month_string_from_int(start_date.month),
                start_date.year,
                Date.month_string_from_int(end_date.month),
                end_date.year
            )

    def change_to_prev_week(self):
        """Set calendar view to use previous week."""
        self.calendar_week = self.calendar_week.prev_week()
        self.date_label.setText(self.get_date_label())
        self.WEEK_CHANGED_SIGNAL.emit(self.calendar_week)

    def change_to_next_week(self):
        """Set calendar view to use next week."""
        self.calendar_week = self.calendar_week.next_week()
        self.date_label.setText(self.get_date_label())
        self.WEEK_CHANGED_SIGNAL.emit(self.calendar_week)

    def change_date_type(self, date_type):
        """Change view date type."""
        self.date_type = date_type
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
        self.DATE_TYPE_CHANGED.emit(date_type)

    def change_view_type(self, view_type):
        """Change view type."""
        self.view_type = view_type
        self.cached_view_types_dict[self.date_type] = self.view_type
        self.VIEW_TYPE_CHANGED.emit(view_type)
