"""Planner tab."""

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.calendar.planned_item import PlannedItemTimePeriod

from scheduler.ui.models.list import PlannerListModel
from scheduler.ui.tabs.base_calendar_tab import BaseCalendarTab
from scheduler.ui.tabs.base_calendar_view import BaseListView
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
                (DateType.DAY, ViewType.LIST),
                PlannerView(name, project, PlannedItemTimePeriod.DAY)
            ),
            (
                (DateType.WEEK, ViewType.LIST),
                PlannerView(name, project, PlannedItemTimePeriod.WEEK)
            ),
            (
                (DateType.MONTH, ViewType.LIST),
                PlannerView(name, project, PlannedItemTimePeriod.MONTH)
            ),
            (
                (DateType.YEAR, ViewType.LIST),
                PlannerView(name, project, PlannedItemTimePeriod.MONTH)
            ),
        ])
        super(PlannerTab, self).__init__(
            name,
            project,
            main_views_dict,
            DateType.DAY,
            ViewType.LIST,
            hide_day_change_buttons=True,
            use_full_period_names=True,
            parent=parent,
        )
        utils.set_style(self, "planner.qss")


class PlannerView(BaseListView):
    """Tracker table view."""
    def __init__(self, name, project, time_period, parent=None):
        """Initialise planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            time_period (PlannedItemTimePeriod): type of time period to
                view over.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(PlannerView, self).__init__(
            name,
            project,
            PlannerListModel(
                project.get_planner_manager(),
                time_period=time_period,
            ),
            parent=parent,
        )
        self.header().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        for column in range(self.model().columnCount()):
            self.resizeColumnToContents(column)
        
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)        
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
