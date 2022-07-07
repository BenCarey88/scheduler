"""Default framework for serializing/deserialing various types."""

from collections import OrderedDict

from scheduler.api.tree._base_tree_item import BaseTreeItem
from scheduler.api.common.date_time import BaseDateTimeWrapper, TimeDelta
# from scheduler.api.common.id_registry import Id, get_object_by_id

from .serializer import (
    BaseSerializer,
    DateTimeSerializer,
    NumberSerializer,
    TreeSerializer,
    # IdSerializer,
    convert_serializer_to_string,
    get_serializer_from_string,
)


class SerializableValue(object):
    """Struct to store an object along with the way we should serialize it."""
    SERIALIZER_MARKER = "<__SERIALIZER__"

    def __init__(self, value, serializer=None, as_key=False, *args, **kwargs):
        """Initialize serializable obj.

        Args:
            value (variant): the object we're storing.
            serializer (BaseSerializable or None): the way to serialize the
                object - if None, we use the default serializer for the value
                type.
            as_key (bool): if True, this value needs to be serialized as a
                dictionary key.
            args (list): args to pass to default serializer init.
            kwargs (dict): kwargs to pass to default serializer init.
        """
        self.value = value
        self.serializer = serializer or default_serializer(
            value,
            as_key,
            *args,
            **kwargs
        )
        self._as_key = as_key

    def serialize(self):
        """Serialize class instance as tuple, or as single value.

        if self._as_key is True, we serialize the item as a string. Otherwise,
        we serialize it as a list. Note that this means that all values
        intended to be used as dictionary keys in a serialized file must be

        Returns:
            (list, str or variant): serialized item. If a serializer is used,
                this is either a list containing the serialized value and then
                the serializer string, or a string consisting of the serialized
                value followed by the serializer string.
                Otherwise, it's just the value.
        """
        if type(self.serializer) == BaseSerializer:
            return self.value
        if self._as_key:
            return "{0}{1}{2}>".format(
                self.serializer.serialize(self.value),
                self.SERIALIZER_MARKER,
                convert_serializer_to_string(self.serializer)
            )
        return [
            self.serializer.serialize(self.value),
            "{0}{1}>".format(
                self.SERIALIZER_MARKER,
                convert_serializer_to_string(self.serializer)
            )
        ]

    @classmethod
    def is_serialized_serializable_value(cls, json_obj, as_key=False):
        """Check if json obj is a serialized SerializableValue class.

        Args:
            json_list (variant): serialized list object.
            as_key (bool): whether we're checking if the object is key-
                serialized (ie. serialized as a string) or list-serialized.

        Returns:
            (bool): whether or not list represents a serializable value class.
        """
        if as_key:
            return (
                isinstance(json_obj, str)
                and len(json_obj.split(cls.SERIALIZER_MARKER) ) == 2
            )
        return (
            isinstance(json_obj, list)
            and len(json_obj) == 2
            and isinstance(json_obj[1], str)
            and json_obj[1].startswith(cls.SERIALIZER_MARKER)
        )

    @classmethod
    def deserialize(cls, json_obj, as_key=False, *args, **kwargs):
        """Deserialize class instance from json compatible value.

        Args:
            json_obj (list, str or variant): serialized item. If this is a
                string containing the SERIALIZER_MARKER as a substring, or
                a list where the second item is a string containing the
                SERIALIZER_MARKER as a substring, we use this to get the
                serializer to use. Otherwise, the json_obj represents the
                entire value.
            as_key (bool): if True, the item is serialized as a string.
                Otherwise, we assume it's been serialized as a list. This flag
                should be set to True whenever we're deserializing dictionary
                keys.
            args (list): args to pass to serializer init.
            kwargs (dict): kwargs to pass to serializer init.

        Returns:
            (SerializableValue): class instance.
        """
        if as_key:
            if not isinstance(json_obj, str):
                return cls(json_obj)
            split_json_obj = json_obj.split(cls.SERIALIZER_MARKER)
            if len(split_json_obj) != 2:
                return cls(json_obj)
            value_obj = split_json_obj[0]
            serializer_string = split_json_obj[1][:-1]

        else:
            if (not cls.is_serialized_serializable_value(json_obj)):
                return cls(json_obj)
            value_obj = json_obj[0]
            serializer_string = json_obj[1][len(cls.SERIALIZER_MARKER):-1]

        serializer = get_serializer_from_string(
            serializer_string,
            *args,
            **kwargs
        )
        value = serializer.deserialize(value_obj)
        return cls(value, serializer, as_key)


#TODO: put all the below in the SerializableValue class?
"""Default serializers to use with each type.

Note that this is not always the serialization we'll want to use; for
example, a tree item is also a serializable and when serializing the whole
task tree we effectively use the SerializableSerializer for it. But by
default, we standardly will use these mappings.

Note also that using an OrderedDict is necessary so that any subclasses
are placed above their parent classes, ensuring that we find the subclass
first.

KEY_TYPE_MAPPINGS gives us additional mappings specific to dictionary keys:
for example, ints and floats can't be keys in json, so we need to convert
them to strings.
"""
TYPE_MAPPINGS = OrderedDict([
    (BaseSerializer, (str, float, int, list, dict,)),
    (DateTimeSerializer, (BaseDateTimeWrapper, TimeDelta,)),
    (TreeSerializer, (BaseTreeItem,)),
])
KEY_TYPE_MAPPINGS = OrderedDict([
    (NumberSerializer, (int, float,))
])


def serializer_from_type(type_, as_key=False, *args, **kwargs):
    """Get default serializer for given type.

    Args:
        type_ (type): type to get serializer for.
        as_key (bool): if True, use KEY_TYPE_MAPPINGS as well as
            normal type mappings.
        args (list): args to pass to serializer init.
        kwargs (dict): kwargs to pass to serializer init.

    Returns:
        (BaseSerializer): the default serializer for that type.
    """
    type_mappings = list(TYPE_MAPPINGS.items())
    if as_key:
        type_mappings = list(KEY_TYPE_MAPPINGS.items()) + list(type_mappings)
    for serializer, type_tuple in type_mappings:
        for base_type in type_tuple:
            if issubclass(type_, base_type):
                return serializer(*args, **kwargs)
    return BaseSerializer()


def default_serializer(value, as_key=False, *args, **kwargs):
    """Get default serializer for given value, based on type.

    Args:
        type_ (type): type to get serializer for.
        as_key (bool): if True, use KEY_TYPE_MAPPINGS as well as
            normal type mappings.
        args (list): args to pass to serializer init.
        kwargs (dict): kwargs to pass to serializer init.

    Returns:
        (BaseSerializer): the default serializer for that type.
    """
    return serializer_from_type(type(value), as_key, *args, **kwargs)


def serialize_dict(dictionary, tree_root=None, delete_empty_containers=False):
    """Serialize dictionary using default type serializers.

    Args:
        dictionary (dict): dictionary to serialize.
        tree_root (TaskRoot or None): tree root, needed for certain
            serializers.
        delete_empty_containers (bool): if True, we delete any empty lists or
            keys from the serialized dict.

    Returns:
        (dict): serialized dictionary, containing serialized SerializableValue
            objects for each object that didn't use the BaseSerializer.
    """
    return_dict = type(dictionary)()
    for key, value in dictionary.items():
        if key is None:
            continue
        key = SerializableValue(
            key,
            as_key=True,
            tree_root=tree_root
        ).serialize()
        if isinstance(value, dict):
            value = serialize_dict(
                value,
                tree_root=tree_root,
                delete_empty_containers=delete_empty_containers,
            )
            if delete_empty_containers and not value:
                continue
        elif isinstance(value, list):
            value = serialize_list(
                value,
                tree_root=tree_root,
                delete_empty_containers=delete_empty_containers,
            )
            if delete_empty_containers and not value:
                continue
        else:
            value = SerializableValue(value, tree_root=tree_root).serialize()
        if value is None:
            # we don't support None type serialization
            continue
        return_dict[key] = value
    return return_dict


def serialize_list(list_, tree_root=None, delete_empty_containers=False):
    """Serialize list using default type serializers.

    Args:
        list_ (list): list to serialize.
        tree_root (TaskRoot or None): tree root, needed for certain
            serializers.
        delete_empty_containers (bool): if True, we delete any empty lists or
            keys from the serialized dict.

    Returns:
        (list): serialized list, containing serialized SerializableValue
            objects for each object that didn't use the BaseSerializer.
    """
    return_list = type(list_)()
    for value in list_:
        if isinstance(value, dict):
            value = serialize_dict(
                value,
                tree_root=tree_root,
                delete_empty_containers=delete_empty_containers
            )
            if delete_empty_containers and not value:
                continue
        elif isinstance(value, list):
            value = serialize_list(
                value,
                tree_root=tree_root,
                delete_empty_containers=delete_empty_containers
            )
            if delete_empty_containers and not value:
                continue
        else:
            value = SerializableValue(value, tree_root=tree_root).serialize()
        if value is None:
            # we don't support None type serialization
            continue
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
        key = SerializableValue.deserialize(
            key,
            as_key=True,
            tree_root=tree_root
        ).value
        if isinstance(value, dict):
            value = deserialize_dict(value, tree_root=tree_root)
        elif isinstance(value, list):
            if SerializableValue.is_serialized_serializable_value(value):
                value = SerializableValue.deserialize(
                    value,
                    tree_root=tree_root
                ).value
            else:
                value = deserialize_list(value, tree_root=tree_root)
        else:
            value = SerializableValue.deserialize(
                value,
                tree_root=tree_root
            ).value
        if key is None or value is None:
            # ignore None types (eg. for tree path that no longer exists)
            continue
        return_dict[key] = value
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
            if SerializableValue.is_serialized_serializable_value(value):
                value = SerializableValue.deserialize(
                    value,
                    tree_root=tree_root
                ).value
            else:
                value = deserialize_list(value, tree_root=tree_root)
        else:
            value = SerializableValue.deserialize(
                value,
                tree_root=tree_root
            ).value
        if value is None:
            # ignore None types (eg. for tree path that no longer exists)
            continue
        return_list.append(value)
    return return_list
