"""Scheduler Tab."""

from collections import OrderedDict

from scheduler.api.enums import TimePeriod as TP
from scheduler.ui.tabs.base_calendar_tab import BaseCalendarTab
from scheduler.ui.tabs.planner_tab.planner_hybrid_view import (
    OverlayedPlannerHybridView
)
from scheduler.ui.widgets.navigation_panel import DateType, ViewType
from scheduler.ui import utils
from .scheduler_timetable_view import SchedulerTimetableView


class SchedulerTab(BaseCalendarTab):
    """Calendar tab."""

    def __init__(self, project, parent=None):
        """Setup calendar main view.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        name = "scheduler"
        main_views_dict = OrderedDict([
            (
                (DateType.DAY, ViewType.TIMETABLE),
                SchedulerTimetableView(name, project, num_days=1),
            ),
            (
                (DateType.DAY, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, TP.DAY),
            ),
            (
                (DateType.THREE_DAYS, ViewType.TIMETABLE),
                SchedulerTimetableView(name, project, num_days=3),
            ),
            (
                (DateType.THREE_DAYS, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, TP.WEEK, num_days=3),
            ),
            (
                (DateType.WEEK, ViewType.TIMETABLE),
                SchedulerTimetableView(name, project),
            ),
        ])
        super(SchedulerTab, self).__init__(
            name,
            project,
            main_views_dict,
            DateType.WEEK,
            ViewType.TIMETABLE,
            parent=parent,
        )
        utils.set_style(self, "scheduler.qss")
