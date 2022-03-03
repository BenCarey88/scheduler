"""Classes to define conversion of various types to json-compatible types."""


class SerializerError(Exception):
    """Exception for any errors related to serializer class."""


class BaseSerializer(object):
    """Base serializer class, used for types that are already json types.

    Types:
        str, float, int, list, tuple, dict
    """
    TYPE_REQUIRED = False

    def __init__(self, type_=None, *args, **kwargs):
        """Initialise serializer to serialize given type.

        Args:
            type_ (type or None): type we're serializing (must be one of
                the types listed in the class docstring). In some cases,
                this isn't needed by the class, so None can be passed.
            args (list): additional args that can be passed to the serialize
                and deserialize functions.
            kwargs (dict): additional kwargs that can be passed to the
                serialize and deserialize functions.
        """
        if self.TYPE_REQUIRED and type_ is None:
            raise SerializerError(
                "{0} Serializer requires type argument in __init__".format(
                    self.__class__.__name__
                )
            )
        self._type = type_
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


# TODO: remove? arguably based on current implementations, there's
# really no point to a TYPE_REQUIRED required serializer, as in that
# case we may as well just deserialize manually.
class SerializableSerializer(BaseSerializer):
    """Serialize a serializable class.

    Types:
        BaseSerializable
    """
    TYPE_REQUIRED = True

    def serialize(self, obj):
        return obj.to_dict()

    def deserialize(self, obj):
        return self._type.from_dict(obj)


class DateTimeSerializer(BaseSerializer):
    """Serialize a DateTime or TimeDelta object.

    Types:
        BaseDateTimeWrapper, TimeDelta
    """
    # TODO: use date_time_obj_from_string method so type isn't required
    TYPE_REQUIRED = True

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
    def __init__(self, tree_root, type_=None, *args, **kwargs):
        """Initialize serializer with tree root item.

        Args:
            tree_root (TaskRoot): tree root item.
            type_ (type or None): type to serialize.
            args (list): additional args, to be ignored.
            kwargs (dict): additional_kwargs, to be ignored.
        """
        super(TreeSerializer, self).__init__(type_)
        self._tree_root = tree_root

    def serialize(self, obj):
        return obj.path

    def deserialize(self, obj):
        return self._tree_root.get_item_at_path(obj)
