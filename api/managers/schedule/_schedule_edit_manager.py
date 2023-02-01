"""Schedule edit manager class to manage scheduled item edits."""

from scheduler.api.edit.schedule_edit import (
    AddScheduledItemEdit,
    AddScheduledItemAsChildEdit,
    RemoveScheduledItemEdit,
    ModifyScheduledItemEdit,
    ModifyRepeatScheduledItemEdit,
    ModifyRepeatScheduledItemInstanceEdit,
    ReplaceScheduledItemEdit,
    UpdateScheduledItemStatusEdit,
)
from scheduler.api.calendar.scheduled_item import(
    BaseScheduledItem,
    ScheduledItem,
    ScheduledItemError,
    RepeatScheduledItem,
    RepeatScheduledItemInstance,
)
from scheduler.api.constants import ItemStatus
from scheduler.api.utils import fallback_value

from .._base_manager import require_class
from ._base_schedule_manager import BaseScheduleManager


class ScheduleEditManager(BaseScheduleManager):
    """Calendar edit manager to apply edits to scheduled items."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(ScheduleEditManager, self).__init__(
            name,
            user_prefs,
            calendar,
            tree_manager,
            filterer,
        )

    def _create_scheduled_item(
            self,
            item_class,
            *args,
            planned_item=None,
            **kwargs):
        """Create scheduled item and add to calendar.

        Args:
            item_class (class): scheduled item to create.
            *args (list): args to be passed to item init.
            planned_item (PlannedItem or None): parent planned item,
                if given.
            **kwargs (dict): kwargs to be passed to item init.

        Returns:
            (bool): whether or not edit was successful.
        """
        item = item_class(*args, **kwargs)
        if planned_item is not None:
            return AddScheduledItemAsChildEdit.create_and_run(
                item,
                planned_item,
            )
        return AddScheduledItemEdit.create_and_run(item)

    def create_scheduled_item(self, *args, planned_item=None, **kwargs):
        """Create single scheduled item and add to calendar.

        Args:
            *args (list): args to be passed to ScheduledItem init.
            planned_item (PlannedItem or None): parent planned item,
                if given.
            **kwargs (dict): kwargs to be passed to ScheduledItem init.

        Returns:
            (bool): whether or not edit was successful.
        """
        return self._create_scheduled_item(
            ScheduledItem,
            *args,
            planned_item=planned_item,
            **kwargs,
        )

    def create_repeat_scheduled_item(
            self,
            *args,
            planned_item=None,
            **kwargs):
        """Create repeat scheduled item and add to calendar.

        Args:
            *args (list): args to be passed to RepeatScheduledItem init.
            planned_item (PlannedItem or None): parent planned item,
                if given.
            **kwargs (dict): kwargs to be passed to RepeatScheduledItem init.

        Returns:
            (bool): whether or not edit was successful.
        """
        return self._create_scheduled_item(
            RepeatScheduledItem,
            *args,
            planned_item=planned_item,
            **kwargs,
        )

    @require_class(BaseScheduledItem, True)
    def remove_scheduled_item(self, scheduled_item):
        """Remove scheduled item from calendar.

        Args:
            scheduled_item (BaseScheduledItem): scheduled item to remove.

        Returns:
            (bool): whether or not edit was successful.
        """
        return RemoveScheduledItemEdit.create_and_run(scheduled_item)

    @require_class((ScheduledItem, RepeatScheduledItem), raise_error=True)
    def modify_scheduled_item(
            self,
            scheduled_item,
            is_repeating,
            date=None,
            start_time=None,
            end_time=None,
            repeat_pattern=None,
            item_type=None,
            tree_item=None,
            event_category=None,
            event_name=None,
            is_background=None):
        """Modify scheduled item.

        Args:
            scheduled_item (BaseScheduledItem): item to edit.
            is_repeating (bool): whether or not to make this a repeating item.
            date (Date or None): new date.
            start_time (DateTime or None): new start date time.
            end_time (DateTime or None): new end date time.
            repeat_pattern (RepeatPattern or None): new repeat pattern.
            item_type (ScheduledItemType or None): new type.
            tree_item (BaseTaskItem or None): new tree item.
            event_category (str or None): new category name.
            event_name (str or None): new event name.
            is_background (bool or None): new background value.

        Returns:
            (bool): whether or not edit was successful.
        """
        if is_repeating == isinstance(scheduled_item, RepeatScheduledItem):
            # no class change needed, use ModifyScheduledItemEdit
            attr_dict = {
                scheduled_item._date: date,
                scheduled_item._start_time: start_time,
                scheduled_item._end_time: end_time,
                scheduled_item._repeat_pattern: repeat_pattern,
                scheduled_item._type: item_type,
                scheduled_item._tree_item: tree_item,
                scheduled_item._event_category: event_category,
                scheduled_item._event_name: event_name,
                scheduled_item._is_background: is_background,
            }
            attr_dict = {
                attr: value
                for attr, value in attr_dict.items() if value is not None
            }
            edit_class = {
                ScheduledItem: ModifyScheduledItemEdit,
                RepeatScheduledItem: ModifyRepeatScheduledItemEdit,
            }.get(type(scheduled_item))
            if edit_class is None:
                raise ScheduledItemError(
                    "Cannot modify scheduled item of type {0}".format(
                        scheduled_item.__class__.__name__
                    )
                )
            new_scheduled_item = scheduled_item
            return edit_class.create_and_run(scheduled_item, attr_dict)

        # otherwise a class change is needed, use ReplaceScheduledItemEdit
        date = fallback_value(date, scheduled_item.date)
        start_time = fallback_value(start_time, scheduled_item.start_time)
        end_time = fallback_value(end_time, scheduled_item.end_time)
        repeat_pattern = fallback_value(
            repeat_pattern,
            scheduled_item.repeat_pattern
        )
        item_type = fallback_value(item_type, scheduled_item.type)
        tree_item = fallback_value(tree_item, scheduled_item.tree_item)
        event_category = fallback_value(
            event_category,
            scheduled_item.category
        )
        event_name = fallback_value(event_name, scheduled_item.name)
        is_background = fallback_value(
            is_background,
            scheduled_item.is_background
        )

        if is_repeating:
            new_scheduled_item = RepeatScheduledItem(
                self._calendar,
                start_time,
                end_time,
                repeat_pattern,
                item_type=item_type,
                tree_item=tree_item,
                event_category=event_category,
                event_name=event_name,
                is_background=is_background,
            )
        else:
            new_scheduled_item = ScheduledItem(
                self._calendar,
                start_time,
                end_time,
                date,
                item_type=item_type,
                tree_item=tree_item,
                event_category=event_category,
                event_name=event_name,
                is_background=is_background,
                repeat_pattern=repeat_pattern,
            )
        return ReplaceScheduledItemEdit.create_and_run(
            scheduled_item,
            new_scheduled_item,
        )

    @require_class((ScheduledItem, RepeatScheduledItemInstance), True)
    def move_scheduled_item(
            self,
            scheduled_item,
            date=None,
            start_time=None,
            end_time=None):
        """Move scheduled item to new start and end datetimes.

        Args:
            scheduled_item (BaseScheduledItem): item to edit.
            date (Date or None): new date.
            start_time (DateTime or None): new start date time.
            end_time (DateTime or None): new end date time.

        Returns:
            (bool): whether or not edit was successful.
        """
        attr_dict = {
            scheduled_item._date: date,
            scheduled_item._start_time: start_time,
            scheduled_item._end_time: end_time,
        }
        attr_dict = {
            attr: value
            for attr, value in attr_dict.items() if value is not None
        }
        edit_class = {
            ScheduledItem: ModifyScheduledItemEdit,
            RepeatScheduledItemInstance: ModifyRepeatScheduledItemInstanceEdit,
        }.get(type(scheduled_item))
        if edit_class is None:
            raise ScheduledItemError(
                "Cannot modify scheduled item of type {0}".format(
                    scheduled_item.__class__.__name__
                )
            )
        return edit_class.create_and_run(scheduled_item, attr_dict)

    @require_class((ScheduledItem, RepeatScheduledItemInstance), True)
    def update_check_status(self, scheduled_item, status=None):
        """Update check status of scheduled item.
        
        Args:
            scheduled_item (BaseScheduledItem): item to edit.
            status (ItemStatus or None): status to update item with. If None
                given, we calculate the next one.

        Returns:
            (bool): whether or not edit was successful.
        """
        # TODO: currently this edit could override a task that was completed
        # earlier to in_progress. We don't want to do this, but we do want to
        # mark the influencer down in case that earlier completion is later
        # removed.
        # The problem is that we then need to change the way that the history
        # dict works out the status as it currently just propagates up from
        # the latest task. And I think we DO want the ability to override
        # a task from complete back to in_progress? Maybe we can add a
        # STATUS_OVERRIDE key to the influencer dict to tell us whether or
        # not to override earlier times, or to check against an earlier one
        if status is None:
            status = scheduled_item.status.next()
        task_item = scheduled_item.tree_item
        if task_item is not None and not self.is_task(task_item):
            # TODO: ^check if we need this - may be that this is being/can be
            # sorted in scheduled_item.get_new_task_status - if so, we can
            # move the is_task method back to base_tree_manager
            task_item = None
        return UpdateScheduledItemStatusEdit.create_and_run(
            scheduled_item,
            scheduled_item.end_datetime,
            status,
            task_item=task_item,
        )
        # TODO: find a way to trigger a task ui update after this too?
        # so that this still updates properly if we're in the task tab
