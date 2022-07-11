"""Planner tab."""

from collections import OrderedDict

from scheduler.api.calendar.planned_item import PlannedItemTimePeriod as PITP

from scheduler.ui.tabs.base_calendar_tab import BaseCalendarTab
from scheduler.ui.widgets.navigation_panel import DateType, ViewType
from scheduler.ui import utils
from .planner_list_view import TitledPlannerListView
from .planner_multi_list_view import (
    PlannerMultiListWeekView,
    PlannerMultiListMonthView,
    PlannerMultiListYearView,
)
from .planner_hybrid_view import (
    PlannerHybridView,
    OverlayedPlannerHybridView,
)


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
            ## DAY ##
            (
                (DateType.DAY, ViewType.LIST),
                TitledPlannerListView(name, project, PITP.DAY),
            ),
            (
                (DateType.DAY, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, PITP.DAY),
            ),
            ## WEEK ##
            (
                (DateType.WEEK, ViewType.LIST),
                TitledPlannerListView(name, project, PITP.WEEK),
            ),
            (
                (DateType.WEEK, ViewType.MULTILIST),
                PlannerMultiListWeekView(name, project),
            ),
            (
                (DateType.WEEK, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, PITP.WEEK),
            ),
            ## MONTH ##
            (
                (DateType.MONTH, ViewType.LIST),
                TitledPlannerListView(name, project, PITP.MONTH),
            ),
            (
                (DateType.MONTH, ViewType.MULTILIST),
                PlannerMultiListMonthView(name, project),
            ),
            (
                (DateType.MONTH, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, PITP.MONTH),
            ),
            ## YEAR ##
            (
                (DateType.YEAR, ViewType.LIST),
                TitledPlannerListView(name, project, PITP.YEAR),
            ),
            (
                (DateType.YEAR, ViewType.MULTILIST),
                PlannerMultiListYearView(name, project),
            ),
            (
                (DateType.YEAR, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, PITP.YEAR),
            ),
        ])
        super(PlannerTab, self).__init__(
            name,
            project,
            main_views_dict,
            DateType.YEAR,
            ViewType.MULTILIST,
            hide_day_change_buttons=True,
            use_full_period_names=True,
            parent=parent,
        )
        utils.set_style(self, "planner.qss")
