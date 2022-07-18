"""Util functions for dealing with serializable file and directory paths."""

import os


class SerializationError(Exception):
    """Exception class for serialization errors."""


def is_serialize_directory(directory_path, marker_file_name):
    """Check if directory path represents a serialized item.

    Args:
        directory_path (str): path to directory we want to write.
        marker_file_name (str): name of marker file (this is a file
            that marks out a directory as being a serializable item).

    Returns:
        (bool): whether or not directory path represents a serialized item.
    """
    if os.path.isdir(directory_path):
        marker_file = os.path.join(
            directory_path,
            marker_file_name,
        )
        if os.path.isfile(marker_file):
            return True
    return False


def check_directory_can_be_written_to(
        directory_path,
        marker_file,
        raise_error=True):
    """Check if directory path can be written to.

    A directory path can have a serializable class written to it so long
    as the following criteria are met:
        - the path's parent directory exists.
        - the path is not a file.
        - the path either doesn't currently exist, or it exists and is
            already a serialized directory, so can be overwritten.

    Args:
        directory_path (str): path to directory we want to write.
        marker_file (str): name of marker file (this is a file that marks
            out a directory as being a serializable item).
        raise_error (bool): if True, raise error on failure.

    Raises:
        (SerializationError): if directory can't be written to and
            raise_error flag is on.

    Returns:
        (bool): whether or not directory path can be written to.
    """
    if not os.path.isdir(os.path.dirname(directory_path)):
        if raise_error:
            raise SerializationError(
                "Directory {0} has no parent dir and so cannot "
                "be created".format(directory_path)
            )
        return False
    if os.path.isfile(directory_path):
        if raise_error:
            raise SerializationError(
                "{0} is a file, not a directory".format(directory_path)
            )
        return False
    if (marker_file and
            os.path.exists(directory_path) and
            not is_serialize_directory(directory_path, marker_file)):
        if raise_error:
            raise SerializationError(
                "Directory {0} already exists and is not a serialized "
                "directory - cannot overwrite".format(directory_path)
            )
        return False
    return True
