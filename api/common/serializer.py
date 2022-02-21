"""Framework for serializing/deserialing various types."""

from collections import OrderedDict

from scheduler.api.tree._base_tree_item import BaseTreeItem
from scheduler.api.common.date_time import BaseDateTimeWrapper, TimeDelta

from ._serializer import (
    SerializerError,
    BaseSerializer,
    SerializableSerializer,
    DateTimeSerializer,
    TreeSerializer
)
from .serializable import BaseSerializable


class SerializableValue(object):
    """Struct to store an object along with the way we should serialize it."""
    SERIALIZER_MARKER = "__SERIALIZER__: "

    def __init__(self, value, serializer=None, *args, **kwargs):
        """Initialize serializable obj.

        Args:
            value (variant): the object we're storing.
            serializer (BaseSerializable or None): the way to serialize the
                object - if None, we use the default serializer for the value
                type.
            args (list): args to pass to default serializer init.
            kwargs (dict): kwargs to pass to default serializer init.
        """
        self.value = value
        self.serializer = serializer or default_serializer(
            value,
            *args,
            **kwargs
        )

    @staticmethod
    def serializer_from_string(string, *args, **kwargs):
        """Get serializer from string.

        Args:
            string (str): serialized serializer.
            args (list): args to pass to serializer init.
            kwargs (dict): kwargs to pass to serializer init.

        Returns:
            (BaseSerializer): the serializer.
        """
        serializers = [
            BaseSerializer,
            SerializableSerializer,
            DateTimeSerializer,
            TreeSerializer,
        ]
        for serializer in serializers:
            if string == serializer.__name__:
                return serializer(*args, **kwargs)
        raise SerializerError(
            "Cannot find serializer of type {0}".format(string)
        )

    def serialize(self):
        """Serialize class instance as tuple, or as single value.

        Returns:
            tuple(variant, str) or variant: tuple containing object and
                serializer, if a serializer is used, else just the value.
        """
        if self.serializer is None or self.serializer == BaseSerializer:
            return self.value
        return (
            self.serializer.serialize(self.value),
            "{0}{1}".format(self.SERIALIZER_MARKER, self.serializer.string())
        )

    @classmethod
    def deserialize(cls, json_obj, *args, **kwargs):
        """Deserialize class instance from json compatible value.

        Args:
            json_obj (tuple(variant, str) or variant): serialized item. If
                it's a 2-tuple with the second value a string starting with
                SERIALIZER_MARKER, we use that string to get the serializer.
                Otherwise, we assume no serializer is needed, and the json_obj
                represents the whole value.
            args (list): args to pass to serializer init.
            kwargs (dict): kwargs to pass to serializer init.

        Returns:
            (SerializableValue): class instance.
        """
        if (not isinstance(json_obj, tuple)
                or len(json_obj != 2)
                or not isinstance(json_obj[1], str)
                or not json_obj[1].startswith(cls.SERIALIZER_MARKER)):
            return cls(json_obj)
        serializer_string = json_obj[1][len(cls.SERIALIZER_MARKER):]
        serializer = cls.serializer_from_string(
            serializer_string,
            *args,
            **kwargs
        )
        value = serializer.deserialize(json_obj[0])
        return cls(value, serializer)


#TODO: put all the below in the SerializableValue class?
"""Default serializers to use with each type.

Note that this is not always the serialization we'll want to use; for
example, a tree item is also a serializable and when serializing the whole
task tree we effectively use the SerializableSerializer for it. But by
default, we standardly will use these mappings.

Note also that using an OrderedDict is necessary so that any subclasses
are placed above their parent classes, ensuring that we find the subclass
first.
"""
TYPE_MAPPINGS = OrderedDict(
    (BaseSerializer, (str, float, int, tuple, list, dict)),
    (DateTimeSerializer, (BaseDateTimeWrapper, TimeDelta)),
    (TreeSerializer, (BaseTreeItem)),
    # (SerializableSerializer, (BaseSerializable)),  <- no use cases afaik
)


def serializer_from_type(type_, *args, **kwargs):
    """Get default serializer for given type.

    Args:
        type_ (type): type to get serializer for.
        args (list): args to pass to serializer init.
        kwargs (dict): kwargs to pass to serializer init.

    Returns:
        (BaseSerializer): the default serializer for that type.
    """
    for serializer, type_tuple in TYPE_MAPPINGS.values():
        for base_type in type_tuple:
            if issubclass(type_, base_type):
                return serializer(*args, **kwargs)
    return BaseSerializer()


def default_serializer(value, *args, **kwargs):
    """Get default serializer for given value, based on type.

    Args:
        type_ (type): type to get serializer for.
        args (list): args to pass to serializer init.
        kwargs (dict): kwargs to pass to serializer init.

    Returns:
        (BaseSerializer): the default serializer for that type.
    """
    return serializer_from_type(type(value), *args, **kwargs)


def serialize_dict(dictionary, tree_root=None):
    """Serialize dictionary using default type serializers.

    Args:
        dictionary (dict): dictionary to serialize.
        tree_root (TaskRoot or None): tree root, needed for certain
            serializers.

    Returns:
        (dict): serialized dictionary, containing serialized SerializableValue
            objects for each object that didn't use the BaseSerializer.
    """
    return_dict = type(dictionary)()
    for key, value in dictionary.items():
        key = SerializableValue(key, tree_root=tree_root).serialize()
        if isinstance(value, dict):
            value = serialize_dict(value, tree_root=tree_root)
        elif isinstance(value, list):
            value = serialize_list(value, tree_root=tree_root)
        else:
            value = SerializableValue(value, tree_root=tree_root).serialize()
        return_dict[key] = value
    return return_dict


def serialize_list(list_, tree_root=None):
    """Serialize list using default type serializers.

    Args:
        list_ (list): list to serialize.
        tree_root (TaskRoot or None): tree root, needed for certain
            serializers.

    Returns:
        (list): serialized list, containing serialized SerializableValue
            objects for each object that didn't use the BaseSerializer.
    """
    return_list = type(list_)()
    for value in list_:
        if isinstance(value, dict):
            value = serialize_dict(value, tree_root=tree_root)
        elif isinstance(value, list):
            value = serialize_list(value, tree_root=tree_root)
        else:
            value = SerializableValue(value, tree_root=tree_root).serialize()
        return_list.append(value)
    return return_list


def deserialize_dict(dictionary, tree_root=None):
    """Deserialize dictionary using default type serializers.

    Args:
        dictionary (dict): serialized dictionary, containing serialized
            SerializableValue objects for each object that didn't use the
            BaseSerializer.
        tree_root (TaskRoot or None): tree root, needed for certain
            serializers.

    Returns:
        (dict): deserialized dictionary.
    """
    return_dict = type(dictionary)()
    for key, value in dictionary.items():
        key = SerializableValue.deserialize(key, tree_root=tree_root)
        if isinstance(value, dict):
            value = deserialize_dict(value, tree_root=tree_root)
        elif isinstance(value, list):
            value = deserialize_list(value, tree_root=tree_root)
        else:
            value = SerializableValue.deserialize(value, tree_root=tree_root)
        return_dict[key.value] = value.value
    return return_dict


def deserialize_list(list_, tree_root=None):
    """Deserialize dictionary using default type serializers.

    Args:
        list_ (list): serialized list, containing serialized SerializableValue
            objects for each object that didn't use the BaseSerializer.
        tree_root (TaskRoot or None): tree root, needed for certain
            serializers.

    Returns:
        (list): deserialized list.
    """
    return_list = type(list_)()
    for value in list_:
        if isinstance(value, dict):
            value = deserialize_dict(value, tree_root=tree_root)
        elif isinstance(value, list):
            value = deserialize_list(value, tree_root=tree_root)
        else:
            value = SerializableValue.deserialize(value, tree_root=tree_root)
        return_list.append(value.value)
    return return_list
