"""Multi-list planner views."""

from scheduler.api.calendar.planned_item import PlannedItemTimePeriod as PITP
from scheduler.ui.tabs.base_calendar_view import (
    BaseMultiListWeekView,
    BaseMultiListMonthView,
    BaseMultiListYearView,
)
from .planner_list_view import TitledPlannerListView


class PlannerMultiListWeekView(BaseMultiListWeekView):
    """Multi list week view for planner."""
    def __init__(self, name, project, parent=None):
        """Initialise multi-list planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        list_views = [
            TitledPlannerListView(name, project, PITP.DAY) for _ in range(7)
        ]
        super(PlannerMultiListWeekView, self).__init__(
            list_views,
            parent=parent,
        )


class PlannerMultiListMonthView(BaseMultiListMonthView):
    """Multi list month view for planner."""
    def __init__(self, name, project, parent=None):
        """Initialise multi-list planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        list_views = [
            TitledPlannerListView(name, project, PITP.WEEK) for _ in range(5)
        ]
        super(PlannerMultiListMonthView, self).__init__(
            list_views,
            parent=parent,
        )


class PlannerMultiListYearView(BaseMultiListYearView):
    """Multi list year view for planner."""
    def __init__(self, name, project, parent=None):
        """Initialise multi-list planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        list_views = [
            TitledPlannerListView(name, project, PITP.MONTH) for _ in range(12)
        ]
        super(PlannerMultiListYearView, self).__init__(
            list_views,
            parent=parent,
        )
