"""Utility functions for scheduler api."""

import sys


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
