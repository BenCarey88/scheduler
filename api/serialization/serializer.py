"""Classes to define conversion of various types to json-compatible types."""


# from scheduler.api.common.id_registry import get_object_by_id, get_object_id


class SerializerError(Exception):
    """Exception for any errors related to serializer class."""


class BaseSerializer(object):
    """Base serializer class, used for types that are already json types.

    Types:
        str, float, int, list, dict
    """
    def __init__(self, *args, **kwargs):
        """Initialise serializer to serialize given type.

        Args:
            args (list): additional args that can be passed to the serialize
                and deserialize functions.
            kwargs (dict): additional kwargs that can be passed to the
                serialize and deserialize functions.
        """
        self._serialize_args = args
        self._serialize_kwargs = kwargs

    def serialize(self, obj):
        """Serialize obj to json type.

        Args:
            obj (variant): object to serialize, must be one of the types
                listed in class docstring.

        Returns:
            (variant): json-serialized object.
        """
        return obj

    def deserialize(self, obj):
        """Deserialize obj from json type.

        Args:
            obj (variant): json type to deserialize.

        Returns:
            (variant): deserialized object, will be one of the types listed in
                class docstring.
        """
        return obj

    def string(self):
        """Serialize serializer class as string.

        Returns:
            (str): serialized serializer.
        """
        return self.__class__.__name__

    @classmethod
    def from_string(cls, string, *args, **kwargs):
        """Get serializer from string.

        Note that default method just calls the __init__ and ignores the
        string. The string only needs to be parsed if it tells us something
        about the args and kwargs we need to pass the serializer.

        Args:
            string (str): string repr of serializer, as defined in its
                string method.
            args (list): additional args to pass to serializer init.
            kwargs (dict): additional kwargs to pass to serializer init.
        """
        return cls(*args, **kwargs)


class NumberSerializer(BaseSerializer):
    """Serialize ints, as these can't be used as json keys.

    For convenience, this assumes the distinction between int and float
    is irrelevant, so just uses float.

    Types:
        int, float
    """
    def serialize(self, obj):
        return str(obj)
    def deserialize(self, obj):
        try:
            return float(obj)
        except ValueError:
            return None


class DateTimeSerializer(BaseSerializer):
    """Serialize a DateTime or TimeDelta object.

    Types:
        BaseDateTimeWrapper, TimeDelta
    """
    # TODO: use date_time_obj_from_string method so type isn't required
    def __init__(self, type_=None, *args, **kwargs):
        """Initialise serializer to serialize given type.

        Args:
            type_ (class): DateTime class we're serializing.
            args (list): additional args that can be passed to the serialize
                and deserialize functions.
            kwargs (dict): additional kwargs that can be passed to the
                serialize and deserialize functions.
        """
        super(DateTimeSerializer, self).__init__(*args, **kwargs)
        self._type = type_

    def serialize(self, obj):
        return obj.string(
            *self._serialize_args,
            **self._serialize_kwargs
        )

    def deserialize(self, obj):
        return self._type.from_string(
            obj,
            *self._serialize_args,
            **self._serialize_kwargs
        )


class TreeSerializer(BaseSerializer):
    """Serialize a tree object using its path.

    Types:
        BaseTreeItem
    """
    def __init__(self, tree_root, *args, **kwargs):
        """Initialize serializer with tree root item.

        Args:
            tree_root (TaskRoot): tree root item.
            args (list): additional args, to be ignored.
            kwargs (dict): additional_kwargs, to be ignored.
        """
        super(TreeSerializer, self).__init__(*args, **kwargs)
        self._tree_root = tree_root

    def serialize(self, obj):
        return obj.path

    def deserialize(self, obj):
        return self._tree_root.get_item_at_path(obj)


# class IdSerializer(BaseSerializer):
#     """Serialize and deserialize items by id.

#     Types:
#         Id
#     """
#     def __init__(self, serializer, *args, **kwargs):
#         """Initialize id serializer.

#         This serializer uses get_object_by_id to convert the id into another
#         object, then uses another serializer to serialize that object.

#         Args:
#             serializer (BaseSerializer): serializer to use on object once
#                 we've found it based on id.
#             args (list): additional args, to be ignored.
#             kwargs (dict): additional_kwargs, to be ignored.
#         """
#         super(IdSerializer, self).__init__()
#         self._serializer = serializer

#     def serialize(self, id):
#         object = get_object_by_id(id)
#         if object:
#             return self._serializer.serialize(object)
#         return None

#     def deserialize(self, obj):
#         object = self._serializer.deserialize(obj)
#         return get_object_id(object)

#     def string(self):
#         """Serialize serializer class as string.

#         Returns:
#             (str): serialized serializer.
#         """
#         return "{0}({1})".format(
#             self.__class__.__name__,
#             self._serializer.__class__.__name__
#         )

#     @classmethod
#     def from_string(cls, string, *args, **kwargs):
#         """Get serializer from string.

#         Args:
#             string (str): string repr of serializer, as defined in its
#                 string method.
#             args (list): additional args to pass to subserializer init.
#             kwargs (dict): additional kwargs to pass to subserializer init.
#         """
#         string = string[len(cls.__name__)+1:-1]
#         subserializer = get_serializer_from_string(string, *args, **kwargs)
#         return cls(subserializer)


# TODO: should we make these strings smaller, eg. just letters with an ! or etc
# still needs to be distinctive so we don't create it accidentally but could
# make it something that doesn't disrupt readability of the serialized files
# should probably also reserve the final strings, so that users can't
# accidentally create them.
# ALTHOUGH it's really the serializer marker thing from default module that
# needs to be reserved. Same discussion applies to that too.
def convert_serializer_to_string(serializer):
    """Convert serializer to string.

    Args:
        serializer (BaseSerializer): serializer to serialize.

    Returns:
        string (str): string repr of serializer.
    """
    return serializer.string()


def get_serializer_from_string(string, *args, **kwargs):
    """Get serializer from string.

    Args:
        string (str): string repr of serializer, as defined in its
            string method.
        args (list): additional args to pass to serializer init.
        kwargs (dict): additional kwargs to pass to serializer init.

    Returns:
        (BaseSerializer): serializer.
    """
    serializers = [
        BaseSerializer,
        DateTimeSerializer,
        TreeSerializer,
        # IdSerializer,
    ]
    for serializer in serializers:
        if string.startswith(serializer.__name__):
            return serializer.from_string(string, *args, **kwargs)
    raise SerializerError(
        "Cannot find serializer from string {0}".format(string)
    )
