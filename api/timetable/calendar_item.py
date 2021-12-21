"""Calendar item class."""

from api.common.date_time import DateTime
from scheduler.api.common.serializable import SaveType, Serializable
from scheduler.api.tree.task import Task


class CalendarItemType():
    """Struct defining types of calendar items."""
    TASK = "task"
    EVENT = "event"


class CalendarItem(Serializable):
    """Calendar item class representing a scheduled task or event."""
    _SAVE_TYPE = SaveType.NESTED

    START_KEY = "start"
    END_KEY = "end"
    TYPE_KEY = "type"
    TREE_ITEM_KEY = "tree_item"
    NAME_KEY = "name"
    CATEGORY_KEY = "category"

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
        self._event_category = event_category or ""
        self._event_name = event_name or ""

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
            return self._event_category

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
            return self._event_name

    def _change_time(self, new_start_datetime, new_end_datetime):
        """Change start time and end time

        Args:
            new_start_datetime (DateTime): new start datetime.
            new_end_datettime (DateTime): new end datetime.
        """
        self._start_datetime = new_start_datetime
        self._end_datetime = new_end_datetime

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {
            self.START_KEY: self._start_datetime.string(),
            self.END_KEY: self._end_datetime.string(),
            self.TYPE_KEY: self._type,
        }
        if self.type == CalendarItemType.TASK:
            dict_repr[self.TREE_ITEM_KEY] = self._tree_item.path
        else:
            dict_repr[self.CATEGORY_KEY] = self._event_category
            dict_repr[self.NAME_KEY] = self._event_name
        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.

        Returns:
            (CalendarItem or None): calendar item, or None if can't be
                initialised.
        """
        start = dict_repr.get(cls.START_KEY)
        end = dict_repr.get(cls.END_KEY)
        type_ = dict_repr.get(cls.TYPE_KEY)
        if not (start and end and type_):
            return None
        tree_item = dict_repr.get(cls.TREE_ITEM_KEY)
        category = dict_repr.get(cls.CATEGORY_KEY)
        name = dict_repr.get(cls.NAME_KEY)

        return cls(
            start,
            end,
            type_,
            tree_item,
            category,
            name
        )
