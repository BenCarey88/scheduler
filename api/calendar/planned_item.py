"""Planned item class."""

from scheduler.api.common.object_wrappers import (
    MutableAttribute,
    MutableHostedAttribute,
)
from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
)
from scheduler.api import utils


class PlannedItemTimePeriod(object):
    """Struct to store potential time periods to plan over."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class PlannedItem(NestedSerializable):
    """Class for items in planner tab."""
    _SAVE_TYPE = SaveType.NESTED

    TREE_ITEM_KEY = "tree_item"
    TIME_PERIOD_KEY = "time_period"
    SCHEDULED_ITEMS_KEY = "scheduled_items"
    PLANNED_CHILDREN_KEY = "planned_children"
    ID_KEY = "id"

    def __init__(
            self,
            calendar,
            calendar_period,
            tree_item):
        """Initialize class.

        Args:
            calendar (Calendar): calendar object.
            calendar_period (BaseCalendarPeriod): calendar period this is
                associated to.
            tree_item (BaseTreeItem): the task that this item represents.

        Attrs:
            _planned_children (PlannedItem): associated items planned for
                shorter time periods. Generally these will be other instances
                of the same tree item or of its children.
            _scheduled_items (ScheduledItem): associated scheduled items for
                this planned item. In general, this should normally be blank
                for anything except a day planned item - the expectation is
                that if you plan an item for over a week, say, then you would
                add a day planned child item which is associated to the
                scheduled item. We don't need to be rigid on this however.
        """
        self._calendar = calendar
        self._calendar_period = MutableAttribute(
            calendar_period,
            "calendar_period"
        )
        self._tree_item = MutableHostedAttribute(tree_item, "tree_item")
        self._planned_children = []
        self._scheduled_items = []
        self._id = None

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): the calendar object.
        """
        return self._calendar

    @property
    def calendar_period(self):
        """Get calendar period that item is planned for.

        Returns:
            (BaseCalendarPeriod): period that item is planned for.
        """
        return self._calendar_period.value

    @property
    def time_period(self):
        """Get time period type that item is planned for.

        Returns:
            (PlannedItemTimePeriod): period type item is planned for.
        """
        return self.calendar_period.get_time_period_type()

    @property
    def tree_item(self):
        """Get task this item is planning.

        Returns:
            (BaseTreeItem): task that this item is using.
        """
        return self._tree_item.value

    @property
    def name(self):
        """Get name of item.

        Returns:
            (str): name of item.
        """
        return self.tree_item.name

    @property
    def tree_path(self):
        """Get path of tree item.

        Returns:
            (str): path of tree item.
        """
        return self.tree_item.path

    @property
    def scheduled_items(self):
        """Get scheduled items associated to this one.

        Returns:
            (list(BaseScheduledItem)): associated scheduled items.
        """
        return [item.value for item in self._scheduled_items]

    @property
    def planned_children(self):
        """Get child items associated to this one.

        Returns:
            (list(PlannedItem)): associated child items.
        """
        return self._planned_children

    def get_item_container(self, calendar_period=None):
        """Get the dict that this item should be contained in.

        Args:
            calendar_period (BaseCalendarPeriod or None): calendar period
                to query at. If None, use self.calendar_period.

        Returns:
            (list): list that planned item should be contained in.
        """
        calendar_period = utils.fallback_value(
            calendar_period,
            self.calendar_period
        )
        return self.calendar_period.get_planned_items_container()

    def index(self):
        """Get index of item in its container.

        Returns:
            (int or None): index of item, if found.
        """
        container = self.get_item_container()
        if container is None:
            return None
        try:
            return container.index(self)
        except ValueError:
            return None

    def _add_scheduled_item(self, scheduled_item):
        """Add scheduled item (to be used during deserialization).

        Args:
            scheduled_item (BaseScheduledItem): scheduled item to associate
                to this planned item.
        """
        if scheduled_item not in self.scheduled_items:
            self._scheduled_items.append(
                MutableHostedAttribute(scheduled_item)
            )

    def _add_planned_child(self, planned_item):
        """Add planned item child (to be used during deserialization).

        Args:
            planned_item (PlannedItem): planned item to associate as child
                of this planned item.
        """
        if planned_item not in self._planned_children:
            self._planned_children.append(planned_item)

    def _get_id(self):
        """Generate unique id for object.

        This should be used only during the serialization process, so that
        the data used for the id string is up to date. Note that once this
        is run the id string is fixed, allowing it to be referenced by other
        classes during serialization (see the item_registry module for
        more information on how this is done).

        Returns:
            (str): unique id.
        """
        if self._id is None:
            self._id = item_registry.generate_unique_id(self.name)
        return self._id

    @classmethod
    def from_dict(cls, dict_repr, calendar, calendar_period):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar object.
            calendar_period (BaseCalendarPeriod): the calendar period
                this is in.

        Returns:
            (PlannedItem): planned item.
        """
        tree_item = calendar.task_root.get_item_at_path(
            dict_repr.get(cls.TREE_ITEM_KEY)
        )
        planned_item = cls(
            calendar,
            calendar_period,
            tree_item,
        )

        for scheduled_item_id in dict_repr.get(cls.SCHEDULED_ITEMS_KEY, []):
            item_registry.register_callback(
                scheduled_item_id,
                planned_item._add_scheduled_item
            )
        for planned_item_id in dict_repr.get(cls.PLANNED_CHILDREN_KEY, []):
            item_registry.register_callback(
                planned_item_id,
                planned_item._add_planned_child
            )
        return planned_item

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {
            self.TIME_PERIOD_KEY: self.time_period,
            self.TREE_ITEM_KEY: self.tree_item.path,
            self.ID_KEY: self._get_id(),
        }
        if self._scheduled_items:
            dict_repr[self.SCHEDULED_ITEMS_KEY] = [
                scheduled_item._get_id()
                for scheduled_item in self.scheduled_items
            ]
        if self._planned_children:
            dict_repr[self.PLANNED_CHILDREN_KEY] = [
                planned_item._get_id()
                for planned_item in self.planned_children
            ]
        return dict_repr
