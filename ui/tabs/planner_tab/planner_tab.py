"""Planner tab."""

from collections import OrderedDict

from scheduler.api.constants import TimePeriod as TP

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
                TitledPlannerListView(name, project, TP.DAY),
            ),
            (
                (DateType.DAY, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, TP.DAY),
            ),
            ## THREE DAYS ##
            (
                (DateType.THREE_DAYS, ViewType.MULTILIST),
                PlannerMultiListWeekView(name, project, num_days=3),
            ),
            (
                (DateType.THREE_DAYS, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, TP.WEEK, num_days=3),
            ),
            ## WEEK ##
            (
                (DateType.WEEK, ViewType.LIST),
                TitledPlannerListView(name, project, TP.WEEK),
            ),
            (
                (DateType.WEEK, ViewType.MULTILIST),
                PlannerMultiListWeekView(name, project),
            ),
            (
                (DateType.WEEK, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, TP.WEEK),
            ),
            ## MONTH ##
            (
                (DateType.MONTH, ViewType.LIST),
                TitledPlannerListView(name, project, TP.MONTH),
            ),
            (
                (DateType.MONTH, ViewType.MULTILIST),
                PlannerMultiListMonthView(name, project),
            ),
            (
                (DateType.MONTH, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, TP.MONTH),
            ),
            ## YEAR ##
            (
                (DateType.YEAR, ViewType.LIST),
                TitledPlannerListView(name, project, TP.YEAR),
            ),
            (
                (DateType.YEAR, ViewType.MULTILIST),
                PlannerMultiListYearView(name, project),
            ),
            (
                (DateType.YEAR, ViewType.HYBRID),
                OverlayedPlannerHybridView(name, project, TP.YEAR),
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
