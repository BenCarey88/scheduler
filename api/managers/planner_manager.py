"""Planner manager class to manage planned item edits."""

from scheduler.api.edit.planner_edit import (
    AddPlannedItemEdit,
    ModifyPlannedItemEdit,
    MovePlannedItemEdit,
    RemovePlannedItemEdit,
    SortPlannedItemsEdit,
)
from scheduler.api.calendar.planned_item import PlannedItem

from ._base_manager import require_class, BaseCalendarManager


class PlannerManager(BaseCalendarManager):
    """Planner edit manager to apply edits to planned items."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(PlannerManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
            filterer=filterer,
            name=name,
            suffix="planner_manager",
        )

    def create_planned_item(
            self,
            *args,
            index=None,
            parent=None,
            **kwargs):
        """Create planner item and add to calendar.

        Args:
            *args (list): args to be passed to item init.
            index (int or None): index to create at, if given.
            parent (PlannedItem or None): parent planned item,
                if given. 
            **kwargs (dict): kwargs to be passed to item init.

        Returns:
            (bool): whether or not edit was successful.
        """
        item = PlannedItem(*args, **kwargs)
        return AddPlannedItemEdit.create_and_run(item, index, parent)

    @require_class(PlannedItem, True)
    def remove_planned_item(self, planned_item):
        """Remove planned item from calendar.

        Args:
            planned_item (PlannedItem): planned item to remove.

        Returns:
            (bool): whether or not edit was successful
        """
        return RemovePlannedItemEdit.create_and_run(planned_item)

    @require_class(PlannedItem, True)
    def move_planned_item(
            self,
            planned_item,
            calendar_period=None,
            index=None):
        """Move planned item to different index in list.

        Args:
            planned_item (PlannedItem): planned item to remove.
            calendar_period (BaseCalendarPeriod or None): calendar period
                to move to.
            index (int or None): index to move to.

        Returns:
            (bool): whether or not edit was successful.
        """
        return MovePlannedItemEdit.create_and_run(
            planned_item,
            calendar_period=calendar_period,
            index=index,
        )

    @require_class(PlannedItem, True)
    def modify_planned_item(
            self,
            planned_item,
            calendar_period=None,
            tree_item=None,
            name=None):
        """Remove planned item from calendar.

        Args:
            planned_item (PlannedItem): planned item to remove.
            calendar_period (BaseCalendarPeriod or None): calendar period
                item is planned over.
            tree_item (BaseTaskItem or None): the task that this item
                represents.
            name (str or None): the new name of the planned item.

        Returns:
            (bool): whether or not edit was successful.
        """
        attr_dict = {
            planned_item._calendar_period: calendar_period,
            planned_item._tree_item: tree_item,
            planned_item._name: name,
        }
        attr_dict = {
            attr: value
            for attr, value in attr_dict.items() if value is not None
        }
        return ModifyPlannedItemEdit.create_and_run(planned_item, attr_dict)

    def sort_planned_items(self, calendar_period, key=None, reverse=False):
        """Sort order of planned items.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period whose planned
                items we're sorting.
            key (function or None): key to sort by.
            reverse (bool): whether or not to sort in reverse.

        Returns:
            (bool): whether or not edit was successful.
        """
        return SortPlannedItemsEdit.create_and_run(
            calendar_period,
            key=key,
            reverse=reverse,
        )
