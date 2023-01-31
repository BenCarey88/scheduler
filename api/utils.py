"""Utility functions for scheduler api."""

from contextlib import contextmanager
import datetime
from enum import Enum
import sys


@contextmanager
def indent_print(bookend=None, indent=1, time_it=False):
    """Context manager to indent all prints, used for debugging.

    Args:
        indent (int): number of tabs to indent by.
        bookend (str or None): string to print on either side.
        time_it (bool): if True, time it.
    """
    if bookend is not None:
        print ("[START]:", bookend)
    old_print = __builtins__["print"]
    def new_print(*strings):
        old_print("\t" * indent, *strings)
    __builtins__["print"] = new_print
    start_time = datetime.datetime.now()
    yield
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    __builtins__["print"] = old_print
    if bookend is not None:
        if time_it:
            print ("[END]:", bookend, duration)
        else:
            print ("[END]:", bookend)
    elif time_it:
        print ("[TIME]:", duration)


def catch_exceptions(exceptions=None):
    """Decorator factory to make a function safe from the given exceptions.

    The decorated function will return None if the exception occurs, otherwise
    it will return whatever the function would return normally.

    Args:
        exceptions (Exception or tuple(Exception) or None): exception(s) to
            catch. If None, we catch all exceptions.

    Returns:
        (function): the function decorator.
    """
    def decorator(function):
        def decorated_function(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except (exceptions or Exception):
                return None
        return decorated_function
    return decorator


def fallback_value(value, fallback):
    """Simple function to return value or fallback if value is None.

    Args:
        value (variant or None): value to return if it's not None.
        fallback (variant): fallback to return if value is None.

    Returns:
        (variant): value if value isn't None, else fallback.
    """
    return (value if value is not None else fallback)


def clamp(value, min_, max_):
    """Clamp value between min and max.

    Args:
        value (int or float): value to clamp.
        min_ (int or float): minimum value.
        max_ (int or float): maximum value.

    Returns:
        (int or float): clamped value
    """
    if min_ > max_:
        raise ValueError("min {0} is greater than max {1}".format(min_, max_))
    return min(max_, max(min_, value))


def add_key_at_start(ordered_dict, key, value):
    """Add key to the start of an ordered dict.

    Args:
        ordered_dict (OrderedDict): the ordered dict to add to.
        key (variant): the key to add.
        value (variant): the value to set at that key.
    """
    ordered_dict[key] = value
    if sys.version_info >= (3, 2):
        ordered_dict.move_to_end(key, last=False)
    else:
        for i in range(len(ordered_dict) - 1):
            k, v = ordered_dict.popitem(last=False)
            ordered_dict[k] = v


def get_class_name_from_method(method):
    """Get name of class that a given class method belongs to.

    Args:
        method (function): method of some class.

    Returns:
        (str): name of class.
    """
    if sys.version_info >= (3, 3):
        return method.__qualname__.split(".")[0]
    else:
        return type(method.__im_class__).__name__


def backup_git_repo(repo_path, commit_message="backup"):
    """Attempt to commit and push all files in git repo at given path.

    Args:
        repo_path (str): path to local git repository.
        commit_message (str or None): message for commit.

    Returns:
        (str or None): error message, if save was unsuccessful.
    """
    try:
        import git
    except ImportError:
        return (
            "Could not import GitPython module. Ensure python version >= 3.7 "
            "and this is installed."
        )
    try:
        git_repo = git.Repo(repo_path)
    except git.exc.InvalidGitRepositoryError:
        return "Directory {0} is not a valid git repo".format(repo_path)
    modified_files = [
        x for x in git_repo.git.diff(None, name_only=True).split("\n") if x
    ]
    untracked_files = git_repo.untracked_files
    files_to_stage = modified_files + untracked_files
    if not files_to_stage:
        return None

    for file_ in files_to_stage:
        try:
            git_repo.git.add(file_)
        except git.exc.GitCommandError as e:
            return "Git error when staging file {0} in repo {1}:\n{2}".format(
                file_,
                repo_path,
                e.stderr
            )
    try:
        git_repo.git.commit("-m", commit_message)
    except git.exc.GitCommandError as e:
        return "Git error when committing changes for repo {0}:\n{1}".format(
            repo_path,
            e.stderr
        )
    try:
        git_repo.git.push()
    except git.exc.GitCommandError as e:
        return "Git error when pushing changes for repo {0}:\n{1}".format(
            repo_path,
            e.stderr
        )

    return None


class OrderedStringEnum(str, Enum):
    """Base ordered enumerator with string values.

    All string enum classes should inherit from this. It defines an
    ordering on the values based on the order they're written in the
    class definitions, with the first values the smallest.

    If you want to manually define the ordering, you can use tuples
    to define the order values, eg.

    class Color(OrderedStringEnum):
        RED = ("Red", 0)
        BLUE = ("Blue", 1)
        GREEN = ("Green", 2)
    """
    def __new__(cls, *args):
        if len(args) == 1:
            number = len(cls.__members__)
            obj = str.__new__(cls, args[0])
            obj._key_ = number
            return obj
        elif len(args) == 2:
            value, number = args
            obj = str.__new__(cls, value)
            obj._key_ = number
            return obj
        raise Exception(
            "Invalid args to pass to OrderedStringEnum: {0}".format(str(args))
        )

    @classmethod
    def get_values(cls):
        """Get all values for enum."""
        return cls.__members__

    @property
    def key(self):
        """Get key for ordering comparisons."""
        return self._key_

    def key_function(self):
        """Get key for ordering comparisons.

        This is the same as the above but no longer implemented as a property.
        """
        return self._key_

    def _assert_comparable(self, other):
        """Assert that the given values are comparable."""
        if (not issubclass(self.__class__, other.__class__)
                or not issubclass(other.__class__, self.__class__)):
            raise Exception(
                "Cannot compare enum values of different classes "
                "{0} and {1}".format(
                    self.__class__.__name__,
                    other.__class__.__name__,
                )
            )

    def __gt__(self, other):
        """Check if this is greater than another enum."""
        self._assert_comparable(other)
        return self.key > other.key

    def __ge__(self, other):
        """Check if this is greater than or equal to another enum."""
        self._assert_comparable(other)
        return self.key >= other.key

    def __lt__(self, other):
        """Check if this is less than another enum."""
        self._assert_comparable(other)
        return self.key < other.key
    
    def __le__(self, other):
        """Check if this is less than or equal to another enum."""
        self._assert_comparable(other)
        return self.key <= other.key

    def __repr__(self):
        """Get string representation of enum."""
        return self.value

    def __str__(self):
        """Get string representation of enum."""
        return self.value


# TODO: USE ACTUAL ENUMS (see my test under
# ~/OneDrive/Documents/Coding/Python/Other/Tests/enums.py)
# will need updating of all derived classes, and crucially
# will also require changes to serialization as I assume enums can't
# be automatically json-serialized? Maybe worth writing my own json
# encoder in this class too and then using that in the serializable
# module instead of the standard json one
# TBH, this needs to be combined with whatever's going on in the
# serializer classes too. It's a bit unneat atm.
# class OrderedStringEnum(object):
#     """Base ordered enumerator struct with string values.

#     Enumerators with an ordering should inherit from this and
#     fill in the values list to define the ordering.
#     """
#     VALUES = []
#     @classmethod
#     def key(cls, value):
#         """Get key, used to order values."""
#         i = 0
#         for i, val in enumerate(cls.VALUES):
#             if val == value:
#                 return i
#         return i + 1

#     @classmethod
#     def filter_key(cls, value):
#         """Key, but returns None if value not found."""
#         i = 0
#         for i, val in enumerate(cls.VALUES):
#             if val == value:
#                 return i
#         return None


"""Id registry to store floating items by temporary ids."""
_TEMPORARY_ID_REGISTRY = {}
_GLOBAL_COUNT = 0


def generate_temporary_id(item):
    """Generate temporary id for item.

    Args:
        item (variant): item to generate id for.

    Returns:
        (str): id of item.
    """
    global _GLOBAL_COUNT
    id = str(_GLOBAL_COUNT)
    _GLOBAL_COUNT += 1
    _TEMPORARY_ID_REGISTRY[id] = item
    return id


def get_item_by_id(id, remove_from_registry=False):
    """Get item by id and remove from registry.

    Args:
        id (str): id of item to get.
        remove_from_registry (bool): if True, remove the item from
            the registry after returning it.

    Returns:
        (variant or None): item, if found.
    """
    item = _TEMPORARY_ID_REGISTRY.get(id, None)
    if remove_from_registry and item is not None:
        del _TEMPORARY_ID_REGISTRY[id]
    return item
