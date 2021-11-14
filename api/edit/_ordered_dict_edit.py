"""Ordered dict edits to be registered in the edit log."""

from collections import OrderedDict

from ._base_edit import BaseEdit, EditError


class OrderedDictOp(object):
    """Enum representing an edit operation on a dictionary."""
    ADD = "Add"
    INSERT = "Insert"
    REMOVE = "Remove"
    RENAME = "Rename"
    MODIFY = "Modify"
    MOVE = "Move"

    _INVERSES = {
        ADD: REMOVE,
        INSERT: REMOVE,
        REMOVE: INSERT,
        RENAME: RENAME,
        MODIFY: MODIFY,
        MOVE: MOVE,
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

        recursive diff_dicts:
            ADD:    if key already exists, check next level and retry
            INSERT: if key already exists, check next level and retry
            REMOVE: only remove keys from lowest levels
            RENAME: only rename keys from lowest levels
            MODIFY: only modify the lowest level key that matches key in the
                    ordered_dict
            MOVE:   only move keys from lowest levels
        """
        super(OrderedDictEdit, self).__init__(register_edit)
        self.ordered_dict = ordered_dict
        self.diff_dict = diff_dict
        self.operation_type = op_type
        self.recursive = recursive
        self.inverse_diff_dict = None
        self.inverse_operation_type = OrderedDictOp.get_inverse_op(op_type)
        # No need to define inverse if this is an inverse itself.
        self.define_inverse = not self._is_inverse

    def _run(self):
        """Run this edit on the given ordered_dict.

        The first time this is called it should also fill up the inverse
        diff dict too.
        """
        if self.define_inverse:
            self.inverse_diff_dict = OrderedDict()

        if self.operation_type == OrderedDictOp.ADD:
            self._add()
        elif self.operation_type == OrderedDictOp.INSERT:
            self._insert()
        elif self.operation_type == OrderedDictOp.REMOVE:
            self._remove()
        elif self.operation_type == OrderedDictOp.RENAME:
            self._rename()
        elif self.operation_type == OrderedDictOp.MODIFY:
            self._modify()
        elif self.operation_type == OrderedDictOp.MOVE:
            self._move()

        # reverse inverse dict since we build up operations in opposite order
        if self.define_inverse:
            self.inverse_diff_dict = OrderedDict(
                reversed(list(self.inverse_diff_dict.items()))
            )
            self._inverse_edit = OrderedDictEdit.as_inverse(
                ordered_dict=self.ordered_dict,
                diff_dict=self.inverse_diff_dict,
                op_type=self.inverse_operation_type,
                register_edit=False,
            )
            self.define_inverse = False

    def _add(self):
        """Run add operation on the ordered_dict."""
        for key, value in self.diff_dict.items():
            if key not in self.ordered_dict:
                if self.define_inverse:
                    self.inverse_diff_dict[key] = None
                self.ordered_dict[key] = value

    # what I think we want (but maybe define outside class/as static):
    # may POSSIBLY be able to use this to switch round again so that edits can just
    # define an inverse function rather than requiring an inverse edit.
    # ie.
    #
    # def _run(self):
    #     if self.inverse_diff_dict is None:
    #         self.inverse_diff_dict = OrderedDict()
    #         self._run_ordered_dict_edit(
    #             self.ordered_dict,
    #             self.diff_dict,
    #             inverse_diff_dict=self.inverse_diff_dict
    #         )
    #
    # def _inverse_run(self):
    #     if self.inverse_diff_dict is None:
    #         raise EditError(
    #             "Can't call _inverse_run for OrderedDicEdit until _run has been called."
    #         )
    #     self._run_ordered_dict_edit(
    #         self.ordered_dict,
    #         self.inverse_diff_dict)
    #
    def __add(
                self,
                ordered_dict,
                diff_dict,
                inverse_diff_dict=None,
                ):
        for key, value in diff_dict.items():
            if key not in ordered_dict:
                if inverse_diff_dict is not None:
                    inverse_diff_dict[key] = None
                ordered_dict[key] = value
            elif (self.recursive
                    and isinstance(value, OrderedDict)
                    and isinstance(ordered_dict[key], OrderedDict)):
                inverse_diff_dict[key] = OrderedDict()
                # remember gotta do something about the reverse ordering of inverse diff dict
                # maybe something like this
                # (but python3 only, maybe implement in utils for python2 for neatness)
                inverse_diff_dict.move_to_end(key, last=False)
                self.__add(ordered_dict[key], value, inverse_diff_dict[key])

    def _insert(self):
        """Run insert operation on the ordered_dict.

        The index in the diff_dict here defines the index we want the item
        to have once it's been inserted.
        """
        for new_key, value_tuple in self.diff_dict.items():
            if new_key in self.ordered_dict:
                continue
            if type(value_tuple) != tuple:
                raise EditError(
                    "diff_dict for INSERT operation needs tuple values"
                )
            index = value_tuple[0]
            if index < 0 or index > len(self.ordered_dict):
                continue
            new_value = value_tuple[1]
            if index == len(self.ordered_dict):
                self.ordered_dict[new_key] = new_value
            else:
                for i in range(len(self.ordered_dict)):
                    key, value = self.ordered_dict.popitem(last=False)
                    if index == i:
                        if self.define_inverse:
                            self.inverse_diff_dict[new_key] = None
                        self.ordered_dict[new_key] = new_value
                    self.ordered_dict[key] = value

    def _remove(self):
        """Run remove operation on the ordered_dict."""
        for key in self.diff_dict:
            if key in self.ordered_dict:
                if self.define_inverse:
                    index = list(self.ordered_dict.keys()).index(key)
                    self.inverse_diff_dict[key] = (
                        index,
                        self.ordered_dict[key]
                    )
                del self.ordered_dict[key]

    def _rename(self):
        """Run rename operation on the ordered_dict."""
        for _ in range(len(self.ordered_dict)):
            key, value = self.ordered_dict.popitem(last=False)
            if key in self.diff_dict:
                new_key = self.diff_dict[key]
                if self.define_inverse:
                    self.inverse_diff_dict[new_key] = key
                key = new_key
            self.ordered_dict[key] = value

    def _modify(self):
        """Run modify operation on the ordered_dict."""
        for key, value in self.diff_dict.items():
            if key in self.ordered_dict:
                if self.define_inverse:
                    self.inverse_diff_dict[key] = self.ordered_dict[key]
                self.ordered_dict[key] = value

    def _move(self):
        """Run move operation on the ordered_dict.

        Just like insert, the index here defines the index we expect the
        item to have once it's been moved.
        """
        for diff_key, new_index in self.diff_dict.items():
            diff_value = self.ordered_dict.get(diff_key)
            if not diff_value:
                continue
            if new_index < 0 or new_index >= len(self.ordered_dict):
                continue
            try:
                old_index = list(self.ordered_dict.keys()).index(diff_key)
            except ValueError:
                continue
            if self.define_inverse:
                self.inverse_diff_dict[diff_key] = old_index
            # first remove item from dict
            del self.ordered_dict[diff_key]
            # now insert item into dict in new position
            if new_index == len(self.ordered_dict):
                self.ordered_dict[diff_key] = diff_value
            else:
                for i in range(len(self.ordered_dict)):
                    key, value = self.ordered_dict.popitem(last=False)
                    if i == new_index:
                        self.ordered_dict[diff_key] = diff_value
                    self.ordered_dict[key] = value
