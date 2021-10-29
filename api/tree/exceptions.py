"""Exceptions for tree classes."""


class DuplicateChildNameError(Exception):
    """Exception for two cildren having the same name."""
    def __init__(self, tree_item_name, child_item_name):
        """Initialise exception.

        Args:
            tree_item_name (str): name of tree item we're adding child to.
            child_item_name (str): name of child.
        """
        message = "child of {0} with name {1} already exists".format(
            tree_item_name, child_item_name
        )
        super(DuplicateChildNameError, self).__init__(message)


class MultipleParentsError(Exception):
    """Exception for when new child does not have current item as a parent."""
    pass


class TaskFileError(Exception):
    """Exception for when the tasks file / directory missing or unreadable."""
    pass
