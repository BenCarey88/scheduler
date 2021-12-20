"""Calendar item class."""

from scheduler.api.common.serializable import SaveType, Serializable
from scheduler.api.tree.task import Task


class CalendarItemType():
    """Struct defining types of calendar items."""
    TASK = "task"
    EVENT = "event"


class CalendarItem(Serializable):
    """Calendar item class representing a scheduled task or event."""

    __SAVE_TYPE__ = SaveType.File

    def __init__(
            self,
            start,
            end,
            item_type=CalendarItemType.TASK,
            tree_item=None,
            event_category=None,
            event_name=None):
        """Initialise item.

        Args:
            start (DateTime): start date time.
            end (DateTime): end date time.
            item_type (CalendarItemType): type of scheduled item.
            tree_item (BaseTreeItem or None): tree item representing task,
                if item_type is task.
            event_category (str or None): name to be used for category of item,
                if item_type is event.
            event_name (str or None): name of event, if item_type is event.
        """
        self._start_datetime = start
        self._end_datetime = end
        self._type = item_type
        self._tree_item = tree_item
        self._event_category = event_category
        self._event_name = event_name

    @property
    def start_time(self):
        """Get start time.

        Returns:
            (datetime.time): start time.
        """
        return self._start_datetime.time()

    @property
    def end_time(self):
        """Get end time.

        Returns:
            (datetime.time): end time.
        """
        return self._end_datetime.time()

    # TODO: for now this assumes that the event is only on one day
    @property
    def date(self):
        """Get date of item.

        Returns:
            (DateTime): date.
        """
        return self._start_datetime

    @property
    def type(self):
        """Get type of calendar item.

        Returns:
            (CalendarItemType): item type.
        """
        return self._type

    @property
    def tree_item(self):
        """Get tree item representing task.

        Returns:
            (BaseTreeItem or None): task or task category tree item, if one
                exists.
        """
        return self._tree_item

    @property
    def category(self):
        """Get item category name.

        Returns:
            (str): name to use for item category.
        """
        if self._type == CalendarItemType.TASK:
            if isinstance(self._tree_item, Task):
                return self._tree_item.top_level_task()
            return ""
        else:
            return self._event_category or ""

    @property
    def name(self):
        """Get item name.

        Returns:
            (str): name to use for item.
        """
        if self._type == CalendarItemType.TASK:
            if self._tree_item:
                return self._tree_item.name
            return ""
        else:
            return self._event_name or ""

    def _change_time(self, new_start_time, new_end_time):
        """Change start time and end time"""

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """

    @classmethod
    def from_dict(self):
