"""Filter edits to create and modify filters."""

from collections import OrderedDict

from ._base_edit import EditError
from ._core_edits import CompositeEdit
from ._container_edit import ContainerOp, DictEdit, ListEdit

from scheduler.api.utils import fallback_value


# TODO: this should probably have a check that the added filter_ has
# a type that matches the filter_type arg
class AddFilterEdit(DictEdit):
    """Add filter to filterer."""
    def __init__(self, filterer, filter_type, filter_path, filter_):
        """Initialise edit.

        Args:
            filterer (Filterer): filterer object for storing filters.
            filter_type (FilterType): type of filter to add.
            filter_path (list(str)): path to filter, including name.
                This must match the filter_.name property.
            filter_ (BaseFilter): filter to add.
        """
        filter_type_dict = filterer.get_filters_dict(filter_type)
        if  (filter_type_dict is None
                or len(filter_path) == 0
                or filter_.name != filter_path[-1]):
            super(AddFilterEdit, self).__init__({}, {}, ContainerOp.ADD)
            self._is_valid = False
            return

        value = filter_
        for path_segment in reversed(filter_path):
            diff_dict = OrderedDict()
            diff_dict[path_segment] = value
            value = diff_dict

        super(AddFilterEdit, self).__init__(
            filter_type_dict,
            diff_dict,
            ContainerOp.ADD,
            recursive=True,
        )
        self._callback_args = self._undo_callback_args = [filter_]
        self._name = "AddFilter ({0})".format(filter_.name)
        self._description = "Add filter '{0}' to filterer".format(
            "/".join(filter_path)
        )


class RemoveFilterEdit(DictEdit):
    """Remove filter from filterer."""
    def __init__(self, filterer, filter_type, filter_path):
        """Initialise edit.

        Args:
            filterer (Filterer): filterer object for storing filters.
            filter_type (FilterType): type of filter we're removing.
            filter_path (list(str)): path to filter, including name.
        """
        filter_type_dict = filterer.get_filters_dict(filter_type)
        if  filter_type_dict is None or len(filter_path) == 0:
            super(RemoveFilterEdit, self).__init__({}, {}, ContainerOp.REMOVE)
            self._is_valid = False
            return

        value = None
        for path_segment in reversed(filter_path):
            diff_dict = OrderedDict()
            diff_dict[path_segment] = value
            value = diff_dict

        super(RemoveFilterEdit, self).__init__(
            filter_type_dict,
            diff_dict,
            ContainerOp.REMOVE,
            recursive=True,
        )
        filter_ = filterer.get_filter(filter_type, filter_path)
        self._callback_args = self._undo_callback_args = [filter_]
        self._name = "RemoveFilter ({0})".format(filter_.name)
        self._description = "Remove filter '{0}' from filterer".format(
            "/".join(filter_path)
        )


class ModifyFilterEdit(CompositeEdit):
    """Modify filter in filterer."""
    def __init__(
            self,
            filterer,
            old_filter_type,
            old_filter_path,
            modified_filter,
            new_filter_type=None,
            new_filter_path=None):
        """Initialise edit.

        Args:
            filterer (Filterer): filterer object for storing filters.
            filter_type (FilterType): type of filter to modify.
            old_filter_path (list(str)): old path to filter, including name.
            modified_filter (BaseFilter): filter after modification.
            new_filter_type (FilterType or None): new filter type, if changed.
            new_filter_path (list(str) or None): new path to filter, if
                changed (note that a change of name doesn't require a new
                filter path, so long as the rest of the path is unchanged).
        """
        old_filter_dict = filterer.get_filters_dict(
            old_filter_type,
            old_filter_path,
        )
        modified_name = modified_filter.name

        # edit is invalid if old_ vars are inaccurate
        if  (old_filter_dict is None
                or len(old_filter_path) == 0
                or old_filter_path[-1] not in old_filter_dict):
            super(ModifyFilterEdit, self).__init__([])
            self._is_valid = False
            return

        old_name = old_filter_path[-1]
        old_filter = old_filter_dict.get(old_name)
        new_filter_type = fallback_value(new_filter_type, old_filter_type)
        new_filter_path = fallback_value(new_filter_path, old_filter_path)

        # case 1: need to change path
        if (new_filter_type != old_filter_type
                or new_filter_path != old_filter_path):

            if new_filter_path[-1] != modified_name:
                new_filter_path = new_filter_path[:]
                new_filter_path[-1] = modified_name
            if filterer.get_filter(new_filter_path) is not None:
                super(ModifyFilterEdit, self).__init__([])
                self._is_valid = False
                return
            remove_edit = DictEdit.create_unregistered(
                old_filter_dict,
                {old_name: None},
                ContainerOp.REMOVE,
            )

            filter_type_dict = filterer.get_filters_dict(new_filter_type)
            value = modified_filter
            for path_segment in reversed(new_filter_path):
                diff_dict = OrderedDict()
                diff_dict[path_segment] = value
                value = diff_dict
            add_edit = AddFilterEdit.create_unregistered(
                filter_type_dict,
                diff_dict,
                ContainerOp.ADD,
                recursive=True,
            )
            super(ModifyFilterEdit, self).__init__([remove_edit, add_edit])

        # case 2: path stays the same (except maybe name)
        else:
            subedits = []
            if modified_name != old_name:
                if modified_name in old_filter_dict:
                    super(ModifyFilterEdit, self).__init__([])
                    self._is_valid = False
                    return
                rename_edit = DictEdit.create_unregistered(
                    old_filter_dict,
                    OrderedDict([(old_name, modified_name)]),
                    ContainerOp.RENAME,
                )
                subedits.append(rename_edit)
            modify_edit = DictEdit.create_unregistered(
                old_filter_dict,
                OrderedDict([(modified_name, modified_filter)]),
                ContainerOp.MODIFY,
            )
            subedits.append(modify_edit)
            super(ModifyFilterEdit, self).__init__(subedits)

        self._callback_args = [old_filter, modified_filter]
        self._undo_callback_args = [modified_filter, old_filter]
        self._name = "ModifyFilter ({0})".format(old_name)
        self._description = "Modify filter ({0} --> {1})".format(
            "{0}/{1}".format(old_filter_type, "/".join(old_filter_path)),
            "{0}/{1}".format(new_filter_type, "/".join(new_filter_path)),
        )


class ModifyFilterPinEdit(CompositeEdit):
    """Edit to pin or unpin a filter."""
    def __init__(
            self,
            filterer,
            filter_name,
            filter_type,
            unpin=False):
        """Initialise edit.

        Args:
            filterer (Filterer): filterer object for storing filters.
            filter_name (str): name of filter we're pinning.
            filter_type (FilterType or None): type of filter to pin as. Note
                that this isn't necessarily required to be the FilterType of
                the filter (ie. we can pin a global filter just to the tree
                filter pinlist and not to global filter pinlist)
            unpin (bool): if True, we're unpinning this filter.
        """
        filter_dict = filterer.get_filters_dict(filter_type)
        filter_ = filter_dict.get(filter_name)
        pinned_filters_list = filterer.get_pinned_filters(filter_type)
        if (filter_ is None
                or (not unpin and filter_ in pinned_filters_list)
                or (unpin and filter_ not in pinned_filters_list)):
            super(ModifyFilterPinEdit, self).__init__([])
            self._is_valid = False
            return

        # remove filter from all pin lists
        subedits = []
        for pin_list in list(filterer._pinned_filters.values()):
            if filter_ in pin_list:
                remove_edit = ListEdit.create_unregistered(
                    pin_list,
                    [filter_],
                    ContainerOp.REMOVE,
                )
                subedits.append(remove_edit)

        # add filter to new pinned list
        if not unpin:
            add_edit = ListEdit.create_unregistered(
                pinned_filters_list,
                [filter_],
                ContainerOp.ADD,
            )
            subedits.append(add_edit)

        super(ModifyFilterPinEdit, self).__init__(subedits)
        self._callback_args = self._undo_callback_args = [filter_]
        pin_type = "Unpin" if unpin else "Pin"
        self._name = "{0}Filter ({1})".format(pin_type, filter_name)
        self._description = "{0} filter '{1}' {2} {3} pin list".format(
            pin_type,
            filter_name,
            "from" if unpin else "to",
            filter_type,
        )
        self._callback_args = self._undo_callback_args = [filter_]
