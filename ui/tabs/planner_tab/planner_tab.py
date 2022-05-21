"""Planner tab."""

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.models.timetable import TrackerWeekModel
from scheduler.ui.tabs.base_calendar_tab import (
    BaseCalendarTab,
    BaseWeekTableView
)
from scheduler.ui.widgets.navigation_panel import DateType, ViewType
from scheduler.ui import utils


class PlannerTab(BaseCalendarTab):
    """Planner tab."""
    def __init__(self, project, parent=None):
        """Setup planner tab.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        name = "planner"
        main_views_dict = OrderedDict([
            (
                (DateType.WEEK, ViewType.TIMETABLE),
                PlannerView(name, project)
            ),
        ])
        super(PlannerTab, self).__init__(
            name,
            project,
            main_views_dict,
            DateType.WEEK,
            ViewType.TIMETABLE,
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
