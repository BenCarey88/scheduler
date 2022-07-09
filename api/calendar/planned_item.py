"""Planned item class."""

from functools import partial

from scheduler.api.common.object_wrappers import (
    Hosted,
    MutableAttribute,
    MutableHostedAttribute,
)
from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
)
from scheduler.api.utils import fallback_value, OrderedEnum


class PlannedItemTimePeriod(OrderedEnum):
    """Struct to store potential time periods to plan over."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    VALUES = [DAY, WEEK, MONTH, YEAR]


class PlannedItem(Hosted, NestedSerializable):
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
            tree_item (BaseTaskItem): the task that this item represents.

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
        super(PlannedItem, self).__init__()
        self._calendar = calendar
        self._calendar_period = MutableAttribute(
            calendar_period,
            "calendar_period"
        )
        self._tree_item = MutableHostedAttribute(tree_item, "tree_item")
        self._planned_children = {
            time_period: []
            for time_period in PlannedItemTimePeriod.VALUES
            if PlannedItemTimePeriod.is_lesser(time_period, self.time_period)
        }
        self._planned_parents = {
            time_period: []
            for time_period in PlannedItemTimePeriod.VALUES
            if PlannedItemTimePeriod.is_greater(time_period, self.time_period)
        }
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
            (BaseTaskItem): task that this item is using.
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
            (dict(PlannedItemTimePeriod, list(PlannedItem))): associated child
                items.
        """
        return {
            time_period: [child.value for child in child_list]
            for time_period, child_list in self._planned_children.items()
        }

    @property
    def planned_parents(self):
        """Get parent items associated to this one.

        Returns:
            (dict(PlannedItemTimePeriod, list(PlannedItem))): associated parent
                items.
        """
        return {
            time_period: [parent.value for parent in parent_list]
            for time_period, parent_list in self._planned_parents.items()
        }

    def get_planned_children(self, time_period):
        """Get child items associated to this one for given time period.

        Args:
            time_period (PlannedItemTimePeriod): time period to check

        Returns:
            (list(PlannedItem)): associated child items for given time period.
        """
        return [c.value for c in self._planned_children.get(time_period, [])]

    def get_planned_parents(self, time_period):
        """Get parent items associated to this one for given time period.

        Args:
            time_period (PlannedItemTimePeriod): time period to check

        Returns:
            (list(PlannedItem)): associated parent items for given time period.
        """
        return [c.value for c in self._planned_parents.get(time_period, [])]

    def get_item_container(self, calendar_period=None):
        """Get the list that this item should be contained in.

        Args:
            calendar_period (BaseCalendarPeriod or None): calendar period
                to query at. If None, use self.calendar_period.

        Returns:
            (list): list that planned item should be contained in.
        """
        calendar_period = fallback_value(
            calendar_period,
            self.calendar_period
        )
        return calendar_period.get_planned_items_container()

    def get_child_container(self, planned_child):
        """Get the container that the given child should live in.

        Args:
            planned_child (PlannedItem): child to look for.

        Returns:
            (list or None): container from this class that the child should
                live in, if exists.
        """
        return self._planned_children.get(planned_child.time_period)

    def get_parent_container(self, planned_parent):
        """Get the container that the given parent should live in.

        Args:
            planned_parent (PlannedItem): parent to look for.

        Returns:
            (list or None): container from this class that the parent should
                live in, if exists.
        """
        return self._planned_parents.get(planned_parent.time_period)

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

    def child_index(self, planned_parent):
        """Get index of this item as a child of the given parent.

        Args:
            planned_parent (PlannedItem): planned item to check against.

        Returns:
            (int or None): index, if found.
        """
        container = planned_parent.get_child_container(self)
        if container is None:
            return None
        try:
            return container.index(self)
        except ValueError:
            return None

    def parent_index(self, planned_child):
        """Get index of this item as a parent of the given child.

        Args:
            planned_parent (PlannedItem): planned item to check against.

        Returns:
            (int or None): index, if found.
        """
        container = planned_child.get_parent_container(self)
        if container is None:
            return None
        try:
            return container.index(self)
        except ValueError:
            return None

    def _add_scheduled_item(self, scheduled_item):
        """Add scheduled item (to be used during deserialization).

        This method also associates the scheduled item to this class.

        Args:
            scheduled_item (BaseScheduledItem): scheduled item to associate
                to this planned item.
        """
        if scheduled_item not in self.scheduled_items:
            self._scheduled_items.append(
                MutableHostedAttribute(scheduled_item)
            )
            PITP = PlannedItemTimePeriod
            scheduled_item_method = {
                PITP.DAY: scheduled_item._add_planned_day_item(self),
                PITP.WEEK: scheduled_item._add_planned_week_item(self),
                PITP.MONTH: scheduled_item._add_planned_month_item(self),
                PITP.YEAR: scheduled_item._add_planned_year_item(self),
            }.get(self.time_period)
            scheduled_item_method(self)

    def _add_planned_child(self, time_period, planned_item):
        """Add planned item child (to be used during deserialization).

        Args:
            time_period (PlannedItemTimePeriod): time period of child.
            planned_item (PlannedItem): planned item to associate as child
                of this planned item.
        """
        if time_period != planned_item.time_period:
            return
        child_list = self._planned_children.get(time_period)
        if child_list is not None and planned_item not in child_list:
            self._planned_children.append(
                MutableHostedAttribute(planned_item)
            )
            planned_item._planned_parents.append(
                MutableAttribute(self)
            )

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
        for tuple_ in dict_repr.get(cls.PLANNED_CHILDREN_KEY, {}).items():
            time_period, child_list = tuple_
            for scheduled_item_id in child_list:
                item_registry.register_callback(
                    scheduled_item_id,
                    partial(planned_item._add_planned_child, time_period)
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
        planned_children_dict = {}
        for time_period, child_list in self.planned_children.items():
            if child_list:
                planned_children_dict[time_period] = [
                    item._get_id() for item in child_list
                ]
        if planned_children_dict:
            dict_repr[self.PLANNED_CHILDREN_KEY] = planned_children_dict
        return dict_repr
