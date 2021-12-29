"""Calendar class containing all calendar data."""

from contextlib import contextmanager

from scheduler.api.common.date_time import DateTime
from scheduler.api.common.serializable import NestedSerializable


class Calendar(object):

    def __init__(self, task_root):
        """Initialise calendar class."""
        self.task_root = task_root
        self._years = {}

    def get_calendar_day(date):
        """Get calendar day data for given date.

        Args:
        """

    

    # @contextmanager
    # def filter_items(self, filters):
    #     """Contextmanager to filter _items list temporarily.

    #     This uses the filters defined in the filters module.

    #     Args:
    #         filters (list(BaseFilter)): types of filtering required.
    #     """
    #     _items = self._items
    #     try:
    #         for filter in filters:
    #             self._items = filter.filter_function(self._items)
    #         yield
    #     finally:
    #         self._items = _items

    def to_dict(self):
        pass

    @classmethod    
    def from_dict(cls):
        pass
