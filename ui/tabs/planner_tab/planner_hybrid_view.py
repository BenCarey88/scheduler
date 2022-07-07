"""Hybrid planner views."""

from scheduler.api.calendar.planned_item import PlannedItemTimePeriod as PITP
from scheduler.ui.tabs.base_calendar_view import BaseHybridView
from scheduler.ui.tabs.scheduler_tab.scheduler_timetable_view import (
    SchedulerTimetableView,
)
from .planner_list_view import TitledPlannerListView
from .planner_multi_list_view import (
    PlannerMultiListWeekView,
    PlannerMultiListMonthView,
    PlannerMultiListYearView,
)


class PlannerHybridDayView(BaseHybridView):
    """Hybrid list-timetable view for day planner."""
    def __init__(self, name, project, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        left_view = TitledPlannerListView(name, project, PITP.DAY)
        right_view = SchedulerTimetableView(name, project, num_days=1)
        super(PlannerHybridDayView, self).__init__(
            left_view,
            right_view,
            parent=parent,
        )


class PlannerHybridWeekView(BaseHybridView):
    """Hybrid list-multilist view for week planner."""
    def __init__(self, name, project, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        left_view = TitledPlannerListView(name, project, PITP.WEEK)
        right_view = PlannerMultiListWeekView(name, project)
        super(PlannerHybridWeekView, self).__init__(
            left_view,
            right_view,
            parent=parent,
        )


class PlannerHybridMonthView(BaseHybridView):
    """Hybrid list-multilist view for month planner."""
    def __init__(self, name, project, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        left_view = TitledPlannerListView(name, project, PITP.MONTH)
        right_view = PlannerMultiListMonthView(name, project)
        super(PlannerHybridMonthView, self).__init__(
            left_view,
            right_view,
            parent=parent,
        )


class PlannerHybridYearView(BaseHybridView):
    """Hybrid list-multilist view for year planner."""
    def __init__(self, name, project, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        left_view = TitledPlannerListView(name, project, PITP.YEAR)
        right_view = PlannerMultiListYearView(name, project)
        super(PlannerHybridYearView, self).__init__(
            left_view,
            right_view,
            parent=parent,
        )
