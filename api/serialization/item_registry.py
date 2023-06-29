"""Registry to store items by id during serialization and deserialization."""


class ItemRegistryError(Exception):
    """Item registry exception class."""


class ItemCallback(object):
    """Struct defining a callback for an item, and the ids it relies on."""
    def __init__(self, item_registry, id_, callback, required_ids, order):
        """Initialise object.

        Args:
            item_registry (ItemRegistry): the item registry object.
            id (str): id of item that callback gets run on.
            callback (function): function to run on item.
            required_ids (list(str)): list of ids of other items that
                must be registered before this callback can be run.
            order (int or None): ordering compared to other callbacks
                with the same id.
        """
        self._item_registry = item_registry
        self._id = id_
        self._callback = callback
        self._additional_ids = required_ids
        self._has_been_run = False
        self.order = order

    def run(self):
        """Run callback on item."""
        if self._has_been_run:
            # we should never get to this point as the callback should
            # only successfully run once when the last id has been
            # registered
            raise ItemRegistryError(
                "Cannot run callback twice on item {0}".format(self._id)
            )

        # first check if all additional required ids are present in registry
        for id_ in self._additional_ids[:]:
            if id_ in self._item_registry._items:
                self._additional_ids.remove(id_)
        if self._additional_ids:
            return

        # now check if item is present in registry
        item = self._item_registry._items.get(self._id)
        if item is None:
            return
        self._has_been_run = True
        return self._callback(item)


class ItemRegistry(object):
    """Registry to store items by id during deserialization.

    This allows us to use callbacks to deserialize items that depend
    on one another and whose order of deserialization is uncertain.
    """
    def __init__(self):
        """Initialize registry.

        Attributes:
            _items (dict(str, variant)): dictionary of registered items.
                These are registered during deserialization and shouldn't
                need to be touched again after that.
            _callbacks (dict(str, list(function))): dictionary of callbacks to
                run when an item of the given id is registered.
            _new_ids (list(str)): this is used to store newly generated ids
                made during serialization. It allows us to ensure all new ids
                created are unique. It's independent of the id keys in the
                _items dict, so ids can change between sessions.
        """
        self._items = {}
        self._callbacks = {}
        self._new_ids = []

    def generate_unique_id(self, base_name):
        """Generate a unique id string using the base_name.

        Args:
            base_name (str): base name of id string.

        Returns:
            (str): unique id starting with base name.
        """
        id = base_name
        suffix = 1
        while id in self._new_ids:
            id = "{0}{1}".format(base_name, str(suffix).zfill(2))
            suffix += 1
        self._new_ids.append(id)
        return id

    def register_item(self, id_, item):
        """Register item at given id.

        Raises:
            (ItemRegistryError): if id already exists.

        Args:
            id_ (str): id to register item with.
            item (variant): item to register at id.
        """
        if id_ in self._items.keys():
            # TODO: need better way to handle serialization errors, tool
            # shouldn't crash if code is saved dodgily
            # Maybe keep this error though and just have some catches in
            # the nested serialization class so can crash but also specify
            # where the dodgy line is in the saved files?
            raise ItemRegistryError(
                "Item with id {0} already exists in registry".format(id_)
            )
        self._items[id_] = item
        for callback in self._callbacks.get(id_, []):
            callback.run()
        # TODO: we could delete the callbacks from the dict now they've run

    def _add_callback_at_id(self, id_, callback):
        """Helper method to add callback at given id in correct order.

        Args:
            id_ (str): id to add callback at.
            callback (ItemCallback): callback to add
        """
        callbacks_list = self._callbacks.setdefault(id_, [])
        if callback.order is not None:
            for i, c in enumerate(callbacks_list):
                if c.order is not None and c.order > callback.order:
                    callbacks_list[i] = callback
                    return
        callbacks_list.append(callback)

    def register_callback(
            self,
            main_id,
            callback,
            required_ids=None,
            order=None):
        """Register callback to be run when given id is registered.

        Args:
            main_id (str): id of item callback will be run on.
            callback (function): function to run on registration. This
                must accept a single input which is the item.
            required_ids (iterable or None): if given, this is a list of
                other ids that must be registered before this callback
                can be run.
            order (int or None): ordering compared to other callbacks with
                the same id.
        """
        required_ids = (required_ids or [])[:]
        if main_id in required_ids:
            # remove main id to ensure we treat it separately
            required_ids.remove(main_id)
        for id_ in required_ids[:]:
            if id_ in self._items:
                required_ids.remove(id_)
        callback = ItemCallback(self, main_id, callback, required_ids, order)

        for id_ in required_ids:
            self._add_callback_at_id(id_, callback)
        if main_id in self._items:
            if not required_ids:
                callback.run()
        else:
            self._add_callback_at_id(main_id, callback)

    def clear(self):
        """Clear registry, for use with a new project."""
        self._items = {}
        self._callbacks = {}


ITEM_REGISTRY = ItemRegistry()


def generate_unique_id(base_name):
    """Generate a unique id string using the base_name as a start point.

    Args:
        base_name (str): base name of id string.

    Returns:
        (str): unique id starting with base name.
    """
    return ITEM_REGISTRY.generate_unique_id(base_name)


def register_item(id_, item):
    """Register item at given id.

    Raises:
        (ItemRegistryError): if id already exists.

    Args:
        id_ (str): id to register item with.
        item (variant): item to register at id.
    """
    ITEM_REGISTRY.register_item(id_, item)


def register_callback(id_, callback, required_ids=None, order=None):
    """Register callback to be run when given id is registered.

    Args:
        id (str): id to trigger callback.
        callback (function): function to run on registration. This must
            accept a single input which is the item.
        required_ids (iterable or None): if given, this is a list of other
            ids that must be registered before this callback can be run.
        order (int or None): ordering compared to other callbacks with the
            same id.
    """
    ITEM_REGISTRY.register_callback(id_, callback, required_ids)


def clear_registry():
    """Clear registry, for use with a new project."""
    ITEM_REGISTRY.clear()
