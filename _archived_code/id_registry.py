### ARCHIVED ###

 """Global id registry used for generating ids and storing objects by id."""

import weakref


_GLOBAL_COUNTER = 1
ID_REGISTRY = {}


class IdError(Exception):
    """Exception class for all id-related errors."""


class Id(int):
    "Wrapper around int for id values."
    def __init__(self):
        """Initialize id with new unique value."""
        super(Id, self).__init__(_GLOBAL_COUNTER)
        _GLOBAL_COUNTER += 1


def generate_id(object):
    """Generate an id for the given object, and add the object to the reigstry.

    Note that we use weakref to ensure objects are no longer accessible from
    the registry once they've been deleted. Hence the object must be one that
    we can create a weak reference to (integer, string etc. types aren't
    allowed)

    Args:
        object (variant): object to generate id for.

    Returns:
        (Id): generated id.
    """
    id = Id()
    if id in ID_REGISTRY:
        # in theory this can't happen, just making sure
        raise IdError("Id registry already contains id {0}".format(id))
    if object in ID_REGISTRY.values():
        raise IdError(
            "Object {0} already has a registered id.".format(str(object))
        )
    ID_REGISTRY[id] = weakref.proxy(object)
    return id


def override_id(id, object):
    """Assign object the given id in the registry.

    This is intended to indicate that the new object has replaced the old
    one at that id. Note that this is done at the client's risk as it means
    deleting another object from the registry, and should only be used when
    the old object is not being used anymore.

    We can only do this if the  id is lower than the global counter, otherwise
    it may conflict with some later id we assign.

    Args:
        id (Id): id to replace.
        object (variant): object to give that id.
    """
    if id >= _GLOBAL_COUNTER:
        raise IdError(
            "Id {0} is reserved for later registration and can't be assigned."
        )
    ID_REGISTRY[id] = weakref.proxy(object)


def get_object_by_id(id):
    """Get object registered under given id.

    Args:
        id (Id): id to check for.

    Returns
        (variant or None): object registered at that id, if one exists.
    """
    try:
        return ID_REGISTRY.get(id, None)
    except ReferenceError:
        del ID_REGISTRY[id]
        return None


def get_object_id(object):
    """Get id of object.

    Args:
        object (variant): object to search for.

    Returns:
        (Id or None): id of object, if it exists.
    """
    for id, obj in list(ID_REGISTRY.items()):
        try:
            if obj is object:
                return id
        except ReferenceError:
            del ID_REGISTRY[id]
            continue
    return None
