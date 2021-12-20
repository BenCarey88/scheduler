"""Base class for classes that can be serialized as dicts and jsons."""


from abc import ABC, abstractclassmethod, abstractmethod
from collections import OrderedDict
import json
import os


class FileError(Exception):
    """Exception class for file related errors."""


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
        NONE:       cannot be saved to a file or directory. This is used for
            classes that can only be written to a dictionary and read from a
            dictionary, and are generally saved as a subdict in another
            serialized class's json file.
    """
    FILE = "File"
    DIRECTORY = "Directory"
    EITHER = "Either"
    NONE = "None"


class SerializableFileTypes():
    """Struct for accepted filetypes for json serialized files.

    The intended purpose of these file types are as follows:
        JSON:   all classes serialized as files should be saved as jsons.
        MARKER: empty file that marks out that directory it lives in represents
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


# TODO: use this in task classes
class Serializable(ABC):
    """Base class for dictionary and file/directory serialization."""

    __SAVE_TYPE__ = SaveType.FILE
    __DIR_MARKER__ = None

    @abstractmethod
    def to_dict(self):
        """Virtual method to create dict from file."""
        pass

    @abstractclassmethod
    def from_dict(cls, dictionary):
        """Virtual method to initialise class from dictionary"""
        pass

    # TODO: should we raise errors here on failed read? Or add to a logger?
    # whatever we do should also be applied to the tree._file_utils as well.
    # if we raise errors, remember to add to docstirng.
    @staticmethod
    def read_json_file(file_path, as_ordered_dict=False):
        """Read json dict from file_path.

        Args:
            file_path (str): path to file to read from.
            as_ordered_dict (bool): whether to return dict or OrderedDict.

        Returns:
            (dict or OrderedDict): json dictionary.
        """
        if not os.path.isfile(file_path):
            raise FileError(
                "File {0} does not exist".format(file_path)
            )
        with open(file_path, "r") as file_:
            file_text = file_.read()
        try:
            if as_ordered_dict:
                return json.loads(file_text, object_pairs_hook=OrderedDict)
            return json.load(file_text)
        except json.JSONDecodeError:
            raise FileError(
                "File {0} is incorrectly formatted for json load".format(
                    file_path
                )
            )

    # TODO: since we're making .info a required standard here, we should make
    # it a constant and inherit it in subclasses.
    def to_file(self, file_path):
        """Serialize class as json file.

        Args:
            file_path (str): path to the json file. This should be a .json
                file in most cases, or a .info file for the additional
                info file sometimes required in directory serialization.
        """
        if self.__SAVE_TYPE__ not in [SaveType.FILE, SaveType.EITHER]:
            raise FileError(
                "{0} has save type '{1}', so can't be saved to a file".format(
                    str(self), self.__SAVE_TYPE__
                )
            )
        if not os.path.isdir(os.path.dirname(file_path)):
            raise FileError(
                "File directory {0} does not exist".format(file_path)
            )
        if os.path.splitext(file_path)[-1] not in [".json", ".info"]:
            raise FileError(
                "File path {0} is not a json.".format(file_path)
            )
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def from_file(cls, file_path, use_ordered_dict=False):
        """Initialise class from json file.

        Args:
            file_path (str): path to file to initialise from.
            use_ordered_dict (bool): whether to load json as dict or
                OrderedDict.

        Returns:
            (Serializable): class instance.
        """
        if cls.__SAVE_TYPE__ not in [SaveType.FILE, SaveType.EITHER]:
            raise FileError(
                "{0} has save type '{1}', so can't be read from a file".format(
                    str(cls), cls.__SAVE_TYPE__
                )
            )
        json_dict = cls.read_json_file(file_path, use_ordered_dict)
        return cls.from_dict(json_dict)

    @staticmethod
    def is_serialized_directory(directory_path, marker_file):
        """Check if directory represents a serialized class.

        Args:
            directory_path (str): path to directory.
            marker_file (str or None): name of marker file in this directory,
                that designates the directory as a serialized class, or None.
                If None, we fail instantly.

        Returns:
            (bool) whether or not directory path represents a valid directory
                that can be deserialized.
        """
        if not marker_file:
            return False
        if os.path.isdir(directory_path):
            marker_file_path = os.path.join(
                directory_path,
                marker_file
            )
            if os.path.isfile(marker_file_path):
                return True
        return False

    # TODO: make info files in tasks directories into json formatting
    @classmethod
    def read_directory(
            cls,
            directory_path,
            marker_file,
            subdir_class_key,
            file_class_key,
            subdir_class=None,
            file_class=None,
            subdir_class_type=dict,
            file_class_type=dict,
            return_type=dict,
            info_file=None,
            order_file=None):
        """Get dict from directory path.

        This is used for classes that contain dictionaries or lists of
        subclasses. The base implementation assumes that all files will
        represent one type of class, and all subdirectories will represent
        another (potentially different) type of class.

        Additional dictionary data may be stored in a given info file, which
        can be read with the read_info_file method. In the base class this
        is assumed to just be a json file with an ordering of files and
        subdirectories from this directory.

        Args:
            directory_path (str): path to directory.
            marker_file (str): name of marker file in this directory, that
                designates the directory as a serialized class. This can be
                the same as the info_file or order_file.
            subdir_class_key (str): string used to key dict/list of subdir
                class items.
            file_class_key (str): string used to key dict/list of file class
                class items.
            subdir_class (class or None): class to use for subdirectories. If
                None, use cls.
            file_class (class or None): class to use for json files in
                directory. If None, use cls.
            subdir_class_type (type): type to use for subdir class - standardly
                this should be dict, OrderedDict or list.
            file_class_type (type): type to use for file class - standardly
                this should be dict, OrderedDict or list.
            return_type (type): type to use for file class - dict or
                OrderedDict
            info_file (str or None): name of file that gives additional info
                about class, if one exists.
            order_file (str or None): name of file that determines order of
                of subdirs and files in the directory.

        Returns:
            (dict): dictonary defined by directory.
        """
        subdir_class = subdir_class or cls
        file_class = file_class or cls
        if not cls.is_serialized_directory(directory_path, marker_file):
            raise FileError(
                "Directory path {0} is not a serialized class "
                "directory".format(directory_path)
            )

        return_dict = return_type()
        if info_file:
            info_file_path = os.path.join(directory_path, info_file)
            return_dict = cls.read_json_file(
                info_file_path,
                as_ordered_dict=(return_type==OrderedDict)
            )

        if order_file:
            order_file_path = os.path.join(directory_path, order_file)
            order = cls.read_json_file(order_file_path)
            if not isinstance(order, list):
                raise FileError(
                    "Order file {0} is not formatted as a json list".format(
                        order_file_path
                    )
                )
            for name in order:
                if not name:
                    # ignore empty strings
                    continue
                path = os.path.join(directory_path, name)
                if cls.is_serialized_directory(path, subdir_class.__DIRECTORY_MARKER__):
                    subcategory = TaskCategory.from_directory(path, category_item)
                    category_item.add_subcategory(subcategory)
                elif (os.path.isfile("{0}.json".format(path))):
                    task = Task.from_file("{0}.json".format(path), category_item)
                    category_item.add_task(task)

        return return_dict

    # def write(self, directory_path):
    #     """Write data to directory tree.

    #     The structure is:
    #         category_tree_dir:
    #             subcategory_1_tree_dir:
    #             subcategory_2_tree_dir:
    #             task_1.json
    #             task_2.json
    #             TREE_FILE_MARKER

    #     The TREE_FILE_MARKER file saves the official ordering as this
    #     will be lost in the directory.

    #     Args:
    #         directory_path (str): path to directory to write to.
    #     """
    #     (
    #         directory_path,
    #         self.TREE_FILE_MARKER
    #     )

    #     tmp_dir = None
    #     if os.path.exists(directory_path):
    #         tmp_dir = tempfile.mkdtemp(
    #             suffix="{0}_backup_".format(os.path.basename(directory_path)),
    #             dir=os.path.dirname(directory_path),
    #         )
    #         shutil.move(directory_path, tmp_dir)
    #     os.mkdir(directory_path)
    #     task_category_file = os.path.join(
    #         directory_path,
    #         self.TREE_FILE_MARKER
    #     )
    #     with open(task_category_file, "w") as file_:
    #         file_.write(
    #             "\n".join([child.name for child in self.get_all_children()])
    #         )

    #     for subcategory in self.get_all_subcategories():
    #         subcategory_directory = os.path.join(
    #             directory_path,
    #             subcategory.name
    #         )
    #         subcategory.write(subcategory_directory)

    #     for task in self.get_all_tasks():
    #         task_file = os.path.join(
    #             directory_path,
    #             "{0}.json".format(task.name)
    #         )
    #         task.write(task_file)

    #     if tmp_dir:
    #         shutil.rmtree(tmp_dir)

    # @classmethod
    # def from_directory(
    #         cls,
    #         directory_path,
    #         parent=None):
    #     """Create TaskCategory object from category directory.

    #     Args:
    #         directory_path (str): path to category directory.
    #         parent (TaskCategory or None): parent item.

    #     Raises:
    #         (TaskFileError): if the directory doesn't exist or isn't a task
    #             directory (ie. doesn't have a TREE_FILE_MARKER)

    #     Returns:
    #         (TaskCategory): TaskCategory object populated with categories from
    #             directory tree.
    #     """
    #     if not is_tree_directory(directory_path, cls.TREE_FILE_MARKER):
    #         raise TaskFileError(
    #             "Directory {0} is not a valid task root directory".format(
    #                 directory_path
    #             )
    #         )
    #     category_name = os.path.basename(directory_path)
    #     category_item = cls(name=category_name, parent=parent)

    #     task_category_file = os.path.join(directory_path, cls.TREE_FILE_MARKER)
    #     with open(task_category_file, "r") as file_:
    #         child_order = file_.read().split("\n")

    #     for name in child_order:
    #         if not name:
    #             # ignore empty strings
    #             continue
    #         path = os.path.join(directory_path, name)
    #         if is_tree_directory(path, TaskCategory.TREE_FILE_MARKER):
    #             subcategory = TaskCategory.from_directory(path, category_item)
    #             category_item.add_subcategory(subcategory)
    #         elif (os.path.isfile("{0}.json".format(path))):
    #             task = Task.from_file("{0}.json".format(path), category_item)
    #             category_item.add_task(task)

    #     return category_item

    def write(self, path):
        """Write to path.

        Args:
            path (str): file or directory path to write to.
        """
        if self.__SAVE_TYPE__ == SaveType.FILE:
            self.to_file(path)
        elif self.__SAVE_TYPE__ == SaveType.DIRECTORY:
            self.to_directory(path)
        elif self.__SAVE_TYPE__ == SaveType.EITHER:
            # assume that path is a file if it has an extension
            if os.path.splitext(path)[1]:
                self.to_file(path)
            else:
                os.path.to_directory(path)
        raise FileError(
            "{0} has save type '{1}', so can't be saved to a file "
            "or directory".format(str(self), self.__SAVE_TYPE__)
        )

    @classmethod
    def read(cls, path):
        """Read class from path.

        Args:
            path (str): file or directory to read from.
        """
        if cls.__SAVE_TYPE__ == SaveType.FILE:
            return cls.from_file(path)
        elif cls.__SAVE_TYPE__ == SaveType.DIRECTORY:
            return cls.from_directory(path)
        elif cls.__SAVE_TYPE__ == SaveType.EITHER:
            if os.path.isfile(path):
                return cls.from_file(path)
            elif os.path.isdir(path):
                return cls.from_directory(path)
            raise FileError(
                "Path {0} is neither a file nor a directory".format(path)
            )
        raise FileError(
            "{0} has save type '{1}', so can't be read from a file "
            "or directory".format(str(cls), cls.__SAVE_TYPE__)
        )
