"""Filter edits to create and modify filters."""

from collections import OrderedDict

from ._core_edits import CompositeEdit
from ._container_edit import DictEdit, ContainerOp


class AddFilterEdit(DictEdit):
    """Add filter to filterer."""
    def __init__(self, filterer, filter_type, filter_):
        """Initialise edit.

        Args:
            filterer (Filterer): filterer object for storing filters.
            filter_type (str): type of filter to add.
            filter_ (BaseFilter): filter to add.
        """
        filter_dict = filterer.get_filters(filter_type)
        if  (filter_dict is None
                or filter_.name is None
                or filter_.name in filter_dict):
            super(AddFilterEdit, self).__init__({}, {}, ContainerOp.ADD)
            self._is_valid = False
            return
        super(AddFilterEdit, self).__init__(
            filter_dict,
            OrderedDict([(filter_.name, filter_)]),
            ContainerOp.ADD,
        )
        self._callback_args = self._undo_callback_args = [filter_]
        self._name = "AddFilter ({0})".format(filter_.name)
        self._description = "Add filter '{0}' to filterer".format(filter_.name)


class RemoveFilterEdit(DictEdit):
    """Remove filter from filterer."""
    def __init__(self, filterer, filter_type, filter_name):
        """Initialise edit.

        Args:
            filterer (Filterer): filterer object for storing filters.
            filter_type (str): type of filter we're removing.
            filter_name (str): name of filter to remove.
        """
        filter_dict = filterer.get_filters(filter_type)
        if  (filter_dict is None
                or filter_name is None
                or filter_name not in filter_dict):
            super(RemoveFilterEdit, self).__init__({}, {}, ContainerOp.REMOVE)
            self._is_valid = False
            return
        super(RemoveFilterEdit, self).__init__(
            filter_dict,
            OrderedDict([(filter_name, None)]),
            ContainerOp.REMOVE,
        )
        filter_ = filter_dict[filter_name]
        self._callback_args = self._undo_callback_args = [filter_]
        self._name = "RemoveFilter ({0})".format(filter_name)
        self._description = "Remove filter '{0}' from filterer".format(
            filter_name
        )


class ModifyFilterEdit(CompositeEdit):
    """Add filter to filterer."""
    def __init__(self, filterer, filter_type, old_name, modified_filter):
        """Initialise edit.

        Args:
            filterer (Filterer): filterer object for storing filters.
            filter_type (str): type of filter to add.
            filter_ (BaseFilter): filter to add.
        """
        filter_dict = filterer.get_filters(filter_type)
        modified_name = modified_filter.name
        if  (filter_dict is None or
                old_name not in filter_dict or
                modified_name is None or
                (modified_name in filter_dict and modified_name != old_name)):
            super(AddFilterEdit, self).__init__([])
            self._is_valid = False
            return
        rename_edit = DictEdit(
            filter_dict,
            OrderedDict([(old_name, modified_name)]),
            ContainerOp.RENAME,
        )
        modify_edit = DictEdit(
            filter_dict,
            OrderedDict([(modified_name, modified_filter)]),
            ContainerOp.MODIFY,
        )
        super(ModifyFilterEdit, self).__init__([rename_edit, modify_edit])
        old_filter = filter_dict.get(old_name)
        self._callback_args = [old_filter, modified_filter]
        self._undo_callback_args = [modified_filter, old_filter]
        self._name = "ModifyFilter ({0})".format(old_name)
        self._description = "Modify filter ({0} --> {1})".format(
            old_name,
            modified_name,
        )
