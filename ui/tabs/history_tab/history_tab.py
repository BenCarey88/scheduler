"""History tab."""

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.models.timetable import TrackerWeekModel
from scheduler.ui.tabs.base_timetable_tab import (
    BaseTimetableTab,
    BaseWeekTableView
)
from scheduler.ui.widgets.navigation_panel import DateType, ViewType


class HistoryTab(BaseTimetableTab):
    """History tab."""
    def __init__(self, project, parent=None):
        """Setup history tab.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        name = "history"
        main_views_dict = OrderedDict([
            (
                (DateType.WEEK, ViewType.TIMETABLE),
                HistoryView(name, project)
            ),
        ])
        super(HistoryTab, self).__init__(
            name,
            project,
            main_views_dict,
            DateType.WEEK,
            ViewType.TIMETABLE,
            parent=parent,
        )


class HistoryView(BaseWeekTableView):
    """History table view."""
    def __init__(self, name, project, parent=None):
        """Initialise history view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(HistoryView, self).__init__(
            name,
            project,
            TrackerWeekModel(project.calendar),
            parent=parent,
        )
