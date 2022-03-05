"""Exceptions for tree classes."""


class TreeError(Exception):
    """Base tree exception for others to inherit from."""


class ChildNameError(TreeError):
    """Exception for when replacing child with another with different name."""
    pass


class DuplicateChildNameError(TreeError):
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


class MultipleParentsError(TreeError):
    """Exception for when new child does not have current item as a parent."""
    pass


class TaskFileError(TreeError):
    """Exception for when the tasks file / directory missing or unreadable."""
    pass


class UnallowedChildType(TreeError):
    """Exception for trying to add a child of an unallowed type to a tree."""
    def __init__(self, tree_class, child_tree_class):
        """Initialise exception.

        Args:
            tree_class (class): class of tree we're adding child to.
            child_tree_class (class): class of child we're trying to add.
        """
        message = "tree class {0} does not allow children of type {1}".format(
            str(tree_class), str(child_tree_class)
        )
        super(UnallowedChildType, self).__init__(message)
