"""Navigation panel for switching dates and view types on timetable views."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date
from scheduler.api.timetable.calendar_period import CalendarWeek

from scheduler.ui import utils


class NavigationPanel(QtWidgets.QWidget):
    """Date and view type avigation panel.

    Signals:
        WEEK_CHANGED_SIGNAL (CalendarWeek): emitted when week is changed in
            week view of panel. Argument is the new week.
    """
    WEEK_CHANGED_SIGNAL = QtCore.pyqtSignal(CalendarWeek)

    def __init__(self, calendar, calendar_week, parent=None):
        """Setup calendar main view.

        Args:
            calendar (Calendar): calendar item.
            calendar_week (CalendarWeek): current calendar week for panel.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(NavigationPanel, self).__init__(parent=parent)
        # utils.set_style(self, "navigation_panel.qss")
        self.calendar = calendar
        self.calendar_week = calendar_week

        self.setFixedHeight(30)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.date_label = QtWidgets.QLabel(self.get_date_label())
        prev_week_button = QtWidgets.QPushButton("<")
        next_week_button = QtWidgets.QPushButton(">")
        view_type_dropdown = QtWidgets.QComboBox()
        view_type_dropdown.addItems(["week"])

        layout.addWidget(self.date_label)
        layout.addStretch()
        layout.addWidget(prev_week_button)
        layout.addWidget(next_week_button)
        layout.addStretch()
        layout.addWidget(view_type_dropdown)

        prev_week_button.clicked.connect(self.change_to_prev_week)
        next_week_button.clicked.connect(self.change_to_next_week)

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
