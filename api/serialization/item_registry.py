"""Registry to store items by id during serialization and deserialization."""


class ItemRegistryError(Exception):
    """Item registry exception class."""


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

    def register_item(self, id, item):
        """Register item at given id.

        Raises:
            (ItemRegistryError): if id already exists.

        Args:
            id (str): id to register item with.
            item (variant): item to register at id.
        """
        if id in self._items.keys():
            # TODO: need better way to handle serialization errors, tool
            # shouldn't crash if code is saved dodgily
            # Maybe keep this error though and just have some catches in
            # the nested serialization class so can crash but also specify
            # where the dodgy line is in the saved files?
            raise ItemRegistryError(
                "Item with id {0} already exists in registry".format(id)
            )
        self._items[id] = item
        for callback in self._callbacks.get(id, []):
            callback(item)

    def register_callback(self, id, callback):
        """Register callback to be run when given id is registered.

        Args:
            id (str): id to trigger callback.
            callback (function): function to run on registration. This
                must accept a single input which is the item.
        """
        item = self._items.get(id, None)
        if item is not None:
            callback(item)
        else:
            self._callbacks.setdefault(id, []).append(callback)

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


def register_item(id, item):
    """Register item at given id.

    Raises:
        (ItemRegistryError): if id already exists.

    Args:
        id (str): id to register item with.
        item (variant): item to register at id.
    """
    ITEM_REGISTRY.register_item(id, item)


def register_callback(id, callback):
    """Register callback to be run when given id is registered.

    Args:
        id (str): id to trigger callback.
        callback (function): function to run on registration. This
            must accept a single input which is the item.
    """
    ITEM_REGISTRY.register_callback(id, callback)


def clear_registry():
    """Clear registry, for use with a new project."""
    ITEM_REGISTRY.clear()
