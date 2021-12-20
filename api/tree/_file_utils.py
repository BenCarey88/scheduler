"""Utility functions for tree classes."""

import os

from .exceptions import TaskFileError


def is_tree_directory(directory_path, tree_marker_file_name):
    """Check if directory path represents a tree item.

    Args:
        directory_path (str): path to directory we want to write.
        tree_marker_file_name (str): name of tree marker file (this is a file
            that marks out a directory as being a tree item).

    Returns:
        (bool): whether or not directory path represents a tree item.
    """
    if os.path.isdir(directory_path):
        tree_marker_file = os.path.join(
            directory_path,
            tree_marker_file_name
        )
        if os.path.isfile(tree_marker_file):
            return True
    return False


def check_directory_can_be_written_to(
        directory_path,
        tree_marker_file,
        raise_error=True):
    """Check if directory path can have a tree item written to it.

    A directory path can have a tree item written to it so long as the
    following criteria are met:
        - its parent directory exists.
        - it is not a file.
        - it either doesn't currently exist, or it exists and is already
            a tree item directory, so can be overwritten.

    Args:
        directory_path (str): path to directory we want to write.
        tree_file_marker (str): name of tree marker file (this is a file
            that marks out this directory as being a tree item).
        raise_errors (str): if True, raise errors on a failure.

    Raises:
        (TreeFileError): if directory can't be written to and raise_error
            is True.

    Returns:
        (bool): whether or not directory path can be written to.
    """
    if not os.path.isdir(os.path.dirname(directory_path)):
        if raise_error:
            raise TaskFileError(
                "Directory {0} has no parent dir and so cannot "
                "be created".format(directory_path)
            )
        return False
    if os.path.isfile(directory_path):
        if raise_error:
            raise TaskFileError(
                "Directory {0} is a file".format(
                    directory_path
                )
            )
        return False
    if (os.path.exists(directory_path) and
            not is_tree_directory(directory_path, tree_marker_file)):
        if raise_error:
            raise TaskFileError(
                "Directory {0} already exists and is not a tree "
                "directory - cannot overwrite".format(directory_path)
            )
        return False
    return True
