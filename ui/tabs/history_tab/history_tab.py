"""History tab."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.models.timetable_week_model import TrackerWeekModel
from scheduler.ui.tabs.base_timetable_tab import (
    BaseTimetableTab,
    BaseWeekTableView
)


class HistoryTab(BaseTimetableTab):
    """History tab."""
    def __init__(self, project, parent=None):
        """Setup history tab.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        name = "history"
        history_view = HistoryView(name, project)
        super(HistoryTab, self).__init__(
            name,
            project,
            history_view,
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
