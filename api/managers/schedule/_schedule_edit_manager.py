"""Schedule edit manager class to manage scheduled item edits."""

from scheduler.api.edit.scheduler_edit import (
    AddScheduledItemEdit,
    RemoveScheduledItemEdit,
    ModifyScheduledItemEdit,
    ModifyRepeatScheduledItemEdit,
    ModifyRepeatScheduledItemInstanceEdit,
    ReplaceScheduledItemEdit,
)
from scheduler.api.calendar.scheduled_item import(
    BaseScheduledItem,
    ScheduledItem,
    ScheduledItemError,
    RepeatScheduledItem,
    RepeatScheduledItemInstance,
)
from scheduler.api.utils import fallback_value

from .._base_manager import require_class
from ._base_schedule_manager import BaseScheduleManager


class ScheduleEditManager(BaseScheduleManager):
    """Calendar edit manager to apply edits to scheduled items."""
    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            archive_calendar (Calendar): archive calendar object.
        """
        super(ScheduleEditManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
        )
        self._item_being_moved = None
        self._continuous_edit = None

    def _create_scheduled_item(self, item_class, *args, **kwargs):
        """Create scheduled item and add to calendar.

        Args:
            item_class (class): scheduled item to create
            *args (list): args to be passed to item init.
            **kwargs (dict): kwargs to be passed to item init.

        Returns:
            (ScheduledItem): newly created scheduled item.
        """
        item = item_class(*args, **kwargs)
        AddScheduledItemEdit.create_and_run(item)
        return item

    def create_scheduled_item(self, *args, **kwargs):
        """Create single scheduled item and add to calendar.

        Args:
            *args (list): args to be passed to ScheduledItem init.
            **kwargs (dict): kwargs to be passed to ScheduledItem init.

        Returns:
            (ScheduledItem): newly created scheduled item.
        """
        return self._create_scheduled_item(ScheduledItem, *args, **kwargs)

    def create_repeat_scheduled_item(self, *args, **kwargs):
        """Create repeat scheduled item and add to calendar.

        Args:
            *args (list): args to be passed to RepeatScheduledItem init.
            **kwargs (dict): kwargs to be passed to RepeatScheduledItem init.

        Returns:
            (RepeatScheduledItem): newly created scheduled item.
        """
        return self._create_scheduled_item(RepeatScheduledItem, *args, **kwargs)

    @require_class(BaseScheduledItem, True)
    def remove_scheduled_item(self, scheduled_item):
        """Remove scheduled item from calendar.

        Args:
            scheduled_item (BaseScheduledItem): scheduled item to remove.
        """
        RemoveScheduledItemEdit.create_and_run(scheduled_item)

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
            tree_item (BaseTreeItem or None): new tree item.
            event_category (str or None): new category name.
            event_name (str or None): new event name.
            is_background (bool or None): new background value.
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
        ReplaceScheduledItemEdit.create_and_run(
            scheduled_item,
            new_scheduled_item,
        )

    @require_class((ScheduledItem, RepeatScheduledItemInstance), True)
    def begin_move_item(
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
        """
        # if date is None:
        #     date = scheduled_item.date
        # if start_time is None:
        #     start_time = scheduled_item.start_time
        # if end_time is None:
        #     end_time = scheduled_item.end_time
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
        self._continuous_edit = edit_class(scheduled_item, attr_dict)
        self._item_being_moved = scheduled_item
        self._continuous_edit.begin_continuous_run()

    @require_class((ScheduledItem, RepeatScheduledItemInstance), True)
    def update_move_item(
            self,
            scheduled_item,
            date=None,
            start_time=None,
            end_time=None):
        """Update edit to move scheduled item to new start and end datetimes.

        Args:
            scheduled_item (BaseScheduledItem): item to edit.
            date (Date or None): new date.
            start_time (DateTime or None): new start date time.
            end_time (DateTime or None): new end date time.
        """
        if self._continuous_edit is None:
            # TODO: sort exception
            raise ScheduledItemError(
                "Cannot update edit when none is in progress."""
            )
        if self._item_being_moved != scheduled_item:
            raise ScheduledItemError(
                "item {0} is not currently being moved".format(
                    scheduled_item.name
                )
            )
        self._continuous_edit.update_continuous_run(date, start_time, end_time)

    @require_class((ScheduledItem, RepeatScheduledItemInstance), True)
    def end_move_item(self, scheduled_item):
        """Finish edit to move scheduled item to new start and end datetimes.

        Args:
            scheduled_item (BaseScheduledItem): item to edit.
        """
        if self._continuous_edit is None:
            # TODO: sort exception
            raise ScheduledItemError(
                "Cannot end edit when none is in progress."
            )
        if self._item_being_moved != scheduled_item:
            raise ScheduledItemError(
                "item {0} is not currently being moved".format(
                    scheduled_item.name
                )
            )
        self._continuous_edit.end_continuous_run()
