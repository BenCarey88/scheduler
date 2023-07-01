"""Base class for scheduled items and planned items to inherit from."""

from collections import OrderedDict
from functools import partial

from scheduler.api.common.object_wrappers import (
    Hosted,
    HostedDataDict,
    HostedDataList,
    MutableAttribute,
    MutableHostedAttribute
)
from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType
)
from scheduler.api import constants
from scheduler.api.enums import ItemStatus, ItemUpdatePolicy
from scheduler.api.utils import fallback_value


class BaseCalendarItem(Hosted, NestedSerializable):
    """Base class for scheduled or planned items."""
    _SAVE_TYPE = SaveType.NESTED

    CHILDREN_KEY = "children"
    TREE_ITEM_KEY = "tree_item"
    STATUS_KEY = "status"
    TASK_UPDATE_POLICY_KEY = "task_update_policy"
    ID_KEY = "id"

    _SERIALIZE_TREE_ITEM = True

    def __init__(
            self,
            calendar,
            tree_item=None,
            status=None,
            task_update_policy=None):
        """Initialize class.

        Args:
            calendar (Calendar): the calendar object.
            tree_item (BaseTaskItem or None): tree item to associate, if used.
            status (ItemStatus or None): status of item, if given.
            task_update_policy (ItemUpdatePolicy or None): update policy for
                linked task.
        """
        super(BaseCalendarItem, self).__init__()
        self._calendar = calendar
        self._tree_item = MutableHostedAttribute(
            tree_item,
            "tree_item",
            pairing_id=self._get_tree_item_pairing_id(),
            parent=self,
            driver=True,
        )
        self._status = MutableAttribute(
            fallback_value(status, ItemStatus.UNSTARTED),
            "status",
        )
        self._status_from_children = MutableAttribute(
            ItemStatus.UNSTARTED,
            "status_from_children",
        )
        self._task_update_policy = MutableAttribute(
            task_update_policy or ItemUpdatePolicy.IN_PROGRESS,
            "task_update_policy",
        )
        self._from_children_update_policy = MutableAttribute(
            ItemUpdatePolicy.IN_PROGRESS,
            "from_children_update_policy",
        )
        self._children = HostedDataList(
            pairing_id=constants.CALENDAR_ITEM_PARENT_CHILD_PAIRING,
            parent=self,
            driver=True,
        )
        self._parents = HostedDataList(
            pairing_id=constants.CALENDAR_ITEM_PARENT_CHILD_PAIRING,
            parent=self,
            driven=True,
        )
        self._influencers = HostedDataDict()
        self._is_planned_item = False
        self._is_scheduled_item = False
        self._id = None

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): the calendar object.
        """
        return self._calendar

    @property
    def tree_item(self):
        """Get task this item is planning.

        Returns:
            (BaseTaskItem): task that this item is using.
        """
        return self._tree_item.value

    @property
    def status(self):
        """Get status of item.

        Returns:
            (ItemStatus): status of item.
        """
        return max(self._status.value, self._status_from_children.value)
        # TODO: just noting this here so I don't forget. There's a very
        # minor issue with this setup in that the _status value no longer
        # always accurately represents the status value. This means that
        # when we edit planned items' or scheduled items' statuses and
        # consequently influence the associated task, the influenced value
        # will be dependent on the _status and not the status, 
        # so for eg.
        # if we complete a child of an item and hence the status of the item
        # is in_progess but then we manually change its _status to unstarted,
        # its status property will still be in_progress but the task will be
        # influenced as unstarted. This shouldn't be an issue in most cases
        # because the child item should still be influencing the task as
        # in_progress but it's slightly inaccurate all the same.
        #
        # it also means that edits don't propagate through, ie. if we update
        # status of child and that updates the parent to complete, this won't
        # influence the task from the parent. Again, this is only an issue
        # if the child has a different ItemUpdatePolicy to the parent, but
        # it does still lead to some potential confusion.
        #
        # If do decide it's an issue, we can fix it with some logic in
        # the _get_task_history_edits function to ensure we compare against
        # the new _status_from_children value as well.

    @property
    def task_update_policy(self):
        """Get update policy for linked tasks.

        Returns:
            (ItemUpdatePolicy): update policy for linked tasks.
        """
        return self._task_update_policy.value

    @property
    def from_children_update_policy(self):
        """Get update policy for update from child items.

        Returns:
            (ItemUpdatePolicy): update policy.
        """
        return self._from_children_update_policy.value

    @property
    def is_scheduled_item(self):
        """Check if item is scheduled item.

        Returns:
            (bool): whether or not item is scheduled item.
        """
        return self._is_scheduled_item

    @property
    def is_planned_item(self):
        """Check if item is planned item.

        Returns:
            (bool): whether or not item is planned item.
        """
        return self._is_planned_item

    def is_task(self):
        """Check whether calendar item represents a task or an event.

        Returns:
            (bool): whether or not calendar item represents a task.
        """
        return True

    def get_new_status_from_children(
            self,
            child_updates=None,
            new_update_policy=None):
        """Get status that should be influenced by child items.

        This is determined by the from_children_update_policy.

        Args:
            child_updates (dict(BaseCalendarItem, ItemStatus or None)
                or None): dictionary of updates to children's statuses to
                consider before updating. This dict can also contain new
                children that have not yet been added to this item's child
                list, and can indicate that a child will be removed with
                a value of None.
            new_update_policy (ItemUpdatePolicy or None): new update poicy
                to use, if given.

        Returns:
            (ItemStatus or None): new status, if it requires updating from
                prev status. For now, we only update if the status is more
                complete than a previous status.
        """
        child_updates = child_updates or {}
        statuses = [
            child_updates.get(child, child.status)
            for child in self._children
        ]
        # filter out any children that are set to None in child_updates dict
        statuses = [s for s in statuses if s is not None]
        # and add any new children from the status_updates dict
        for child, value in child_updates.items():
            if child not in self._children and value is not None:
                statuses.append(child_updates[child])

        # check against from_child update policy
        update_policy = fallback_value(
            new_update_policy,
            self.from_children_update_policy,
        )
        new_status = update_policy.get_new_status(statuses)
        if new_status != self._status_from_children.value:
            # if new status is None and status_from_children isn't, we need
            # to switch to unstarted
            return new_status or ItemStatus.UNSTARTED
        return None

    def child_index(self, planned_parent):
        """Get index of this item as a child of the given parent.

        Args:
            planned_parent (PlannedItem): planned item to check against.

        Returns:
            (int or None): index, if found.
        """
        container = planned_parent._children(self)
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
        container = planned_child._parents(self)
        if container is None:
            return None
        try:
            return container.index(self)
        except ValueError:
            return None

    def _update_status_from_children(self):
        """Update status from children.

        This should be called only as part of an edit, whenever this item's
        children are updated in some way that will affect it, or its update
        policy is updated.
        """
        status = self.get_new_status_from_children()
        if status is not None and status != self._status_from_children.value:
            self._status_from_children.set_value(status)

    def _get_tree_item_pairing_id(self):
        """Get the id for pairing the tree item in the pairing framework.

        This is used so that subclasses can reimpliment it to return None,
        allowing them to opt out of the pairing framework for tree items.

        Returns:
            (str or None): tree item pairing id, if found.
        """
        return constants.CALENDAR_ITEM_TREE_PAIRING

    # TODO: I think there's a problem here with autosaves: the assumption
    # with this _get_id method (and same for the ones in scheduled item class)
    # was that it will only be called once, as the program is being closed,
    # but because of autosaves, this isn't true. This just means the id name
    # may be dodgy, but everything else should work afaik.
    # To fix, I think we need to check if item currently exists in registry
    # rather than check if self._id is set, and then we can make autosaves
    # and saves both clear the id registry after each cache.
    # TODO: add this to serialization class
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
        raise NotImplementedError("_get_id must be implemented in subclasses")

    def _add_child(self, calendar_item):
        """Add child (to be used during deserialization).

        Args:
            calendar_item (BaseCalendarItem): planned item or scheduled item
                to associate as child of this item.
        """
        if calendar_item not in self._children:
            self._children.append(calendar_item)

    @classmethod
    def from_dict(cls, dict_repr, calendar, *init_args, **init_kwargs):
        """Initialize class from dict representation.

        This implements the base functionality:
        - set the status
        - set the tree item
        - activate the instance
        - add children (and hence parents, through the pairing framework)
        - register in item_registry

        Args:
            dict_repr (dict): dictionary representing class.
            calendar 
        """
        status = dict_repr.get(cls.STATUS_KEY)
        tree_item = calendar.task_root.get_item_at_path(
            dict_repr.get(cls.TREE_ITEM_KEY),
            search_archive=True,
        )
        task_update_policy = dict_repr.get(cls.TASK_UPDATE_POLICY_KEY)
        if task_update_policy is not None:
            task_update_policy = ItemUpdatePolicy(task_update_policy)
        class_instance = cls(
            calendar,
            *init_args,
            tree_item=tree_item,
            status=status,
            task_update_policy=task_update_policy,
            **init_kwargs,
        )
        class_instance._activate()

        for item_id in dict_repr.get(cls.CHILDREN_KEY, []):
            item_registry.register_callback(
                item_id,
                class_instance._add_child,
            )

        id = dict_repr.get(cls.ID_KEY, None)
        if id is not None:
            item_registry.register_item(id, class_instance)
        return class_instance

    def to_dict(self):
        """Return dictionary representation of class.

        This gives the base dictionary representation of the class instance,
        intended to give a starting point for dictionary representations of
        the subclasses. It includes:
            - the id
            - the status, if not unstarted
            - the tree item, if item represents a task
            - a list of all child items, if any exist

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {self.ID_KEY: self._get_id()}
        if self.status != ItemStatus.UNSTARTED:
            dict_repr[self.STATUS_KEY] = self.status
        if self._SERIALIZE_TREE_ITEM and self.is_task():
            dict_repr[self.TREE_ITEM_KEY] = self.tree_item.path
        if self._children:
            dict_repr[self.CHILDREN_KEY] = [
                child._get_id() for child in self._children
            ]
        if self.task_update_policy != ItemUpdatePolicy.IN_PROGRESS:
            dict_repr[self.TASK_UPDATE_POLICY_KEY] = self.task_update_policy
        return dict_repr
