"""Planner tab."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.models.timetable_week_model import TrackerWeekModel
from scheduler.ui.tabs.base_timetable_tab import (
    BaseTimetableTab,
    BaseWeekTableView
)
from scheduler.ui import utils


class PlannerTab(BaseTimetableTab):
    """Planner tab."""
    def __init__(self, project, parent=None):
        """Setup planner tab.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        name = "planner"
        planner_view = PlannerView(name, project)
        super(PlannerTab, self).__init__(
            name,
            project,
            planner_view,
            parent=parent,
        )
        utils.set_style(self, "planner.qss")


class PlannerView(BaseWeekTableView):
    """Tracker table view."""
    def __init__(self, name, project, parent=None):
        """Initialise planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(PlannerView, self).__init__(
            name,
            project,
            TrackerWeekModel(project.calendar),
            parent=parent,
        )
