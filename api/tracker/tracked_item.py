"""Tracked item class to wrap around items that are tracked."""

from scheduler.api.enums import TrackedValueType
from scheduler.api.common.object_wrappers import (
    MutableAttribute,
    MutableHostedAttribute,
    Hosted,
)
from scheduler.api.serialization.serializable import BaseSerializable


# TODO: need to include a history dict for non-task items (can still use
# TaskHistory class, although maybe that could do with renaming?)
class TrackedItem(Hosted, BaseSerializable):
    """Tracked item class for tracked tasks or other trackables."""
    TASK_ITEM_KEY = "task_item"
    NAME_KEY = "name"
    VALUE_TYPE_KEY = "value_type"

    def __init__(self, task_item=None, name=None, value_type=None):
        """Initialize class.

        Args:
            task_item (BaseTaskItem or None): task item to track, if used.
            name (str or None): name to use for tracked item.
            value_type (TrackedItemValueType or None): value type of item.
        """
        super(TrackedItem, self).__init__()
        if task_item is None and (name is None or value_type is None):
            raise ValueError(
                "TrackedItem class must accept a task item or name and "
                "value_type args."
            )
        self._task_item = MutableHostedAttribute(task_item, "task_item")
        self._name = MutableAttribute(name, "name")
        self._value_type = MutableAttribute(value_type, "value_type")

    @property
    def task_item(self):
        """Get task item that this item tracks, if exists.

        Returns:
            (BaseTaskItem or None): tracked task, if this item is a task.
        """
        return self._task_item.value

    @property
    def name(self):
        """Get name of this item.

        Returns:
            (str): name of tracked item.
        """
        if self._name.value is not None:
            return self._name.value
        if self.task_item is not None:
            return self.task_item.name
        return ""
    
    @property
    def value_type(self):
        """Get value type of this item.

        Returns:
            (TrackedValueType): type of value this item tracks.
        """
        if self._value_type.value is not None:
            return self._value_type.value
        if self.task_item is not None:
            return self.task_item.value_type
        return TrackedValueType.STATUS

    def to_dict(self):
        """Get json compatible dictionary representation of class.

        Returns:
            (OrderedDict): dictionary representation.
        """
        json_dict = {}
        if self.task_item is not None:
            json_dict[self.TASK_ITEM_KEY] = self.task_item.path
        if self._name.value is not None:
            json_dict[self.NAME_KEY] = self._name.value
        if self._value_type.value is not None:
            json_dict[self.VALUE_TYPE_KEY] = self._value_type.value
        return json_dict

    @classmethod
    def from_dict(cls, json_dict, task_root):
        """Initialise class from dictionary representation.

        The json_dict is expected to be structured as described in the to_dict
        docstring.

        Args:
            json_dict (OrderedDict): dictionary representation.
            task_root (TaskRoot): task root item, used to get linked task.

        Returns:
            (TrackedItem): tracked item for given dict.
        """
        task = json_dict.get(cls.TASK_ITEM_KEY)
        if task is not None:
            task = task_root.get_item_at_path(task, search_archive=True)
        name = json_dict.get(cls.NAME_KEY)
        value_type = TrackedValueType.from_string(
            json_dict.get(cls.VALUE_TYPE_KEY)
        )
        return cls(task_item=task, name=name, value_type=value_type)
