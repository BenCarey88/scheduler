"""Utility functions for scheduler api."""

from collections.abc import MutableMapping
from contextlib import contextmanager
import datetime
import sys
import time


"""Global dictionary for dumping simple debugging info."""
_GLOBAL_DEBUG_DICT = {}

"""Global time variable, for use with print_time_elapsed."""
_GLOBAL_TIME = None


def print_time_elapsed(comment, reset=False, indent=0):
    """Print comment with time elapsed since last comment, for debugging.

    Args:
        comment (str): comment to print.
        reset (bool): if True, reset global time var and don't print it.
        indent (int): indent by this many tabs.
    """
    new_time = time.time()
    global _GLOBAL_TIME
    if reset or _GLOBAL_TIME is None:
        print ("{0}{1}".format("\t" * indent, comment))
    else:
        print (
            "{0}{1} ({2})".format(
                "\t" * indent,
                comment,
                new_time - _GLOBAL_TIME,
            )
        )
    _GLOBAL_TIME = new_time


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


def print_dict(dict_, indent=0, key_ordering=None, start_message=None):
    """A nice way of printing a nested dictionary.

    Args:
        dict_ (dict): dict to print.
        indent (int): number of tabs to indent with.
        key_ordering (list or None): list of keys in a given order, if wanted.
        start_message (str or None): string to print before dict.
    """
    if start_message is not None:
        print (start_message)

    if key_ordering is not None:
        for key in key_ordering:
            if key in dict_:
                value = dict_[key]
                if isinstance(value, MutableMapping):
                    print("{0}{1}:".format("\t"*indent, key))
                    print_dict(
                        value,
                        indent=indent+1,
                        key_ordering=key_ordering,
                    )
                else:
                    print("{0}{1}: {2}".format("\t"*indent, key, value))

    for key, value in dict_.items():
        if key_ordering is not None and key in key_ordering:
            continue
        if isinstance(value, MutableMapping):
            print("{0}{1}:".format("\t"*indent, key))
            print_dict(value, indent=indent+1, key_ordering=key_ordering)
        else:
            print("{0}{1}: {2}".format("\t"*indent, key, value))


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


def fallback_value(*fallbacks):
    """Simple function to return first non-None value in a list of fallbacks.

    Args:
        *fallbacks (variant): values to loop through to find the first one
            that isn't None.

    Returns:
        (variant or None): first non-None value in a list of fallbacks, if
            one exists.
    """
    for v in fallbacks:
        if v is not None:
            return v
    return None


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


def setdefault_not_none(dict_, key, default):
    """Return dict value at key, setting as default if not set or None.

    This is the same as the setdefault method on dicts, except that if the
    value at the given key is None this method treats it as if the dict is
    not set at that key, and replaces the value with the default.

    Args:
        dict_ (dict): dict to get value from (and set value if needed).
        key (variant): key of dict to get value at (and set if needed).
        default (variant): default value to set if dict is None at key.

    Returns:
        (variant): value at that key.
    """
    if dict_.get(key) is None:
        dict_[key] = default
    return dict_[key]


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
