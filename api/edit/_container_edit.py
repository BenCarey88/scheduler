"""Ordered dict edits to be registered in the edit log."""

from collections import OrderedDict
from re import I

from scheduler.api import utils
from ._base_edit import BaseEdit, EditError
from ._core_edits import CompositeEdit


class ContainerOp(object):
    """Enum representing an edit operation on a container."""
    ADD = "Add"
    INSERT = "Insert"
    REMOVE = "Remove"
    RENAME = "Rename"
    MODIFY = "Modify"
    MOVE = "Move"
    SORT = "Sort"
    ADD_OR_MODIFY = "Add_Or_Modify"
    REMOVE_OR_MODIFY = "Remove_Or_Modify"

    _INVERSES = {
        ADD: REMOVE,
        INSERT: REMOVE,
        REMOVE: INSERT,
        RENAME: RENAME,
        MODIFY: MODIFY,
        MOVE: MOVE,
        SORT: SORT,
        ADD_OR_MODIFY: REMOVE_OR_MODIFY,
        REMOVE_OR_MODIFY: ADD_OR_MODIFY,
    }

    @classmethod
    def get_inverse_op(cls, op_type):
        """Get inverse operation of given operation.

        Args:
            op_type (ContainerOp): operation type.

        Returns:
            (ContainerOp): inverse operation type.
        """
        return cls._INVERSES.get(op_type)


class ContainerEditFlag(object):
    """Enum representing flags for container edits.

    Flag types:
        LIST_FIND_BY_VALUE: if set, list edits will use values rather than
            indexes to find items. This means that edits that remove, move
            and modify edits will take in values in place of indexes and
            apply the edit to the first instance of that value they find
            in the list (so any repeats will only be applied once).
    """
    LIST_FIND_BY_VALUE = "List_Find_By_Value"


class BaseContainerEdit(BaseEdit):
    """Edit on a container type (dict, OrderedDict or list)."""
    def __init__(
            self,
            container,
            diff_container,
            op_type,
            recursive=False,
            edit_flags=None):
        """Initialise edit item.

        Args:
            container (list or dict): the container that this edit is being
                run on.
            diff_container (list or dict): a container representing
                modifications to the original container dict. How to interpret
                this depends on the operation type.
            operation_type (ContainerOp): The type of edit operation to do.
            recrsive (bool): if this is True, the diff_container will be
                applied recursively: ie. if the values in the diff_container
                are further containers, whose keys/values correspond to keys
                and values at the same level in the diff container, we can go
                down a level and apply the edit operation there. Interpretation
                depends on op_type.
            edit_flags (list(ContainerEditFlag)): list of edit flags to use in
                edit.

        diff_dict formats:
            ADD:    {new_key: new_value}          - add new values at new keys
            INSERT: {new_key: (index, new_value)} - insert key, value at index
            REMOVE: {old_key: None}               - remove given keys
            RENAME: {old_key: new_key}            - rename given keys
            MODIFY: {old_key: new_value}          - add new values at old keys
            MOVE:   {old_key: new_index}          - move key to given index

            ADD_OR_MODIFY    {key: value}         - add/change value at keys
            REMOVE_OR_MODIFY {key: value or None} - remove/change value at keys

        diff_list formats:
            ADD:    [new_item]               - append new item
            INSERT: [(index, new_item)]      - insert new item at index
            REMOVE: [item/index]             - remove item/item at given index
            MODIFY: [(item/index, new_item)] - change item to new_item
            MOVE:   [(item/index, new_index)] - move item to new index
            SORT:   [(key, reverse)]         - sort list by given key

        recursive diff_dicts:
            ADD:    if key already exists, check next level and retry
            INSERT: if key already exists, check next level and retry
            REMOVE: only remove keys from lowest levels
            RENAME: only rename keys from lowest levels
            MODIFY: only modify the lowest level key that matches key in the
                    ordered_dict
            MOVE:   only move keys from lowest levels

            All these cases are covered by the _recursion_required method.

        recursive diff_list:
            Not really tested yet, be cautious with this.
        """
        self._container = container
        self._container_type = type(container)
        self._diff_container = diff_container
        self._operation_type = op_type
        self._edit_flags = edit_flags or []
        self._recursive = recursive
        self._inverse_diff_container = None
        self._inverse_operation_type = ContainerOp.get_inverse_op(op_type)
        super(BaseContainerEdit, self).__init__()
        self._is_valid = self._check_validity()

    def _check_validity(self):
        """Check if edit is valid.

        Returns:
            (bool): whether or not edit is valid.
        """
        if isinstance(self._container, list):
            if self._operation_type == ContainerOp.ADD:
                return True

            elif self._operation_type == ContainerOp.INSERT:
                return any([
                    0 <= index <= len(self._container)
                    for (index, _) in self._diff_container
                ])

            elif self._operation_type == ContainerOp.REMOVE:
                if ContainerEditFlag.LIST_FIND_BY_VALUE in self._edit_flags:
                    return any ([
                        value in self._container
                        for value in self._diff_container
                    ])
                else:
                    return any(
                        0 <= index < len(self._container)
                        for index in self._diff_container
                    )

            elif (self._operation_type
                    in [ContainerOp.MODIFY, ContainerOp.MOVE]):
                if ContainerEditFlag.LIST_FIND_BY_VALUE in self._edit_flags:
                    return any ([
                        value in self._container
                        for (value, _) in self._diff_container
                    ])
                else:
                    return any(
                        0 <= index < len(self._container)
                        for (index, _) in self._diff_container
                    )

            elif self._operation_type == ContainerOp.SORT:
                return any([
                    sorted(
                        self._container,
                        key=key,
                        reverse=reverse,
                    ) != self._container
                    for (key, reverse) in self._diff_container
                ])

        elif isinstance(self._container, dict):
            if self._operation_type == ContainerOp.ADD:
                return any([
                    key not in self._container for key in self._diff_container
                ])

            elif self._operation_type == ContainerOp.INSERT:
                return any([
                    key not in self._container
                    and 0 <= index <= len(self._container)
                    for key, (index, _) in self._diff_container.items()
                ])

            elif self._operation_type in [ContainerOp.REMOVE, ContainerOp.MODIFY]:
                return any([
                    key in self._container for key in self._diff_container
                ])

            elif self._operation_type == ContainerOp.RENAME:
                return any([
                    key in self._container and new_key not in self._container
                    for key, new_key in self._diff_container.items()
                ])

            elif self._operation_type in (
                    [ContainerOp.ADD_OR_MODIFY, ContainerOp.REMOVE_OR_MODIFY]):
                return True

            elif isinstance(self._container, OrderedDict):
                if self._operation_type == ContainerOp.MOVE:
                    return any([
                        key in self._container 
                        and 0 <= index < len(self._container)
                        for key, index in self._diff_container.items()
                    ])

        raise EditError(
            "Invalid container edit of type {0} with container of type {1}"
            "".format(self._operation_type, type(self._container).__name__)
        )

    def _get_operation_method(self, container, operation_type):
        """Get the method required for an operation, based on the container.

        Args:
            container (dict or list): container we're doing the operation on.
            operation_type (ContainerOp): operation type of container.

        Returns:
            (function): method required for this operation type.
        """
        if isinstance(container, list):
            if operation_type == ContainerOp.ADD:
                return self._list_add
            if operation_type == ContainerOp.INSERT:
                return self._list_insert
            if operation_type == ContainerOp.REMOVE:
                return self._list_remove
            if operation_type == ContainerOp.MODIFY:
                return self._list_modify
            if operation_type == ContainerOp.MOVE:
                return self._list_move
            if operation_type == ContainerOp.SORT:
                return self._list_sort

        elif isinstance(container, dict):
            if operation_type == ContainerOp.ADD:
                return self._dict_add
            if operation_type == ContainerOp.INSERT:
                return self._dict_insert
            if operation_type == ContainerOp.REMOVE:
                return self._dict_remove
            if operation_type == ContainerOp.RENAME:
                return self._dict_rename
            if operation_type == ContainerOp.MODIFY:
                return self._dict_modify
            if operation_type == ContainerOp.ADD_OR_MODIFY:
                return self._dict_add_or_modify
            if operation_type == ContainerOp.REMOVE_OR_MODIFY:
                return self._dict_remove_or_modify

            if isinstance(container, OrderedDict):
                if operation_type == ContainerOp.MOVE:
                    return self._ordered_dict_move

        raise EditError(
            "Cannot run container edit of type {0} with container of type "
            "{1}".format(operation_type, type(container).__name__)
        )

    def _run(self):
        """Run this edit on the given container.

        The first time this is called it should also fill up the inverse
        diff container too, so that we can use it in _inverse_run. It
        will also determine whether or not the edit is in fact valid.
        """
        if self._inverse_diff_container is None:
            self._inverse_diff_container = self._container_type()
            self._run_operation(
                self._container,
                self._diff_container,
                self._operation_type,
                self._inverse_diff_container,
            )
        else:
            self._run_operation(
                self._container,
                self._diff_container,
                self._operation_type,
            )

    def _inverse_run(self):
        """Run inverse operation to undo edit.

        Raises:
            (EditError): if the edit has not yet been run so the diff dict
                hasn't been filled up.
        """
        if self._inverse_diff_container is None:
            raise EditError(
                "Can only call ContainerEdit _inverse_run once _run has "
                "been called."
            )
        self._run_operation(
            self._container,
            self._inverse_diff_container,
            self._inverse_operation_type,
        )

    def _recursion_required(self, key_or_index, container, diff_container):
        """Utility to check if we should apply an operation recursively.

        If self._recursive=True, and the values at a given key/index of both
        the container and the diff container are nested containers then we
        should apply recursively.

        Args:
            key_or_index (variant): key to check dictionaries at, or index
                to check lists at.
            container (dict or list): container that's being edited.
            diff_container (dict or list): diff_container used to edit it.

        Returns:
            (bool): whether or not we should use recursion.
        """
        if not self._recursive:
            return False

        if isinstance(container, dict):
            subcontainer = diff_container.get(key_or_index)
            if not isinstance(subcontainer, (dict, list)):
                return False
            if not isinstance(container.get(key_or_index), type(subcontainer)):
                return False

        elif isinstance(container, list):
            if len(diff_container) != len(container):
                return False
            if (len(container) < key_or_index
                    or len(diff_container) < key_or_index):
                return False
            subcontainer = diff_container[key_or_index]
            if not isinstance(subcontainer, (dict, list)):
                return False
            if not isinstance(container[key_or_index], type(subcontainer)):
                return False

        return True

    @staticmethod
    def iter_container(container):
        """Convenience method to iterate through either a dictionary or a list.

        Args:
            container(dict or list): container to iterate through.

        Yields:
            (int or variant): key of dict item or index of list item.
            (variant): dict value or list item.
        """
        if isinstance(container, dict):
            for key, value in container.items():
                yield key, value
        elif isinstance(container, list):
            for index, item in enumerate(container):
                yield index, item

    @staticmethod
    def _add_inverse_diff_dict_key(inverse_diff_dict, key, value):
        """Add key, value to inverse diff container.

        Note that in ordered dict, inverse diff items are added at start
        so that they're applied in reverse order from the forwards diff.

        Args:
            inverse_diff_dict (dict): inverse diff dict.
            key (variant): key to add to dict.
            value (variant): value to add at key.
        """
        if isinstance(inverse_diff_dict, OrderedDict):
            utils.add_key_at_start(inverse_diff_dict, key, value)
        else:
            inverse_diff_dict[key] = value

    def _run_operation(
            self,
            container,
            diff_container,
            operation_type,
            inverse_diff_container=None):
        """Run operation on a container.

        Loop through the container and check if there are nested diff
        containers that we should run this function recursively with,
        otherwise call methods to apply the edit operation on that key.

        Args:
            container (dict or list): dictionary to run on.
            diff_container (dict or list): dictionary of modifications to make.
            op_type (ContainerOp): type of operation to run.
            inverse_diff_container (dict, list or None): if given, use this to
                build up the inverse operation.

        Returns:
            (bool): whether or not edit is valid ie. whether or not edit
                actually modifies container. Note that this return value is
                currently not used for anything, since we now calculate
                is_valid during edit init, but may well deprecate in future.
        """
        is_valid = False
        # note that in the case of lists, key is an index here
        for key, value in self.iter_container(diff_container):
            # call recursively if needed
            if self._recursion_required(key, container, diff_container):
                if inverse_diff_container is not None:
                    # in ordered containers, add inverse diff items at start
                    inverse_diff_subcontainer = type(value)()
                    if isinstance(value, list):
                        inverse_diff_container.insert(
                            0,
                            inverse_diff_subcontainer
                        )
                    elif isinstance(value, dict):
                        self._add_inverse_diff_dict_key(
                            inverse_diff_container,
                            key,
                            inverse_diff_subcontainer
                        )
                    is_valid = self._run_operation(
                        container[key],
                        value,
                        operation_type,
                        inverse_diff_subcontainer,
                    ) or is_valid

            # otherwise call specific operarion method
            else:
                operation_method = self._get_operation_method(
                    container,
                    operation_type
                )
                if isinstance(container, dict):
                    is_valid = operation_method(
                        key,
                        value,
                        container,
                        inverse_diff_container
                    ) or is_valid
                elif isinstance(container, list):
                    is_valid = operation_method(
                        value,
                        container,
                        inverse_diff_container
                    ) or is_valid

        return is_valid

    ### Dict Operation Methods ###
    def _dict_add(self, key, value, dict_, inverse_diff_dict=None):
        """Add given key, value to dict.

        Args:
            key (variant): key to add.
            value (variant): value to set at key.
            dict_ (dict): dict to add key to.
            inverse_diff_dict (dict or None): if given, add to this to
                define inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if key not in dict_:
            if inverse_diff_dict is not None:
                self._add_inverse_diff_dict_key(inverse_diff_dict, key, None)
            dict_[key] = value
            return True
        return False

    def _dict_insert(
            self,
            key,
            value_tuple,
            dict_,
            inverse_diff_dict=None):
        """Insert given key, value to dict.

        Args:
            key (variant): key to insert.
            value_tuple (tuple(int, variant)): tuple of index to add new key at
                and value to set for key. The index defines the index that we
                want the key to have after being inserted.
            dict_ (dict): dict to insert key into. If this isn't ordered, we
                ignore the index and treat this as an ADD edit.
            inverse_diff_dict (dict or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if not isinstance(value_tuple, tuple) or len(value_tuple) != 2:
            raise EditError("diff_dict for INSERT op needs 2-tuple values")
        if not isinstance(dict_, OrderedDict):
            return self._dict_add(
                key,
                value_tuple[1],
                dict_,
                inverse_diff_dict
            )

        if key not in dict_:
            index = value_tuple[0]
            if index < 0 or index > len(dict_):
                return False
            new_value = value_tuple[1]
            if index == len(dict_):
                dict_[key] = new_value
            else:
                for i in range(len(dict_)):
                    k, v = dict_.popitem(last=False)
                    if index == i:
                        dict_[key] = new_value
                    dict_[k] = v
            if inverse_diff_dict is not None:
                self._add_inverse_diff_dict_key(inverse_diff_dict, key, None)
            return True
        return False

    def _dict_remove(self, key, _, dict_, inverse_diff_dict=None):
        """Remove given key from dict.

        Args:
            key (variant): key to remove.
            _ (variant): value at key, passed for neatness so args match other
                functions, but this is unused (and should be None).
            dict_ (dict): ordered dict to remove key from.
            inverse_diff_dict (dict or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if key in dict_:
            if inverse_diff_dict is not None:
                index = list(dict_.keys()).index(key)
                self._add_inverse_diff_dict_key(
                    inverse_diff_dict,
                    key,
                    (index, dict_[key])
                )
            del dict_[key]
            return True
        return False

    def _dict_rename(self, key, new_key, dict_, inverse_diff_dict=None):
        """Rename given key in dict.

        Args:
            key (variant): key to rename.
            new_key (variant): new name of key.
            dict_ (dict): dict whose key we're renaming.
            inverse_diff_dict (dict or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if key in dict_:
            if isinstance(dict_, OrderedDict):
                for i in range(len(dict_)):
                    k, v = dict_.popitem(last=False)
                    if k == key:
                        dict_[new_key] = v
                    else:
                        dict_[k] = v
            else:
                dict_[new_key] = dict_[key]
                del dict_[key]
            if inverse_diff_dict is not None:
                self._add_inverse_diff_dict_key(
                    inverse_diff_dict,
                    new_key,
                    key
                )
            return True
        return False

    def _dict_modify(self, key, new_value, dict_, inverse_diff_dict=None):
        """Modify given key to new value in dict.

        Args:
            key (variant): key to modify.
            new_value (variant): new value for key.
            dict_ (dict): dict whose key we're modifying.
            inverse_diff_dict (dict or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if key in dict_:
            if inverse_diff_dict is not None:
                self._add_inverse_diff_dict_key(
                    inverse_diff_dict,
                    key,
                    dict_[key]
                )
            dict_[key] = new_value
            return True
        return False

    # TODO: add some tests for these composite ones, haven't considered all
    # cases so I don't know if could hit some issues with the inverses for
    # certain recursive scenarios - but seems to work for task history :)
    def _dict_add_or_modify(self, key, value, dict_, inverse_diff_dict=None):
        """Add given key to dict if doesn't exist or modify existing key.

        Args:
            key (variant): key to add in modify.
            value (variant): value for key.
            dict_ (dict): dict we're editing.
            inverse_diff_dict (dict or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if key in dict_:
            return self._dict_modify(key, value, dict_, inverse_diff_dict)
        else:
            return self._dict_add(key, value, dict_, inverse_diff_dict)

    def _dict_remove_or_modify(
            self,
            key,
            value,
            dict_,
            inverse_diff_dict=None):
        """Remove existing key from dict if value is None, else modify key.

        Args:
            key (variant): key to add in modify.
            value (variant): value for key.
            dict_ (dict): ordered dict we're editing.
            inverse_diff_dict (dict or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if value is None:
            return self._dict_remove(key, value, dict_, inverse_diff_dict)
        else:
            return self._dict_modify(key, value, dict_, inverse_diff_dict)

    ### OrderedDict Operation Methods ###
    def _ordered_dict_move(
            self,
            key,
            index,
            ordered_dict,
            inverse_diff_dict=None):
        """Move given key to new index in ordered dict.

        Args:
            key (variant): key to move.
            index (int): new index for key. The index defines the index that we
                want the key to have after being inserted.
            dict (OrderedDict): ordered dict whose key we're moving.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if key in ordered_dict and index >= 0 and index < len(ordered_dict):
            value = ordered_dict[key]
            old_index = list(ordered_dict.keys()).index(key)
            if inverse_diff_dict is not None:
                self._add_inverse_diff_dict_key(
                    inverse_diff_dict,
                    key,
                    old_index
                )
            # first remove item from dict
            del ordered_dict[key]
            # now insert item into dict in new position
            # note that ordered_dict length has now decreased by 1
            if index == len(ordered_dict):
                ordered_dict[key] = value
            else:
                for i in range(len(ordered_dict)):
                    k, v = ordered_dict.popitem(last=False)
                    if i == index:
                        ordered_dict[key] = value
                    ordered_dict[k] = v
            return True
        return False

    ### List Operation Methods ###
    def _list_add(self, value, list_, inverse_diff_list=None):
        """Add given value to list.

        Args:
            value (variant): value to add.
            list_ (list): list to add to.
            inverse_diff_list (list or None): if given, add to this to
                define inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if inverse_diff_list is not None:
            if ContainerEditFlag.LIST_FIND_BY_VALUE in self._edit_flags:
                inverse_diff_list.insert(0, value)
            else:
                inverse_diff_list.insert(0, len(list_))
        list_.append(value)
        return True

    def _list_insert(self, value_tuple, list_, inverse_diff_list=None):
        """Insert given value to list.

        Args:
            value_tuple (tuple(int, variant)): tuple of index to add new value
                at and value to add. The index defines the index that we
                want the item to have after being inserted.
            list_ (list): list to insert into.
            inverse_diff_list (list or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if not isinstance(value_tuple, tuple) or len(value_tuple) != 2:
            raise EditError("diff list for INSERT op needs 2-tuple values")
        index, new_value = value_tuple
        if index < 0 or index > len(list_):
            return False
        list_.insert(index, new_value)
        if inverse_diff_list is not None:
            if ContainerEditFlag.LIST_FIND_BY_VALUE in self._edit_flags:
                inverse_diff_list.insert(0, new_value)
            else:
                inverse_diff_list.insert(0, index)
        return True

    def _list_remove(self, index_or_value, list_, inverse_diff_list=None):
        """Remove item from list.

        Args:
            index_or_value (int or variant): index to remove item at, or item to
                remove. Which of these has been used should be dependent on the
                whether or not the LIST_FIND_BY_VALUE flag was passed.
            list_ (list): list to remove from.
            inverse_diff_list (list or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if ContainerEditFlag.LIST_FIND_BY_VALUE in self._edit_flags:
            # Remove by value
            value = index_or_value
            if not value in list_:
                return False
            index = list_.index(value)
            list_.pop(index)
        else:
            # Remove by index
            index = index_or_value
            if not isinstance(index, int):
                raise EditError(
                    "List remove edits need index diff_list inputs. If you "
                    "wish to remove items by value, use the LIST_FIND_BY_VALUE "
                    "ContainerEditFlag."
                )
            if index < 0 or index >= len(list_):
                return False
            value = list_.pop(index)

        if inverse_diff_list is not None:
            inverse_diff_list.insert(0, (index, value))
        return True

    def _list_modify(self, value_tuple, list_, inverse_diff_list=None):
        """Modify list item at given index to new value.

        Args:
            value_tuple (tuple(int, variant)): index to modify and new value
                to set to.
            new_value (variant): new value for key.
            dict_ (dict): dict whose key we're modifying.
            inverse_diff_dict (dict or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if not isinstance(value_tuple, tuple) or len(value_tuple) != 2:
            raise EditError("diff_list for MODIFY op needs 2-tuple values")
        index, new_value = value_tuple
        if index < 0 or index >= len(list_):
            return False
        if inverse_diff_list is not None:
            inverse_diff_list.insert(0, (index, list_[index]))
        list_[index] = new_value
        return True

    def _list_move(self, index_tuple, list_, inverse_diff_list=None):
        """Move given index to new index in ordered dict.

        Args:
            index_tuple (tuple(variant, int)): old item or index of old item,
                and new index to move to.
            list_ (list): list whose items we're moving.
            inverse_diff_list (list or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if not isinstance(index_tuple, tuple) or len(index_tuple) != 2:
            raise EditError("diff list for MOVE op needs 2-tuple values")
        old_index, new_index = index_tuple
        if ContainerEditFlag.LIST_FIND_BY_VALUE in self._edit_flags:
            # in this case old_index arg is in fact the item.
            old_index = list_.index(old_index)
        if new_index == len(list_):
            # treat (new_index == len(list_)) as (new_index == len(list_) - 1)
            new_index -= 1
        for index in (old_index, new_index):
            if index < 0 or index >= len(list_):
                return False
        if inverse_diff_list is not None:
            if ContainerEditFlag.LIST_FIND_BY_VALUE in self._edit_flags:
                inverse_diff_list.insert(0, (list_[old_index], old_index))
            else:
                inverse_diff_list.insert(0, (new_index, old_index))
        list_.insert(new_index, list_.pop(old_index))
        return True

    def _list_sort(self, sort_func_tuple, list_, inverse_diff_list=None):
        """Sort list according to given tuple.

        Args:
            sort_func_tuple (tuple(function, bool)): sort key, and boolean to
                define if we're sorting in reverse order or not.
            list_ (list): list whose items we're moving.
            inverse_diff_list (list or None): if given, add to this to define
                inverse operation.

        Returns:
            (bool): whether or not container is modified.
        """
        if not isinstance(sort_func_tuple, tuple) or len(sort_func_tuple) != 2:
            raise EditError("diff list for MOVE op needs 2-tuple values")
        key, reverse = sort_func_tuple
        if inverse_diff_list is not None:
            inverse_key_dict = {item: i for i, item in enumerate(list_)}
            inverse_diff_list.insert(
                0,
                (lambda x: inverse_key_dict.get(x), False)
            )
        orig_list = list_[:]
        list_.sort(key=key, reverse=reverse)
        return (orig_list != list_)


class DictEdit(BaseContainerEdit):
    """Edit on an dictionary."""
    def __init__(
            self,
            dict_,
            diff_dict,
            op_type,
            recursive=False,
            edit_flags=None):
        """Initialise edit item.

        Args:
            dict_ (dict): the dictionary that this edit is being run on.
            diff_dict (dict): a dictionary representing modifications to a
                dict. If dict_ is ordered, this should be too. How to
                interpret this dictionary depends on the operation type.
            operation_type (ContainerOp): The type of edit operation to do.
            recrsive (bool): if this is True, the diff_dict will be applied
                recursively: ie. if the values in the diff_dict are further
                dictionaries, whose keys correspond to keys at the same level
                in the diff dict, we can go down a level and apply the edit
                operation there. Interpretation depends on op_type.
            edit_flags (list(ContainerEditFlag)): list of edit flags to use in
                edit.

        diff_dict formats:
            ADD:    {new_key: new_value}          - add new values at new keys
            INSERT: {new_key: (index, new_value)} - insert key, value at index
            REMOVE: {old_key: None}               - remove given keys
            RENAME: {old_key: new_key}            - rename given keys
            MODIFY: {old_key: new_value}          - add new values at old keys
            MOVE:   {old_key: new_index}          - move key to given index

            ADD_OR_MODIFY    {key: value}         - add/change value at keys
            REMOVE_OR_MODIFY {key: value or None} - remove/change value at keys

        recursive diff_dicts:
            ADD:    if key already exists, check next level and retry
            INSERT: if key already exists, check next level and retry
            REMOVE: only remove keys from lowest levels
            RENAME: only rename keys from lowest levels
            MODIFY: only modify the lowest level key that matches key in the
                    ordered_dict
            MOVE:   only move keys from lowest levels

            All these cases are covered by the _recursion_required method.
        """
        if not isinstance(dict_, dict):
            raise EditError("dict_ argument must be a dict")
        if type(dict_) != type(diff_dict):
            raise EditError("diff_dict and dict_ must have the same type")
        super(DictEdit, self).__init__(
            dict_,
            diff_dict,
            op_type,
            recursive=recursive,
            edit_flags=edit_flags,
        )


class ListEdit(BaseContainerEdit):
    """Edit on a list."""
    def __init__(
            self,
            list_,
            diff_list,
            op_type,
            recursive=False,
            edit_flags=None):
        """Initialise edit item.

        Args:
            list_ (list): the list that this edit is being run on.
            diff_list (list): a list representing modifications to a list.
                How to interpret this list depends on the operation type.
            operation_type (ContainerOp): The type of edit operation to do.
            recursive (bool): if this is True, the diff_list will be applied
                recursively: ie. if the values in the diff_list are further
                lists and diff_list has the same size as list_, then we can
                apply the edit operation to each of those sublists.
            edit_flags (list(ContainerEditFlag)): list of edit flags to use in
                edit.

        diff_list formats:
            ADD:    [new_item]               - append new item
            INSERT: [(index, new_item)]      - insert new item at index
            REMOVE: [index/item]             - remove item/item at given index
            MODIFY: [(index, new_item)]      - change item at index to new_item
            MOVE:   [(old_index, new_index)] - move item at index to new index
            SORT:   [(key, reverse)]         - sort list by given key, reverse

        recursive diff_list:
            Not really tested yet, be cautious with this.
        """
        if not isinstance(list_, list) or not isinstance(diff_list, list):
            raise EditError("list and diff_list arguments must be lists")
        super(ListEdit, self).__init__(
            list_,
            diff_list,
            op_type,
            recursive=recursive,
            edit_flags=edit_flags,
        )


class TimelineEdit(CompositeEdit):
    """Edit on a Timeline object."""
    def __init__(
            self,
            timeline,
            diff_dict,
            op_type):
        """Initialise edit item.

        Args:
            timeline (Timeline): the timeline that this edit is being run on.
            diff_dict (dict): a dict representing modifications to the timeline
                object. How to interpret this list depends on the operation
                type.
            operation_type (ContainerOp): The type of edit operation to do.

        diff_dict formats:
            ADD:    {time: [item]}             - add item at time
            INSERT: {time: [item]}             - insert item at time
            REMOVE: {time: [item]}             - remove item from time
            MODIFY: {time: [(item, new_item)]} - change item to new_item
            MOVE:   {time: [(item, new_time)]} - move item to new time

        Note that because Timeline containers can't have duplicate items at the
        same time then REMOVE, MODIFY, MOVE can all use item instead of index.
        """
        if op_type in (
                ContainerOp.ADD, ContainerOp.INSERT, ContainerOp.REMOVE):
            edit = BaseContainerEdit.create_unregistered(
                timeline._dict,
                diff_dict,
                op_type,
                recursive=True,
                edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
            )
            super(TimelineEdit, self).__init__([edit])

        elif op_type == ContainerOp.MODIFY:
            # convert diff list to use indexes instead of items
            modify_edit = BaseContainerEdit.create_unregistered(
                timeline._dict,
                OrderedDict([
                    (time, [(item_list.index(i1), i2) for i1, i2 in item_list])
                    for time, item_list in diff_dict.items()
                ]),
                op_type,
                recursive=True,
            )
            super(TimelineEdit, self).__init__([modify_edit])

        elif op_type == ContainerOp.MOVE:
            # remove anything that tries to move to same time
            diff_dict = OrderedDict([
                (time, [(i, t) for i, t in item_list if t != time])
                for time, item_list in diff_dict.items()
            ]),
            # remove items from current time
            remove_edit = TimelineEdit.create_unregistered(
                timeline,
                OrderedDict([
                    (time, [item for item, _ in item_list])
                    for time, item_list in diff_dict.items()
                ]),
                ContainerOp.REMOVE,
            )
            # add items to new time
            add_diff_dict = OrderedDict()
            for item_list in diff_dict.values():
                for item, time in item_list:
                    if item in timeline.get(time):
                        continue
                    diff_list = add_diff_dict[time].setdefault([])
                    if item in diff_list:
                        continue
                    diff_list.append(item)
            add_edit = TimelineEdit.create_unregistered(
                timeline,
                add_diff_dict,
                ContainerOp.ADD,
            )
            super(TimelineEdit, self).__init__(
                [remove_edit, add_edit],
            )
