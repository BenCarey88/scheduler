"""Base class for classes that can be serialized as dicts and jsons."""


from abc import ABC, abstractclassmethod, abstractmethod
from ast import excepthandler
from collections import OrderedDict
import json
import os
import shutil
import tempfile

from .file_utils import (
    check_directory_can_be_written_to,
    is_serialize_directory,
    SerializationError
)


class SaveType():
    """Struct for types of save available for serialized classes.

    The interpretation of the different types is as follows:
        FILE:       can be read from and written to a json file.
        DIRECTORY:  can be read from and written to a directory. The files and
            subdirectories in this directory represent serializations of other
            classes contained in attributes of the serialized class. Additional
            data can be stored in special files, defined below in the
            SerializableFileTypes struct.
        EITHER:     can be read/written to/from a file or a directory.
        NESTED:     cannot be saved to a file or directory. This is used for
            classes that can only be written to a dictionary and read from a
            dictionary, and will be saved as a subdict in another serialized
            class's json file.
    """
    FILE = "File"
    DIRECTORY = "Directory"
    EITHER = "Either"
    NESTED = "Nested"

    _FILE_TYPES = [FILE, EITHER]
    _DIR_TYPES = [DIRECTORY, EITHER]


class SerializableFileTypes():
    """Struct for accepted filetypes for json serialized files.

    The intended purpose of these file types are as follows:
        JSON:   all classes serialized as files should be saved as jsons.
        MARKER: empty file that marks that the directory it lives in represents
            a serialized class and can be read accordingly. A marker file is
            required for any directory-serializable class, but in cases where
            an order or info file is used, one of these can be designated as
            the marker.
        ORDER:  optional json formatted file representing the order that all
            files and subdirectories in a directory should be read in, in cases
            where the order matters for deserialization.
        INFO:   optional json formatted file representing any additional info
            required for deserialization of a directory.
    """
    JSON = ".json"
    MARKER= ".marker"
    ORDER = ".order"
    INFO = ".info"


class BaseSerializable(ABC):
    """Base class for dictionary and file/directory serialization.

    This is for classes that can be serialized to/deserialized from
    dictionaries, which in turn can be saved to/read from either files
    or directories.

    All subclasses make use of these two class variables:

        _SAVE_TYPE (SaveType): the type of save that this serialization uses
            (see SaveType struct above).
        _DICT_TYPE (type): the type of dict that this class can be serialized
            to (can be dict or OrderedDict).
        _STORE_SAVE_PATH (bool): if True, store the path this serializable was
            read from during read method so we can use it in the write method.
    """
    _SAVE_TYPE = SaveType.FILE
    _DICT_TYPE = dict
    _STORE_SAVE_PATH = False

    def __init__(self):
        """Initialize serializable instance."""
        self._save_path = None

    @property
    def _save_type(self):
        """Get save type of class.

        This property can be overridden in subclasses to allow classes with an
        EITHER save type to specify the type based on class details - so they
        can be read from either but we determine how they're written.

        Returns:
            (SaveType): save type.
        """
        return self._SAVE_TYPE

    def set_save_path(self, save_path):
        """Set save path for serializable.

        This is a path that can be used with the write command, so that we
        don't have to pass in a path to write.

        Args:
            save_path (str): path to write this serializable to. 
        """
        self._save_path = save_path

    ### Dict Read/Write ###
    # These must be reimplemented in subclasses
    @abstractclassmethod
    def from_dict(cls, dictionary, *args, **kwargs):
        """Virtual method to initialise class from dictionary.

        The from_file, from_directory and read methods all include generic args
        and kwargs, which will be passed directly to this method. So apart from
        the first argument, those methods will have the same arguments as this
        one.

        Args:
            dictionary (dict or OrderedDict): the dictionary we're using to
                deserialize the class.
            args (list): additional arguments.
            kwargs (dict): additional keyword arguments.
        """
        pass

    @abstractmethod
    def to_dict(self):
        """Virtual method to create dict from class.

        Returns:
            (dict or OrderedDict): Serialized dictionary.
        """
        pass

    ### File Read/Write ###
    @staticmethod
    def _read_json_file(file_path, as_ordered_dict=False):
        """Read json dict from file_path.

        Args:
            file_path (str): path to file to read from.
            as_ordered_dict (bool): whether to return dict or OrderedDict.

        Returns:
            (dict or OrderedDict): json dictionary.
        """
        # TODO: should we raise errors here on failed read? Or add to a logger?
        # if we raise errors, remember to add to docstring.
        if not os.path.isfile(file_path):
            raise SerializationError(
                "File {0} does not exist".format(file_path)
            )
        with open(file_path, "r") as file_:
            file_text = file_.read()
        try:
            if as_ordered_dict:
                return json.loads(file_text, object_pairs_hook=OrderedDict)
            return json.loads(file_text)
        except json.JSONDecodeError:
            raise SerializationError(
                "File {0} is incorrectly formatted for json load".format(
                    file_path
                )
            )

    @classmethod
    def from_file(cls, file_path, *args, **kwargs):
        """Initialise class from json file.

        Args:
            file_path (str): path to file to initialise from.
            args (list): additional arguments to pass to from_dict.
            kwargs (dict): additional keyword arguments to pass to from_dict.

        Returns:
            (BaseSerializable): class instance.
        """
        if cls._SAVE_TYPE not in SaveType._FILE_TYPES:
            raise SerializationError(
                "{0} has save type '{1}', so can't be read from a file".format(
                    str(cls), cls._SAVE_TYPE
                )
            )
        json_dict = cls._read_json_file(
            file_path,
            as_ordered_dict=(cls._DICT_TYPE==OrderedDict)
        )
        return cls.from_dict(json_dict, *args, **kwargs)

    def to_file(self, file_path):
        """Serialize class as json file.

        Args:
            file_path (str): path to the json file. This should be a .json
                file in most cases, or a .info file for the additional
                info file sometimes required in directory serialization.
        """
        if self._save_type not in SaveType._FILE_TYPES:
            raise SerializationError(
                "{0} has save type '{1}', so can't be saved to a file".format(
                    str(self), self._save_type
                )
            )
        if not os.path.isdir(os.path.dirname(file_path)):
            raise SerializationError(
                "File directory {0} does not exist".format(file_path)
            )
        if os.path.splitext(file_path)[-1] not in [".json"]:
            raise SerializationError(
                "File path {0} is not a json.".format(file_path)
            )
        with open(file_path, 'w') as file_:
            json.dump(self.to_dict(), file_, indent=4)

    ### Directory Read/Write ###
    @classmethod
    def from_directory(cls, directory_path, *args, **kwargs):
        """Initialise class from directory.

        Args:
            directory_path (str): directory to read from.
            args (list): additional arguments to pass to from_dict.
            kwargs (dict): additional keyword arguments to pass to from_dict.

        Returns:
            (BaseSerializable): class instance.
        """
        raise NotImplementedError(
            "from_directory needs to be reimplemented in subclasses that "
            "permit directory deserialization."
        )

    def to_directory(self, directory_path):
        """Write class to directory path.

        Args:
            directory_path (str): directory to write to.
            args (list): additional arguments to pass to from_dict.
            kwargs (dict): additional keyword arguments to pass to from_dict.
        """
        raise NotImplementedError(
            "to_directory needs to be reimplemented in subclasses that "
            "permit directory serialization."
        )

    ### General Read/Write ###
    @classmethod
    def read(cls, path, *args, **kwargs):
        """Read class from path.

        Args:
            path (str): file or directory to read from.
            args (list): additional arguments to pass to from_dict.
            kwargs (dict): additional keyword arguments to pass to from_dict.

        Returns:
            (BaseSerializable): class instance.
        """
        if cls._SAVE_TYPE == SaveType.FILE:
            instance = cls.from_file(path, *args, **kwargs)
        elif cls._SAVE_TYPE == SaveType.DIRECTORY:
            instance = cls.from_directory(path, *args, **kwargs)
        elif cls._SAVE_TYPE == SaveType.EITHER:
            if os.path.isfile(path):
                instance = cls.from_file(path, *args, **kwargs)
            elif os.path.isdir(path):
                instance = cls.from_directory(path, *args, **kwargs)
            raise SerializationError(
                "Path {0} is neither a file nor a directory".format(path)
            )
        else:
            raise SerializationError(
                "{0} has save type '{1}', so can't be read from a file "
                "or directory".format(str(cls), cls._SAVE_TYPE)
            )
        if cls._STORE_SAVE_PATH:
            instance._save_path = path
        return instance

    # TODO: we should split up serialization errors - we don't want to catch
    # every single one here. Ideally I think we should catch cases
    # eg. things that will stop us writing back may need to be flagged here
    @classmethod
    def safe_read(cls, path, *args, **kwargs):
        """Read class from path, or create new one if error.

        Note for this to work, we need to ensure that the __init__ method
        doesn't require additional arguments that aren't passed to the read
        method (or alternatively that we pass additional init args as kwargs
        and the read method can just accept and ignore these).

        Args:
            path (str): file or directory to read from.
            args (list): args to pass to class read or __init__ method.
            kwargs (dict): kwargs to pass to class read or __init__ method.

        Returns:
            (BaseSerializable): class instance.
        """
        try:
            return cls.read(path, *args, **kwargs)
        except SerializationError as e:
            print (
                "Could not read class instance at path {0}"
                " - hit error {1}".format(path, e.message)
            )
            instance = cls(*args, **kwargs)
            if cls._STORE_SAVE_PATH:
                # this may cause crashes during write if the wrong errors
                # have been caught
                instance._save_path = path
            return instance

    def write(self, path=None):
        """Write to path.

        Args:
            path (str or None): file or directory path to write to, or None
                if we intend to use stored save_path instead.
        """
        path = path or self._save_path
        if not path:
            raise SerializationError(
                "Save path has not been set on {0} instance.".format(
                    self.__class__.__name__
                )
            )
        if self._save_type == SaveType.FILE:
            self.to_file(path)
        elif self._save_type == SaveType.DIRECTORY:
            self.to_directory(path)
        elif self._save_type == SaveType.EITHER:
            # assume that path is a file if it has an extension
            if os.path.splitext(path)[1]:
                self.to_file(path)
            else:
                self.to_directory(path)
        else:
            raise SerializationError(
                "{0} has save type '{1}', so can't be saved to a file "
                "or directory".format(str(self), self._save_type)
            )


class NestedSerializable(BaseSerializable):
    """Serializable class for nested structures.

    This class performs serialization through nested dictionaries, usually
    representing tree-like structures.

    The following global variables are defined to help with directory reading
    and writing (and so only need to overridden in subclasses with a save type
    of 'Directory' or 'Either'):

        _MARKER_FILE (str): name of marker file in this directory, that
            designates the directory as a serialized class. This can be the
            the same as the info_file or order_file, if they exist.
        _INFO_FILE (str or None): name of file that gives additional info
            about class, if one exists.
        _ORDER_FILE (str or None):  name of file that determines order of
            of subdirs and files in the directory, if one exists.
        _SUBDIR_KEY (str or None): string used to key dict/list of subdir
            class items. This should be used in the to_dict and from_dict
            methods too. It is also used to determine if this class can
            read/write subdirs when serializaing as a directory.
        _SUBDIR_CLASS (class, None): class to use for serializing /
            deserializing subdirectories in the given directory. If None, use
            this class.
        _SUBDIR_DICT_TYPE (type): type to store deserialized subdirectory
            classes in (should be dict or OrderedDict).
        _FILE_KEY (str): string used to key dict/list of file class items.
            This should be used in the to_dict and from_dict methods too.
            It is also used to determine if this class can read/write files
            when serializaing as a directory.
        _FILE_CLASS (class or None): class to use for serializing /
            deserializing files in the given directory. If None, use this
            class.
        _FILE_DICT_TYPE (type): type to store deserialized file classes in
            (should be dict or OrderedDict).
    """
    _MARKER_FILE = None
    _INFO_FILE = None
    _ORDER_FILE = None

    _SUBDIR_KEY = None
    _SUBDIR_CLASS = None
    _SUBDIR_DICT_TYPE = dict

    _FILE_KEY = None
    _FILE_CLASS = None
    _FILE_DICT_TYPE = dict

    @classmethod
    def _file_class(cls):
        """Get class used to read files in directory deserialization.

        Returns:
            (class): class used for file serialization/deserialization.
        """
        return cls._FILE_CLASS or cls

    @classmethod
    def _subdir_class(cls):
        """Get class used to read subdirs in directory deserialization.

        Returns:
            (class): class used for subdir serialization/deserialization.
        """
        return cls._SUBDIR_CLASS or cls

    ### Directory utils ###
    @classmethod
    def _run_directory_checks(cls):
        """Run error checks on directory-serializable subclass.

        This checks whether the global class attrs have been defined correctly.
        """
        if cls._SAVE_TYPE not in SaveType._DIR_TYPES:
            return

        # directory error checks
        if not cls._MARKER_FILE:
            raise SerializationError(
                "Directory writing not possible without a defined "
                "_MARKER_FILE attribute"
            )
        if not (cls._SUBDIR_KEY or cls._FILE_KEY):
            raise SerializationError(
                "Directory writing not possible without a defined "
                "_SUBDIR_KEY or _FILE_KEY attribute"
            )
        if (cls._SUBDIR_KEY and
                cls._subdir_class()._SAVE_TYPE not in SaveType._DIR_TYPES):
            raise SerializationError(
                "_subdir_class() must have a directory save type"
            )
        if (cls._FILE_KEY and
                cls._file_class()._SAVE_TYPE not in SaveType._FILE_TYPES):
            raise SerializationError(
                "_file_class() must have a file save type"
            )
        if (cls._FILE_KEY == cls._SUBDIR_KEY and
                cls._FILE_DICT_TYPE != cls._SUBDIR_DICT_TYPE):
            raise SerializationError(
                "If file key and subdir key are the same, their dict "
                "types must be too"
            )

    @classmethod
    def _check_directory_can_be_written_to(
            cls,
            directory_path,
            raise_error=True):
        """Check if directory path can be written to by this class.

        A directory path can have this nested serializable written to it so
        long as the following criteria are met:
            - the _SAVE_TYPE of this class is a directory one.
            - the path's parent directory exists.
            - the path is not a file.
            - the path either doesn't currently exist, or it exists and is
                already a serialized directory, so can be overwritten.

        Args:
            directory_path (str): path to directory we want to write.
            raise_error (bool): if True, raise error on failure.

        Raises:
            (SerializationError): if directory can't be written to.

        Returns:
            (bool): whether or not directory path can be written to.
        """
        if cls._SAVE_TYPE not in SaveType._DIR_TYPES:
            raise SerializationError(
                "{0} has save type '{1}', so can't be saved to a dir".format(
                    str(cls), cls._SAVE_TYPE
                )
            )
        return check_directory_can_be_written_to(
            directory_path,
            cls._MARKER_FILE,
            raise_error=raise_error
        )

    ### Directory Read/Write ###
    @classmethod
    def _read_directory(cls, directory_path):
        """Get dict from directory path.

        This is used for classes that contain dictionaries of subclasses.
        This assumes that all files will represent one type of class, and
        all subdirectories will represent another (potentially different)
        type of class.

        Additional dictionary data may be stored in the info file, and an
        ordering of the files and subdirs in the directory, if needed, can
        be stored in the order file.

        Args:
            (dict): directory class to read from.

        Returns:
            (dict): dictonary defined by directory.
        """
        subdir_class = cls._subdir_class()
        file_class = cls._file_class()
        if not is_serialize_directory(directory_path, cls._MARKER_FILE):
            raise SerializationError(
                "Directory path {0} is not a serialized class "
                "directory".format(directory_path)
            )

        # read info file if given
        return_dict = cls._DICT_TYPE()
        if cls._INFO_FILE:
            info_file_path = os.path.join(directory_path, cls._INFO_FILE)
            if os.path.exists(info_file_path):
                return_dict = cls._read_json_file(
                    info_file_path,
                    as_ordered_dict=(cls._DICT_TYPE==OrderedDict)
                )

        # get order from order file if given
        if cls._ORDER_FILE:
            order_file_path = os.path.join(directory_path, cls._ORDER_FILE)
            if os.path.exists(order_file_path):
                order = cls._read_json_file(order_file_path)
                if not isinstance(order, list):
                    raise SerializationError(
                        "Order file {0} is not formatted as json list".format(
                            order_file_path
                        )
                    )
        else:
            # remove file formatting from each name in dir
            order = [
                os.path.splitext(name)[0]
                for name in os.listdir(directory_path)
            ]

        # fill dicts of nested classes represented by files and subdirs
        subdir_dict = cls._SUBDIR_DICT_TYPE()
        file_dict = cls._FILE_DICT_TYPE()
        if cls._SUBDIR_KEY == cls._FILE_KEY:
            file_dict = subdir_dict
        for name in order:
            if not name:
                # ignore empty strings
                continue
            path = os.path.join(directory_path, name)
            subdir_marker = subdir_class._MARKER_FILE
            if (cls._SUBDIR_KEY
                    and subdir_marker
                    and is_serialize_directory(path, subdir_marker)):
                subdir_item_dict = subdir_class._read_directory(path)
                subdir_dict[name] = subdir_item_dict
            elif cls._FILE_KEY and os.path.isfile("{0}.json".format(path)):
                file_item_dict = file_class._read_json_file(
                    "{0}.json".format(path)
                )
                file_dict[name] = file_item_dict

        # add file and subdir classes to dict
        if cls._SUBDIR_KEY:
            return_dict[cls._SUBDIR_KEY] = subdir_dict
        if cls._FILE_KEY and cls._FILE_KEY != cls._SUBDIR_KEY:
            return_dict[cls._FILE_KEY] = file_dict

        return return_dict

    @classmethod
    def from_directory(cls, directory_path, *args, **kwargs):
        """Initialise class from directory.

        Args:
            directory_path (str): directory to read from.

        Returns:
            (NestedSerializable): class instance.
        """
        cls._run_directory_checks()
        if cls._SAVE_TYPE not in SaveType._DIR_TYPES:
            raise SerializationError(
                "{0} has save type '{1}', so can't be read from a dir".format(
                    str(cls), cls._SAVE_TYPE
                )
            )
        serialized_dict = cls._read_directory(directory_path)
        return cls.from_dict(serialized_dict, *args, **kwargs)

    @classmethod
    def _dict_to_directory(cls, directory_path, dict_repr):
        """Write dictionary representation of class to directory path.

        This is a class method because it doesn't require any internal data
        (all data is provided by the dictionary). Therefore, it can be called
        on nested file classes or subirectory classes within the to_directory
        method.

        Args:
            directory_path (str): directory to write to.
            dict_repr (dict or OrderedDict): dictionary representing class.
        """
        cls._check_directory_can_be_written_to(directory_path)

        # backup prev directory
        tmp_dir = None
        if os.path.exists(directory_path):
            tmp_dir = tempfile.mkdtemp(
                suffix="{0}_backup_".format(os.path.basename(directory_path)),
                dir=os.path.dirname(directory_path),
            )
            shutil.move(directory_path, tmp_dir)
        os.mkdir(directory_path)

        # marker file
        marker_file = os.path.join(directory_path, cls._MARKER_FILE)
        with open(marker_file, "w+"):
            pass

        # order file
        file_items = dict_repr.get(cls._FILE_KEY, {})
        subdir_items = dict_repr.get(cls._SUBDIR_KEY, {})
        if cls._ORDER_FILE:
            order_file = os.path.join(directory_path, cls._ORDER_FILE)
            seen = set()
            order = [
                x for x in list(file_items.keys()) + list(subdir_items.keys())
                if not (x in seen or seen.add(x))
            ]
            with open(order_file, "w") as file_:
                json.dump(order, file_, indent=4)

        # info file
        if cls._INFO_FILE:
            info_file = os.path.join(directory_path, cls._INFO_FILE)
            info_dict = cls._DICT_TYPE()
            for key, subdict in dict_repr.items():
                if key not in [cls._SUBDIR_KEY, cls._FILE_KEY]:
                    info_dict[key] = subdict
            with open(info_file, "w+") as file_:
                json.dump(info_dict, file_, indent=4)

        # files
        for file_item_key, file_item_dict in file_items.items():
            file_name = "{0}.json".format(file_item_key)
            file_path = os.path.join(directory_path, file_name)
            with open(file_path, "w+") as file_:
                json.dump(file_item_dict, file_, indent=4)

        # subdirs
        for subdir_item_key, subdir_item_dict in subdir_items.items():
            subdir_path = os.path.join(directory_path, subdir_item_key)
            cls._subdir_class()._dict_to_directory(
                subdir_path,
                subdir_item_dict
            )

        # remove backup
        if tmp_dir:
            shutil.rmtree(tmp_dir)

    def to_directory(self, directory_path):
        """Write class to directory path.

        Args:
            directory_path (str): directory to write to.
        """
        self._run_directory_checks()
        dict_repr = self.to_dict()
        self._dict_to_directory(directory_path, dict_repr)


class CustomSerializable(NestedSerializable):
    """Serializable class that doesn't use dictionaries for serialization."""

    def to_dict(self):
        """Override to_dict method so it doesn't need to be defined."""
        raise NotImplementedError(
            "to_dict method not implemented for {0}".format(
                self.__class__.__name__
            )
        )

    @classmethod
    def from_dict(cls):
        """Override to_dict method so it doesn't need to be defined."""
        raise NotImplementedError(
            "from_dict method not implemented for {0}".format(cls.__name__)
        )
