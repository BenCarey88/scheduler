"""Multi-list planner views."""

from PyQt5 import QtCore

from scheduler.api.calendar.planned_item import (
    PlannedItem,
    PlannedItemTimePeriod as PITP,
)
from scheduler.ui.tabs.base_calendar_view import (
    BaseMultiListWeekView,
    BaseMultiListMonthView,
    BaseMultiListYearView,
)
from .planner_list_view import TitledPlannerListView


class PlannerMultiListWeekView(BaseMultiListWeekView):
    """Multi list week view for planner."""
    HOVERED_ITEM_SIGNAL = QtCore.pyqtSignal(PlannedItem)
    HOVERED_ITEM_REMOVED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, name, project, parent=None):
        """Initialise multi-list planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        list_views = [
            TitledPlannerListView(name, project, PITP.DAY)
            for _ in range(7)
        ]
        super(PlannerMultiListWeekView, self).__init__(
            name,
            project,
            list_views,
            parent=parent,
        )

    def setup(self):
        """Additional setup after tab init."""
        super(PlannerMultiListWeekView, self).setup()
        for view in self.iter_widgets():
            view.HOVERED_ITEM_SIGNAL.connect(
                self.HOVERED_ITEM_SIGNAL.emit
            )
            view.HOVERED_ITEM_REMOVED_SIGNAL.connect(
                self.HOVERED_ITEM_REMOVED_SIGNAL.emit
            )


class PlannerMultiListMonthView(BaseMultiListMonthView):
    """Multi list month view for planner."""
    HOVERED_ITEM_SIGNAL = QtCore.pyqtSignal(PlannedItem)
    HOVERED_ITEM_REMOVED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, name, project, parent=None):
        """Initialise multi-list planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        list_views = [
            TitledPlannerListView(name, project, PITP.WEEK)
            for _ in range(5)
        ]
        super(PlannerMultiListMonthView, self).__init__(
            name,
            project,
            list_views,
            parent=parent,
        )

    def setup(self):
        """Additional setup after tab init."""
        super(PlannerMultiListMonthView, self).setup()
        for view in self.iter_widgets():
            view.HOVERED_ITEM_SIGNAL.connect(
                self.HOVERED_ITEM_SIGNAL.emit
            )
            view.HOVERED_ITEM_REMOVED_SIGNAL.connect(
                self.HOVERED_ITEM_REMOVED_SIGNAL.emit
            )


class PlannerMultiListYearView(BaseMultiListYearView):
    """Multi list year view for planner."""
    HOVERED_ITEM_SIGNAL = QtCore.pyqtSignal(PlannedItem)
    HOVERED_ITEM_REMOVED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, name, project, parent=None):
        """Initialise multi-list planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        list_views = [
            TitledPlannerListView(name, project, PITP.MONTH)
            for _ in range(12)
        ]
        super(PlannerMultiListYearView, self).__init__(
            name,
            project,
            list_views,
            parent=parent,
        )

    def setup(self):
        """Additional setup after tab init."""
        super(PlannerMultiListYearView, self).setup()
        for view in self.iter_widgets():
            view.HOVERED_ITEM_SIGNAL.connect(
                self.HOVERED_ITEM_SIGNAL.emit
            )
            view.HOVERED_ITEM_REMOVED_SIGNAL.connect(
                self.HOVERED_ITEM_REMOVED_SIGNAL.emit
            )
