"""Utility functions for scheduler api."""

from collections import OrderedDict
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
    modified_files = git_repo.git.diff(None, name_only=True).split("\n")
    untracked_files = git_repo.untracked_files
    for file_ in modified_files + untracked_files:
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
        return "Git error when committing changes for repo {1}:\n{2}".format(
            repo_path,
            e.stderr
        )
    try:
        git_repo.git.push()
    except git.exc.GitCommandError as e:
        return "Git error when pushing changes for repo {1}:\n{2}".format(
            repo_path,
            e.stderr
        )

    return None
