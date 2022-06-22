"""Planner tab."""

from collections import OrderedDict

from scheduler.api.calendar.planned_item import (
    PlannedItemTimePeriod,
)

from scheduler.ui.tabs.base_calendar_tab import BaseCalendarTab
from scheduler.ui.widgets.navigation_panel import DateType, ViewType
from scheduler.ui import utils
from .planner_list_view import PlannerListView

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
                PlannerListView(name, project, PlannedItemTimePeriod.DAY)
            ),
            (
                (DateType.WEEK, ViewType.LIST),
                PlannerListView(name, project, PlannedItemTimePeriod.WEEK)
            ),
            (
                (DateType.MONTH, ViewType.LIST),
                PlannerListView(name, project, PlannedItemTimePeriod.MONTH)
            ),
            (
                (DateType.YEAR, ViewType.LIST),
                PlannerListView(name, project, PlannedItemTimePeriod.MONTH)
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
