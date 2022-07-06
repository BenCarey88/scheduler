"""Planner edit manager class to manage planned item edits."""

from scheduler.api.edit.planner_edit import (
    AddPlannedItemEdit,
    ModifyPlannedItemEdit,
    MovePlannedItemEdit,
    RemovePlannedItemEdit,
    SortPlannedItemsEdit,
)
from scheduler.api.calendar.planned_item import PlannedItem

from .._base_manager import require_class
from ._base_planner_manager import BasePlannerManager
from ._planner_callbacks import PLANNER_CALLBACKS as PC


class PlannerEditManager(BasePlannerManager):
    """Planner edit manager to apply edits to planned items."""
    register_pre_item_added_callback = PC.register_pre_item_added_callback
    register_item_added_callback = PC.register_item_added_callback
    register_pre_item_removed_callback = PC.register_pre_item_removed_callback
    register_item_removed_callback = PC.register_item_removed_callback
    register_pre_item_modified_callback = PC.register_item_modified_callback
    register_item_modified_callback = PC.register_item_modified_callback
    register_pre_item_moved_callback = PC.register_pre_item_moved_callback
    register_item_moved_callback = PC.register_item_moved_callback
    register_pre_full_update_callback = PC.register_pre_full_update_callback
    register_full_update_callback = PC.register_full_update_callback
    remove_callbacks = PC.remove_callbacks

    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            archive_calendar (Calendar): archive calendar object.
        """
        super(PlannerEditManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
        )

    def create_planned_item(self, *args, index=None, **kwargs):
        """Create planner item and add to calendar.

        Args:
            *args (list): args to be passed to item init.
            index (int or None): index to create at, if given.
            **kwargs (dict): kwargs to be passed to item init.

        Returns:
            (bool): whether or not edit was successful.
        """
        item = PlannedItem(*args, **kwargs)
        edit = AddPlannedItemEdit(item, index)
        if edit.is_valid:
            edit.run()
        return edit.is_valid

    @require_class(PlannedItem, True)
    def remove_planned_item(self, planned_item):
        """Remove planned item from calendar.

        Args:
            planned_item (PlannedItem): planned item to remove.

        Returns:
            (bool): whether or not edit was successful
        """
        edit = RemovePlannedItemEdit(planned_item)
        if edit.is_valid:
            edit.run()
        return edit.is_valid

    @require_class(PlannedItem, True)
    def move_planned_item(self, planned_item, index):
        """Move planned item to different index in list.

        Args:
            planned_item (PlannedItem): planned item to remove.
            index (int): index to move to.

        Returns:
            (bool): whether or not edit was successful.
        """
        edit = MovePlannedItemEdit(planned_item, index)
        if edit.is_valid:
            edit.run()
        return edit.is_valid

    @require_class(PlannedItem, True)
    def modify_planned_item(
            self,
            planned_item,
            calendar_period=None,
            tree_item=None,
            size=None,
            importance=None):
        """Remove planned item from calendar.

        Args:
            planned_item (PlannedItem): planned item to remove.
            calendar_period (BaseCalendarPeriod or None): calendar period
                item is planned over.
            tree_item (BaseTreeItem or None): the task that this item
                represents.
            size (PlannedItemSize or None): size of item.
            importance (PlannedItemImportance or None): importance of item.

        Returns:
            (bool): whether or not edit was successful.
        """
        attr_dict = {
            planned_item._calendar_period: calendar_period,
            planned_item._tree_item: tree_item,
            planned_item._size: size,
            planned_item._importance: importance,
        }
        attr_dict = {
            attr: value
            for attr, value in attr_dict.items() if value is not None
        }
        edit = ModifyPlannedItemEdit(planned_item, attr_dict)
        if edit.is_valid:
            edit.run()
        return edit.is_valid

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
        edit = SortPlannedItemsEdit(calendar_period, key=key, reverse=reverse)
        if edit.is_valid:
            edit.run()
        return edit.is_valid
