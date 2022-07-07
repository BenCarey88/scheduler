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
    PlannerHybridDayView,
    PlannerHybridWeekView,
    PlannerHybridMonthView,
    PlannerHybridYearView,
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
                TitledPlannerListView(name, project, PITP.DAY)
            ),
            (
                (DateType.DAY, ViewType.HYBRID),
                PlannerHybridDayView(name, project)
            ),
            ## WEEK ##
            (
                (DateType.WEEK, ViewType.LIST),
                TitledPlannerListView(name, project, PITP.WEEK)
            ),
            (
                (DateType.WEEK, ViewType.MULTILIST),
                PlannerMultiListWeekView(name, project)
            ),
            (
                (DateType.WEEK, ViewType.HYBRID),
                PlannerHybridWeekView(name, project)
            ),
            ## MONTH ##
            (
                (DateType.MONTH, ViewType.LIST),
                TitledPlannerListView(name, project, PITP.MONTH)
            ),
            (
                (DateType.MONTH, ViewType.MULTILIST),
                PlannerMultiListMonthView(name, project)
            ),
            (
                (DateType.MONTH, ViewType.HYBRID),
                PlannerHybridMonthView(name, project)
            ),
            ## YEAR ##
            (
                (DateType.YEAR, ViewType.LIST),
                TitledPlannerListView(name, project, PITP.YEAR)
            ),
            (
                (DateType.YEAR, ViewType.MULTILIST),
                PlannerMultiListYearView(name, project)
            ),
            (
                (DateType.YEAR, ViewType.HYBRID),
                PlannerHybridYearView(name, project)
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

    #     pm = project.get_planner_manager()
    #     pm.register_pre_item_added_callback(self, self.pre_item_added)
    #     pm.register_item_added_callback(self, self.on_item_added)
    #     pm.register_pre_item_removed_callback(self, self.pre_item_removed)
    #     pm.register_item_removed_callback(self, self.on_item_removed)
    #     pm.register_pre_item_moved_callback(self, self.pre_item_moved)
    #     pm.register_item_moved_callback(self, self.on_item_moved)
    #     pm.register_item_modified_callback(self, self.on_item_modified)
    #     pm.register_pre_full_update_callback(self, self.pre_full_update)
    #     pm.register_full_update_callback(self, self.on_full_update)

    # ### Callbacks ###
    # def pre_item_added(self, item, row):
    #     """Callback for before an item has been added.

    #     Args:
    #         item (PlannedItem): the item to add.
    #         row (int): the index the item will be added at.
    #     """
    #     for model in self.main_view.get_models():
    #         model.pre_item_added(item, row)

    # def on_item_added(self, item, row):
    #     """Callback for after an item has been added.

    #     Args:
    #         item (PlannedItem): the added item.
    #         row (int): the index the item was added at.
    #     """
    #     for model in self.main_view.get_models():
    #         model.on_item_added(item, row)

    # def pre_item_removed(self, item, row):
    #     """Callbacks for before an item is removed.

    #     Args:
    #         item (PlannedItem): the item to remove.
    #         row (int): the index the item will be removed from.
    #     """
    #     for model in self.main_view.get_models():
    #         model.pre_item_removed(item, row)

    # def on_item_removed(self, item, row):
    #     """Callback for after an item has been removed.

    #     Args:
    #         item (PlannedItem): the item that was removed.
    #         row (int): the index the item was removed from.
    #     """
    #     for model in self.main_view.get_models():
    #         model.on_item_added(item, row)

    # def pre_item_moved(self, item, old_row, new_row):
    #     """Callback for before an item is moved.

    #     Args:
    #         item (PlannedItem): the item to move.
    #         old_row (int): the original index of the item.
    #         new_row (int): the new index of the moved item.
    #     """
    #     for model in self.main_view.get_models():
    #         model.pre_item_moved(item, old_row, new_row)

    # def on_item_moved(self, item, old_row, new_row):
    #     """Callback for after an item has been moved.

    #     Args:
    #         item (PlannedItem): the item that was moved.
    #         old_row (int): the original index of the item.
    #         new_row (int): the new index of the moved item.
    #     """
    #     for model in self.main_view.get_models():
    #         model.on_item_moved(item, old_row, new_row)

    # def on_item_modified(self, old_item, new_item):
    #     """Callback for after an item has been modified.

    #     Args:
    #         old_item (BaseTreeItem): the item that was modified.
    #         new_item (BaseTreeItem): the item after modification.
    #     """
    #     for model in self.main_view.get_models():
    #         model.on_item_modified(old_item, new_item)

    # def pre_full_update(self):
    #     """Callbacks for before a full reset."""
    #     for model in self.main_view.get_models():
    #         model.pre_full_update()

    # def on_full_update(self):
    #     """Callback for after a full reset."""
    #     for model in self.main_view.get_models():
    #         model.on_full_update()
