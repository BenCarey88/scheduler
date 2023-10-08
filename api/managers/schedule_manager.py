"""Schedule manager class."""

from scheduler.api.calendar.scheduled_item import(
    BaseScheduledItem,
    ScheduledItem,
    ScheduledItemError,
    ScheduledItemType,
    RepeatScheduledItem,
    RepeatScheduledItemInstance,
)
from scheduler.api.edit.schedule_edit import (
    AddScheduledItemEdit,
    RemoveScheduledItemEdit,
    ModifyScheduledItemEdit,
    ModifyRepeatScheduledItemEdit,
    ModifyRepeatScheduledItemInstanceEdit,
    ReplaceScheduledItemEdit,
)
from scheduler.api.utils import fallback_value

from ._base_manager import BaseCalendarManager, require_class


class ScheduleManager(BaseCalendarManager):
    """Schedule manager class to manage schedule edits."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(ScheduleManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
            filterer=filterer,
            name=name,
            suffix="schedule_manager",
        )

    @require_class((ScheduledItem, RepeatScheduledItemInstance), True)
    def get_item_to_modify(self, scheduled_item):
        """Get the scheduled item we can use to modify this one's attributes.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItemInstance):
                scheduled item instance that a user can select.

        Returns:
            (BaseScheduledItem): either the scheduled item, or the repeat item
                that it's an instance of, in the case of repeat scheduled item
                instances.
        """
        if isinstance(scheduled_item, ScheduledItem):
            return scheduled_item
        elif isinstance(scheduled_item, RepeatScheduledItemInstance):
            return scheduled_item.repeat_scheduled_item

    @require_class(BaseScheduledItem, True)
    def has_task_type(self, scheduled_item, strict=False):
        """Check if item is a task item.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItem): scheduled
                item to check.
            strict (bool): if True, don't include task categories.

        Returns:
            (bool): whether or not item is task item.
        """
        if not strict:
            return scheduled_item.type == ScheduledItemType.TASK
        return (
            scheduled_item.type == ScheduledItemType.TASK and
            scheduled_item.tree_item is not None and
            self._tree_manager.is_task(scheduled_item.tree_item)
        )

    @require_class(BaseScheduledItem, True)
    def has_event_type(self, scheduled_item):
        """Check if item is an event item.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItem): scheduled
                item to check.

        Returns:
            (bool): whether or not item is an event item.
        """
        return scheduled_item.type == ScheduledItemType.EVENT

    @require_class((ScheduledItem, RepeatScheduledItem), True)
    def is_repeat_item(self, scheduled_item):
        """Check if item is repeat item or repeat item instance.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItem): calendar
                item to check.

        Returns:
            (bool): whether or not item is repeat item.
        """
        return isinstance(scheduled_item, RepeatScheduledItem)

    @require_class((ScheduledItem, RepeatScheduledItem), True)
    def get_repeat_pattern(self, scheduled_item):
        """Get the repeat pattern of the scheduled item, if it's a repeat item.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItem): scheduled item
                to check.

        Returns:
            (RepeatPattern or None): repeat pattern.
        """
        if isinstance(scheduled_item, RepeatScheduledItem):
            return scheduled_item.repeat_pattern
        return None

    ### Edit Methods ###
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
        return AddScheduledItemEdit.create_and_run(item, parent=planned_item)

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
            task_update_policy=None,
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
            task_update_policy (ItemUpdatePolicy or None): new update policy.
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
                scheduled_item._task_update_policy: task_update_policy,
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
        if status is None:
            status = scheduled_item.status.next()
        edit_class = {
            ScheduledItem: ModifyScheduledItemEdit,
            RepeatScheduledItemInstance: ModifyRepeatScheduledItemInstanceEdit,
        }.get(type(scheduled_item))
        return edit_class.create_and_run(
            scheduled_item,
            {scheduled_item._status: status},
        )
        # TODO: find a way to trigger a task ui update after this too?
        # so that this still updates properly if we're in the task tab
