"""Ordered dict edits to be registered in the edit log."""

from collections import OrderedDict

from scheduler.api import utils

from ._base_edit import BaseEdit, EditError


class OrderedDictOp(object):
    """Enum representing an edit operation on a dictionary."""
    ADD = "Add"
    INSERT = "Insert"
    REMOVE = "Remove"
    RENAME = "Rename"
    MODIFY = "Modify"
    MOVE = "Move"
    ADD_OR_MODIFY = "Add_Or_Modify"
    REMOVE_OR_MODIFY = "Remove_Or_Modify"

    _INVERSES = {
        ADD: REMOVE,
        INSERT: REMOVE,
        REMOVE: INSERT,
        RENAME: RENAME,
        MODIFY: MODIFY,
        MOVE: MOVE,
        ADD_OR_MODIFY: REMOVE_OR_MODIFY,
        REMOVE_OR_MODIFY: ADD_OR_MODIFY,
    }

    @classmethod
    def get_inverse_op(cls, op_type):
        """Get inverse operation of given operation.

        Args:
            op_type (OrderedDictOp): operation type.

        Returns:
            (OrderedDictOp): inverse operation type.
        """
        return cls._INVERSES.get(op_type)


class BaseContainerEdit(BaseEdit):
    """Edit on a container type (dict, OrderedDict or list)."""
    def __init__(
            self,
            container,
            diff_container,
            op_type,
            recursive=False,
            register_edit=True):
        """Initialise edit item.

        Args:
            container (list or dict): the container that this edit is being
                run on.
            diff_container (list or dict): a container representing
                modifications to the original container dict. How to interpret
                this depends on the operation type.
            operation_type (OrderedDictOp): The type of edit operation to do.
            recrsive (bool): if this is True, the diff_container will be
                applied recursively: ie. if the values in the diff_container
                are further containers, whose keys/values correspond to keys
                and values at the same level in the diff container, we can go
                down a level and apply the edit operation there. Interpretation
                depends on op_type.
            register_edit (bool): whether or not to register this edit.
        """
        super(BaseContainerEdit, self).__init__(register_edit)
        self._container = container
        self._container_type = type(container)
        self._diff_container = diff_container
        self._operation_type = op_type
        self._recursive = recursive
        self._inverse_diff_container = None
        self._inverse_operation_type = OrderedDictOp.get_inverse_op(op_type)

    def _run(self):
        """Run this edit on the given container.

        The first time this is called it should also fill up the inverse
        diff container too, so that we can use it in _inverse_run.
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

        If self.recursive=True, and the values at a given key of both the
        ordered_dict and the diff_dict are nested ordered dictionaries,
        then we should apply recursively.

        Args:
            key_or_index (variant): key to check dictionaries at, or index
                to check lists at.
            container (dict or list): container that's being edited.
            diff_container (dict or list): diff_container used to edit it.

        Returns:
            (bool): whether or not we should use recursion.
        """
        if not self.recursive:
            return False

        if isinstance(container, dict):
            subcontainer_type = diff_container.get(key_or_index)
            if not isinstance(subcontainer_type, (dict, list)):
                return False
            if not isinstance(container.get(key_or_index), subcontainer_type):
                return False

        elif isinstance(container, list):
            if len(diff_container) != len(container):
                return False
            if (len(container) < key_or_index
                    or len(diff_container) < key_or_index):
                return False
            subcontainer_type = diff_container[key_or_index]
            if not isinstance(subcontainer_type, (dict, list)):
                return False
            if not isinstance(container[key_or_index], subcontainer_type):
                return False

        return True

    @staticmethod
    def _add_inverse_diff_dict_key(inverse_diff_dict, key, value):
        """Add key to inverse diff dict.

        If the dict is ordered, this is added at start.

        Args:
            inverse_diff_dict (dict): dict to add key to.
            key (variant): key to add.
            value (variant): value at key.
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
            ordered_dict (OrderedDict): dictionary to run on.
            diff_dict (OrderedDict): dictionary of modifications to make.
            op_type (OrderedDictOp): type of operation to run.
            inverse_diff_dict (OrderedDict or None): if given, use this to
                build up the inverse operation.
        """
        if isinstance(container, dict):
            for key, value in diff_container.items():
                # call recursively if needed
                if self._recursion_required(key, container, diff_container):
                    if inverse_diff_container is not None:
                        # all inverse diff keys are added at start so that they're
                        # applied in reverse order from the forwards diff
                        self._add_inverse_diff_dict_key(
                            inverse_diff_container,
                            key,
                            type(container)()
                        )
                        self._run_operation(
                            container[key],
                            diff_container[key],
                            operation_type,
                            inverse_diff_container[key],
                        )
                    else:
                        self._run_operation(
                            container[key],
                            diff_container[key],
                            operation_type,
                        )
                # otherwise call specific operarion method
                else:
                    if operation_type == OrderedDictOp.ADD:
                        self._dict_add(
                            key, value, container, inverse_diff_container
                        )
                    elif operation_type == OrderedDictOp.INSERT:
                        self._ordered_dict_insert(
                            key, value, container, inverse_diff_container
                        )
                    elif operation_type == OrderedDictOp.REMOVE:
                        self._dict_remove(
                            key, value, container, inverse_diff_container
                        )
                    elif operation_type == OrderedDictOp.RENAME:
                        self._dict_rename(
                            key, value, container, inverse_diff_container
                        )
                    elif operation_type == OrderedDictOp.MODIFY:
                        self._dict_modify(
                            key, value, container, inverse_diff_container
                        )
                    elif operation_type == OrderedDictOp.MOVE:
                        self._ordered_dict_move(
                            key, value, container, inverse_diff_container
                        )

                    elif operation_type == OrderedDictOp.ADD_OR_MODIFY:
                        self._add_or_modify(
                            key, value, container, inverse_diff_container
                        )
                    elif operation_type == OrderedDictOp.REMOVE_OR_MODIFY:
                        self._remove_or_modify(
                            key, value, container, inverse_diff_container
                        )

    # def _run_operation(
    #         self,
    #         container,
    #         diff_container,
    #         operation_type,
    #         inverse_diff_container=None):
    #     """Run operation on contatiner.

    #     Loop through the container, and check if there are nested containers
    #     that we should run this function recursively with, otherwise call
    #     methods to apply the edit operation on that key.

    #     Args:
    #         container (list or dict): container to run on.
    #         diff_container (list or dict): container of modifications to make.
    #         op_type (OrderedDictOp): type of operation to run.
    #         inverse_diff_container (list or dict or None): if given, use this
    #             to build up the inverse operation.
    #     """
    #     raise NotImplementedError(
    #         "_run_operation must be implemented in BaseContainer subclasses."
    #     )

    def _dict_add(self, key, value, dict_, inverse_diff_dict=None):
        """Add given key, value to ordered dict.

        Args:
            key (variant): key to add.
            value (variant): value to set at key.
            dict_ (dict): dict to add key to.
            inverse_diff_dict (dict or None): if given, add to this to
                define inverse operation.
        """
        if key not in dict_:
            if inverse_diff_dict is not None:
                self._add_inverse_diff_dict_key(inverse_diff_dict, key, None)
            dict_[key] = value

    def _ordered_dict_insert(
            self,
            key,
            value_tuple,
            ordered_dict,
            inverse_diff_dict=None):
        """Insert given key, value to ordered dict.

        Args:
            key (variant): key to insert.
            value_tuple (tuple(int, variant)): tuple of index to add new key at
                and value to set for key. The index defines the index that we
                want the key to have after being inserted.
            ordered_dict (OrderedDict): ordered dict to insert key into.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.
        """
        if key not in ordered_dict:
            if type(value_tuple) != tuple:
                raise EditError(
                    "diff_dict for INSERT op needs tuple valued leaves"
                )
            index = value_tuple[0]
            if index < 0 or index > len(ordered_dict):
                return
            new_value = value_tuple[1]
            if index == len(ordered_dict):
                ordered_dict[key] = new_value
            else:
                for i in range(len(ordered_dict)):
                    k, v = ordered_dict.popitem(last=False)
                    if index == i:
                        ordered_dict[key] = new_value
                    ordered_dict[k] = v
            if inverse_diff_dict is not None:
                self._add_inverse_diff_dict_key(inverse_diff_dict, key, None)




class OrderedDictEdit(BaseEdit):
    """Edit on an OrderedDict."""

    def __init__(
            self,
            ordered_dict,
            diff_dict,
            op_type,
            recursive=False,
            register_edit=True):
        """Initialise edit item.

        Args:
            ordered_dict (OrderedDict): the dictionary that this edit is being
                run on.
            diff_dict (OrderedDict): a dictionary representing modifications
                to a dict. How to interpret this dictionary depends on the
                operation type.
            operation_type (OrderedDictOp): The type of edit operation to do.
            recrsive (bool): if this is True, the diff_dict will be applied
                recursively: ie. if the values in the diff_dict are further
                dictionaries, whose keys correspond to keys at the same level
                in the diff dict, we can go down a level and apply the edit
                operation there. Interpretation depends on op_type.
            register_edit (bool): whether or not to register this edit.

        diff_dict formats:
            ADD:    {new_key: new_value}          - add new values at new keys
            INSERT: {new_key: (index, new_value)} - insert key, value at index
            REMOVE: {old_key: None}               - remove given keys
            RENAME: {old_key: new_key}            - rename given keys
            MODIFY: {old_key: new_value}          - add new values at old keys
            MOVE:   {old_key: new_index}          - move key to given index

            ADD_OR_MODIFY    {key: value}         - add new values at keys
            REMOVE_OR_MODIFY {key: value or None} - change/remove value at keys

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
        super(OrderedDictEdit, self).__init__(register_edit)
        self.ordered_dict = ordered_dict
        self.diff_dict = diff_dict
        self.operation_type = op_type
        self.recursive = recursive
        self.inverse_diff_dict = None
        self.inverse_operation_type = OrderedDictOp.get_inverse_op(op_type)

    def _run(self):
        """Run this edit on the given ordered_dict.

        The first time this is called it should also fill up the inverse
        diff dict too, so that we can use it in _inverse_run.
        """
        if self.inverse_diff_dict is None:
            self.inverse_diff_dict = OrderedDict()
            self._run_operation(
                self.ordered_dict,
                self.diff_dict,
                self.operation_type,
                self.inverse_diff_dict,
            )
        else:
            self._run_operation(
                self.ordered_dict,
                self.diff_dict,
                self.operation_type,
            )

    def _recursion_required(self, key, ordered_dict, diff_dict):
        """Utility to check if we should apply an operation recursively.

        If self.recursive=True, and the values at a given key of both the
        ordered_dict and the diff_dict are nested ordered dictionaries,
        then we should apply recursively.

        Args:
            key (variant): key to check them at.
            ordered_dict (OrderedDict): ordered_dict that's being edited.
            diff_dict (OrderedDict): diff_dict used to edit it.

        Returns:
            (bool): whether or not we should use recursion.
        """
        return (
            self.recursive
            and isinstance(ordered_dict.get(key), OrderedDict)
            and isinstance(diff_dict.get(key), OrderedDict)
        )

    # TODO: update so that this sets is_valid to true once any change is introduced
    def _run_operation(
            self,
            ordered_dict,
            diff_dict,
            operation_type,
            inverse_diff_dict=None):
        """Run operation on an ordered_dict.

        Loop through the keys and values in the diff_dict, and check if there
        are nested diff dicts that we should run this function recursively
        with, otherwise call methods to apply the edit operation on that key.

        Args:
            ordered_dict (OrderedDict): dictionary to run on.
            diff_dict (OrderedDict): dictionary of modifications to make.
            op_type (OrderedDictOp): type of operation to run.
            inverse_diff_dict (OrderedDict or None): if given, use this to
                build up the inverse operation.
        """
        for key, value in diff_dict.items():
            # call recursively if needed
            if self._recursion_required(key, ordered_dict, diff_dict):
                if inverse_diff_dict is not None:
                    # all inverse diff keys are added at start so that they're
                    # applied in reverse order from the forwards diff
                    utils.add_key_at_start(
                        inverse_diff_dict,
                        key,
                        OrderedDict()
                    )
                    self._run_operation(
                        ordered_dict[key],
                        diff_dict[key],
                        operation_type,
                        inverse_diff_dict[key],
                    )
                else:
                    self._run_operation(
                        ordered_dict[key],
                        diff_dict[key],
                        operation_type,
                    )
            # otherwise call specific operarion method
            else:
                if operation_type == OrderedDictOp.ADD:
                    self._add(key, value, ordered_dict, inverse_diff_dict)
                elif operation_type == OrderedDictOp.INSERT:
                    self._insert(key, value, ordered_dict, inverse_diff_dict)
                elif operation_type == OrderedDictOp.REMOVE:
                    self._remove(key, value, ordered_dict, inverse_diff_dict)
                elif operation_type == OrderedDictOp.RENAME:
                    self._rename(key, value, ordered_dict, inverse_diff_dict)
                elif operation_type == OrderedDictOp.MODIFY:
                    self._modify(key, value, ordered_dict, inverse_diff_dict)
                elif operation_type == OrderedDictOp.MOVE:
                    self._move(key, value, ordered_dict, inverse_diff_dict)

                elif operation_type == OrderedDictOp.ADD_OR_MODIFY:
                    self._add_or_modify(
                        key, value, ordered_dict, inverse_diff_dict
                    )
                elif operation_type == OrderedDictOp.REMOVE_OR_MODIFY:
                    self._remove_or_modify(
                        key, value, ordered_dict, inverse_diff_dict
                    )

    @staticmethod
    def _add(key, value, ordered_dict, inverse_diff_dict=None):
        """Add given key, value to ordered dict.

        Args:
            key (variant): key to add.
            value (variant): value to set at key.
            ordered_dict (OrderedDict): ordered dict to add key to.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.
        """
        if key not in ordered_dict:
            if inverse_diff_dict is not None:
                utils.add_key_at_start(inverse_diff_dict, key, None)
            ordered_dict[key] = value

    @staticmethod
    def _insert(key, value_tuple, ordered_dict, inverse_diff_dict=None):
        """Insert given key, value to ordered dict.

        Args:
            key (variant): key to insert.
            value_tuple (tuple(int, variant)): tuple of index to add new key at
                and value to set for key. The index defines the index that we
                want the key to have after being inserted.
            ordered_dict (OrderedDict): ordered dict to insert key into.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.
        """
        if key not in ordered_dict:
            if type(value_tuple) != tuple:
                raise EditError(
                    "diff_dict for INSERT op needs tuple valued leaves"
                )
            index = value_tuple[0]
            if index < 0 or index > len(ordered_dict):
                return
            new_value = value_tuple[1]
            # TODO: Question: is it safer to allow indexes of > len(ordered_dict)
            # or leave it up to clients of this edit to ensure that they don't give
            # indexes that high.
            # further q, is it safer to raise errors in edit classes when edit can't be
            # performed? Or at least, maybe we should return false? Then there could be
            # something done with composite edits where we raise an error/don't do
            # the edit if one of the subedits can't be done.
            # But then there's still q of what to do if part of edit can be done. So
            # maybe the error is easiest.
            if index == len(ordered_dict):
                ordered_dict[key] = new_value
            else:
                for i in range(len(ordered_dict)):
                    k, v = ordered_dict.popitem(last=False)
                    if index == i:
                        ordered_dict[key] = new_value
                    ordered_dict[k] = v
            if inverse_diff_dict is not None:
                utils.add_key_at_start(inverse_diff_dict, key, None)

    @staticmethod
    def _remove(key, _, ordered_dict, inverse_diff_dict=None):
        """Remove given key from ordered dict.

        Args:
            key (variant): key to remove.
            _ (variant): value at key, passed for neatness so args match other
                functions, but this is unused (and should be None).
            ordered_dict (OrderedDict): ordered dict to remove key from.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.
        """
        if key in ordered_dict:
            if inverse_diff_dict is not None:
                index = list(ordered_dict.keys()).index(key)
                utils.add_key_at_start(
                    inverse_diff_dict,
                    key,
                    (index, ordered_dict[key])
                )
            del ordered_dict[key]

    @staticmethod
    def _rename(key, new_key, ordered_dict, inverse_diff_dict=None):
        """Rename given key in ordered dict.

        Args:
            key (variant): key to rename.
            new_key (variant): new name of key.
            ordered_dict (OrderedDict): ordered dict whose key we're renaming.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.
        """
        if key in ordered_dict:
            for i in range(len(ordered_dict)):
                k, v = ordered_dict.popitem(last=False)
                if k == key:
                    ordered_dict[new_key] = v
                else:
                    ordered_dict[k] = v
            if inverse_diff_dict is not None:
                utils.add_key_at_start(inverse_diff_dict, new_key, key)

    @staticmethod
    def _modify(key, new_value, ordered_dict, inverse_diff_dict=None):
        """Modify given key to new value in ordered dict.

        Args:
            key (variant): key to modify.
            new_value (variant): new value for key.
            ordered_dict (OrderedDict): ordered dict whose key we're modifying.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.
        """
        if key in ordered_dict:
            if inverse_diff_dict is not None:
                utils.add_key_at_start(
                    inverse_diff_dict,
                    key,
                    ordered_dict[key]
                )
            ordered_dict[key] = new_value

    @staticmethod
    def _move(key, index, ordered_dict, inverse_diff_dict=None):
        """Move given key to new index in ordered dict.

        Args:
            key (variant): key to move.
            index (int): new index for key. The index defines the index that we
                want the key to have after being inserted.
            ordered_dict (OrderedDict): ordered dict whose key we're moving.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.
        """
        if key in ordered_dict and index >= 0 and index < len(ordered_dict):
            value = ordered_dict[key]
            old_index = list(ordered_dict.keys()).index(key)
            if inverse_diff_dict is not None:
                utils.add_key_at_start(inverse_diff_dict, key, old_index)
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

    # TODO: add some tests for these composite ones, haven't considered all
    # cases so I don't know if could hit some issues with the inverses for
    # certain recursive scenarios - but seems to work for task history :)
    @staticmethod
    def _add_or_modify(key, value, ordered_dict, inverse_diff_dict=None):
        """Add given key to dict if doesn't exist or modify existing key.

        Args:
            key (variant): key to add in modify.
            value (variant): value for key.
            ordered_dict (OrderedDict): ordered dict we're editing.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.
        """
        if key in ordered_dict:
            OrderedDictEdit._modify(
                key,
                value,
                ordered_dict,
                inverse_diff_dict
            )
        else:
            OrderedDictEdit._add(
                key,
                value,
                ordered_dict,
                inverse_diff_dict
            )

    @staticmethod
    def _remove_or_modify(key, value, ordered_dict, inverse_diff_dict=None):
        """Remove existing key from dict if value is None, else modify key.

        Args:
            key (variant): key to add in modify.
            value (variant): value for key.
            ordered_dict (OrderedDict): ordered dict we're editing.
            inverse_diff_dict (OrderedDict or None): if given, add to this to
                define inverse operation.
        """
        if value is None:
            OrderedDictEdit._remove(
                key,
                value,
                ordered_dict,
                inverse_diff_dict
            )
        else:
            OrderedDictEdit._modify(
                key,
                value,
                ordered_dict,
                inverse_diff_dict
            )

    def _inverse_run(self):
        """Run inverse operation to undo edit.

        Raises:
            (EditError): if the edit has not yet been run so the diff dict
                hasn't been filled up.
        """
        if self.inverse_diff_dict is None:
            raise EditError(
                "Can only call OrderedDictEdit _inverse_run once _run has "
                "been called."
            )
        self._run_operation(
            self.ordered_dict,
            self.inverse_diff_dict,
            self.inverse_operation_type,
        )
