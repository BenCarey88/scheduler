"""Tree edits to be applied to tree items."""

from collections import OrderedDict

from .edit_log import BaseEdit, EditError


class EditOperation(object):
    """Enum representing an edit operation on a dictionary."""
    ADD = "Add"
    INSERT = "Insert"
    REMOVE = "Remove"
    RENAME = "Rename"
    MODIFY = "Modify"
    MOVE = "Move"

    INVERSES = {
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
            op_type (EditOperation): operation type.

        Returns:
            (EditOperation): inverse operation type.
        """
        return cls.INVERSES.get(op_type)


class OrderedDictEdit(BaseEdit):
    """Object representing an edit on an OrderedDict."""

    def __init__(self, diff_dict, op_type, register_edit=True):
        """Initialise edit item.

        Args:
            diff_dict (OrderedDict): a dictionary representing modifications
                to a dict. How to interpret this dictionary depends on the
                operation type.
            operation_type (EditOperation): The type of edit operation to do.
            register_edit (bool): whether or not to register this edit.

        diff_dict formats:
            ADD: {new_key: new_value} - add new values at new keys
            INSERT: {new_key: (index, new_value)} - insert new key, value at
                given index
            REMOVE: {old_key: anything} - remove given keys
            RENAME: {old_key: new_key} - rename given keys
            MODIFY: {old_key: new_value} - add new values at old keys
            MOVE: {old_key: new_index} - move given key to given index
        """
        super(OrderedDictEdit, self).__init__(register_edit)
        self.diff_dict = diff_dict
        self.operation_type = op_type
        self.inverse_diff_dict = None
        self.inverse_operation_type = EditOperation.get_inverse_op(op_type)

    def _run(self, ordered_dict, *args, **kwargs):
        """Run this edit on the given ordered_dict.

        The first time this is called it should also fill up the inverse
        diff dict too.

        Args:
            ordered_dict (OrderedDict): ordered dict object to run on.
            args (list): additional args this was called with.
            kwargs (dict): additional kwargs this was called with.
        """
        super(OrderedDictEdit, self)._run(
            *args,
            ordered_dict=ordered_dict,
            **kwargs
        )

        define_inverse = False
        if self.inverse_diff_dict is None:
            self.inverse_diff_dict = OrderedDict()
            define_inverse = True

        if self.operation_type == EditOperation.ADD:
            self._add(ordered_dict, define_inverse)
        elif self.operation_type == EditOperation.INSERT:
            self._insert(ordered_dict, define_inverse)
        elif self.operation_type == EditOperation.REMOVE:
            self._remove(ordered_dict, define_inverse)
        elif self.operation_type == EditOperation.RENAME:
            self._rename(ordered_dict, define_inverse)
        elif self.operation_type == EditOperation.MODIFY:
            self._modify(ordered_dict, define_inverse)
        elif self.operation_type == EditOperation.MOVE:
            self._move(ordered_dict, define_inverse)

        # reverse inverse dict since we build up operations in opposite order
        if define_inverse:
            self.inverse_diff_dict = OrderedDict(
                reversed(list(self.inverse_diff_dict.items()))
            )

    def _add(self, ordered_dict, define_inverse):
        """Run add operation on the given ordered_dict.

        Args:
            ordered_dict (OrderedDict): ordered dict object to run on.
            define_inverse (bool): if True, also define inverse too.
        """
        for key, value in self.diff_dict.items():
            if key not in ordered_dict:
                if define_inverse:
                    self.inverse_diff_dict[key] = None
                ordered_dict[key] = value

    def _insert(self, ordered_dict, define_inverse):
        """Run insert operation on the given ordered_dict.

        The index in the diff_dict here defines the index we want the item
        to have once it's been inserted.

        Args:
            ordered_dict (OrderedDict): ordered dict object to run on.
            define_inverse (bool): if True, also define inverse too.
        """
        for new_key, value_tuple in self.diff_dict.items():
            if new_key in ordered_dict:
                continue
            if type(value_tuple) != tuple:
                raise EditError(
                    "Insert diff dict needs tuple values"
                )
            index = value_tuple[0]
            if index < 0 or index > len(ordered_dict):
                continue
            new_value = value_tuple[1]
            if index == len(ordered_dict):
                ordered_dict[new_key] = new_value
            else:
                for i in range(len(ordered_dict)):
                    key, value = ordered_dict.popitem(last=False)
                    if index == i:
                        if define_inverse:
                            self.inverse_diff_dict[new_key] = None
                        ordered_dict[new_key] = new_value
                    ordered_dict[key] = value

    def _remove(self, ordered_dict, define_inverse):
        """Run remove operation on the given ordered_dict.

        Args:
            ordered_dict (OrderedDict): ordered dict object to run on.
            define_inverse (bool): if True, also define inverse too.
        """
        for key in self.diff_dict:
            if key in ordered_dict:
                if define_inverse:
                    index = list(ordered_dict.keys()).index(key)
                    self.inverse_diff_dict[key] = (index, ordered_dict[key])
                del ordered_dict[key]

    def _rename(self, ordered_dict, define_inverse):
        """Run rename operation on the given ordered_dict.

        Args:
            ordered_dict (OrderedDict): ordered dict object to run on.
            define_inverse (bool): if True, also define inverse too.
        """
        for _ in range(len(ordered_dict)):
            key, value = ordered_dict.popitem(last=False)
            if key in self.diff_dict:
                new_key = self.diff_dict[key]
                if define_inverse:
                    self.inverse_diff_dict[new_key] = key
                key = new_key
            ordered_dict[key] = value

    def _modify(self, ordered_dict, define_inverse):
        """Run modify operation on the given ordered_dict.

        Args:
            ordered_dict (OrderedDict): ordered dict object to run on.
            define_inverse (bool): if True, also define inverse too.
        """
        for key, value in self.diff_dict.items():
            if key in ordered_dict:
                if define_inverse:
                    self.inverse_diff_dict[key] = ordered_dict[key]
                ordered_dict[key] = value

    def _move(self, ordered_dict, define_inverse):
        """Run move operation on the given ordered_dict.

        Just like insert, the index in move defines the index we expect
        the item to have once it's been moved.

        Args:
            ordered_dict (OrderedDict): ordered dict object to run on.
            define_inverse (bool): if True, also define inverse too.
        """
        for diff_key, new_index in self.diff_dict.items():
            diff_value = ordered_dict.get(diff_key)
            if not diff_value:
                continue
            if new_index < 0 or new_index >= len(ordered_dict):
                continue
            # first remove item from dict
            try:
                old_index = list(ordered_dict.keys()).index(diff_key)
            except ValueError:
                continue
            del ordered_dict[diff_key]
            if define_inverse:
                self.inverse_diff_dict[diff_key] = old_index
            # now insert item into dict in new position
            if new_index == len(ordered_dict):
                ordered_dict[diff_key] = diff_value
            else:
                for i in range(len(ordered_dict)):
                    key, value = ordered_dict.popitem(last=False)
                    if i == new_index:
                        ordered_dict[diff_key] = diff_value
                    ordered_dict[key] = value

    def _inverse(self):
        """Get inverse edit object.

        This needs to be run after the function is called.

        Returns:
            (OrderedDictEdit): Inverse OrderedDictEdit, used to undo this one.
        """
        if self._inverse_edit:
            return self._inverse_edit
        if not self.inverse_diff_dict:
            raise EditError(
                "_inverse must be called after edit has been run."
            )
        self._inverse_edit = self.from_inverse(
            self,
            self.inverse_diff_dict,
            self.inverse_operation_type
        )
        return self._inverse_edit


class BaseTreeEdit(OrderedDictEdit):
    """Object representing an edit that can be called on a tree item."""

    def _run(self, tree_item, *args, **kwargs):
        """Run this edit on a tree item.

        This method just applies an OrderedDictEdit to the tree's child dict
        (this class is a 'friend' of BaseTreeItem, hence why it can access the
        'private' _children and _name variables).

        We also add additional logic to the rename operation to ensure
        that renaming a tree in its parent's child_dict will also alter the
        child item's name attribute.

        Args:
            tree_item (BaseTreeItem or None): tree item whose child dict
                is being edited.
        """
        ordered_dict = tree_item._children
        if self.operation_type == EditOperation.RENAME:
            for name, new_name in self.diff_dict.items():
                child = ordered_dict.get(name)
                if child:
                    child._name = new_name

        kwargs["ordered_dict"] = ordered_dict
        super(BaseTreeEdit, self)._run(
            *args,
            tree_item=tree_item,
            **kwargs
        )
