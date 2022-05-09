"""Core edit types, used as building blocks of other edits."""

from functools import partial

from scheduler.api.common.object_wrappers import MutableAttribute
from ._base_edit import BaseEdit, EditError


class SimpleEdit(BaseEdit):
    """Simple edit class where _run and inverse can both be predefined."""
    def __init__(
            self,
            run_func,
            inverse_run_func,
            object_to_edit=None,
            register_edit=True):
        """Initialise edit with run and inverse functions.

        Args:
            run_func (function): function used for _run. This function must
                take either zero or one arguments, depending on whether or
                not object_to_edit is passed to the __init__.
            inverse_run_func (function): function used for _inverse_run. This
                function must take the same number of arguments as run_func.
            object_to_edit (variant or None): the object(s) to be edited.
                If given, this will be passed as an argument to run_func
                and inverse_run_func.
            register_edit (bool): whether or not to register this edit in
                the EDIT_LOG.
        """
        super(SimpleEdit, self).__init__(register_edit=register_edit)
        if object_to_edit is not None:
            self._run = partial(run_func, object_to_edit)
            self._inverse_run = partial(inverse_run_func, object_to_edit)
        else:
            self._run = run_func
            self._inverse_run = inverse_run_func


class SelfInverseSimpleEdit(SimpleEdit):
    """Special case of simple edit where run_func defines inverse too."""

    def __init__(
            self,
            run_func,
            object_to_edit=None,
            use_inverse_flag=False,
            register_edit=True):
        """Initialise edit with run function.

        Args:
            run_func (function): function used for _inverse_run_run. This
                function must take zero, one or two inputs: the object_to_edit
                (depending on whether this is passed to the __init__), and a
                boolean inverse flag, determining whether the function is being
                used for _run, or inverse _run (depending on the value of
                use_inverse_flag)
            object_to_edit (variant or None): the object(s) to be edited. If given,
                this will be passed as an argument to run_func.
            use_inverse_flag (bool): if True, run_func accepts an inverse argument
                determining whether or not it's running as an inverse.
            register_edit (bool): whether or not to register this edit in
                the EDIT_LOG.
        """
        if use_inverse_flag:
            _run_func=partial(run_func, inverse=False)
            _inverse_run_func=partial(run_func, inverse=True)
        else:
            _run_func = _inverse_run_func = run_func
        super(SelfInverseSimpleEdit, self).__init__(
            run_func=_run_func,
            inverse_run_func=_inverse_run_func,
            object_to_edit=object_to_edit,
            register_edit=register_edit
        )


class CompositeEdit(BaseEdit):
    """Edit made up of a combination of other edit types."""

    def __init__(
            self,
            edits_list,
            reverse_order_for_inverse=True,
            register_edit=True):
        """Initialize composite edit.

        The edits passed to the edits_list must have their register flag
        set to False, and be unregistered.

        Args:
            edits_list (list(BaseEdit)): list of edits to compose.
            reverse_order_for_inverse (bool): if True, we reverse the order
                of the edits for the inverse.
            reigster_edit (bool): whether or not to register this edit.
        """
        super(CompositeEdit, self).__init__(register_edit)
        self._is_valid = bool(edits_list)
        for edit in edits_list:
            if edit._register_edit or edit._registered or edit._has_been_done:
                raise EditError(
                    "Edits passed to CompositeEdit class cannot be "
                    "registered individually, and must not have already "
                    "been run."
                )
        self._edits_list = edits_list
        self._reverse_order_for_inverse = reverse_order_for_inverse
        self._valid_subedits = set()

    def _run(self):
        """Run each edit in turn."""
        for edit in self._edits_list:
            edit._run()
            if not self._registered and edit._is_valid:
                self._valid_subedits.add(edit)
        if not self._registered:
            self._is_valid = bool(self._valid_subedits)

    def _inverse_run(self):
        """Run each inverse edit in reverse order of edits_list."""
        if self._reverse_order_for_inverse:
            inverse_edits_list = reversed(self._edits_list)
        else:
            inverse_edits_list = self._edits_list
        for edit in inverse_edits_list:
            edit._inverse_run()

    def _update(
            self,
            edit_updates=None,
            edit_replacements=None,
            edit_additions=None):
        """Update subedits for continuous run functionality.

        args:
            edit_updates (dict(BaseEdit, tuple) or None): dictionary of
                subedits to update along with args and kwargs for those
                _update methods.
            edit_replacements (dict(BaseEdit, BaseEdit) or None): dictionary
                of subedits to replace, along with edits to replace them.
            edit_additions (list(BaseEdit)): additional edits to add.
        """
        edit_updates = edit_updates or {}
        edit_replacements = edit_replacements or {}
        edit_additions = edit_additions or []

        for edit, args_and_kwargs in edit_updates.items():
            if not edit in self._edits_list:
                raise EditError(
                    "Edit ({0}) not part of this composite edit. Cannot "
                    "update it.".format(edit.name)
                )
            args, kwargs = args_and_kwargs
            edit._update(*args, **kwargs)
            if edit._is_valid:
                self._valid_subedits.add(edit)
            else:
                self._valid_subedits.discard(edit)

        for edit, replacement_edit in edit_replacements.items():
            if not edit in self._edits_list:
                raise EditError(
                    "Edit ({0}) not part of this composite edit. Cannot "
                    "replace it.".format(edit.name)
                )
            if (replacement_edit._register_edit
                    or replacement_edit._registered
                    or replacement_edit._has_been_done):
                raise EditError(
                    "Edits passed to CompositeEdit update cannot be "
                    "registered individually, and must not have already "
                    "been run."
                )
            if edit._is_valid:
                edit._inverse_run()
            replacement_edit._run()
            index = self._edits_list.index(edit)
            self._edits_list[index] = replacement_edit
            self._valid_subedits.discard(edit)
            if replacement_edit._is_valid:
                self._valid_subedits.add(replacement_edit)

        for edit in edit_additions:
            if edit._register_edit or edit._registered or edit._has_been_done:
                raise EditError(
                    "Edits passed to CompositeEdit update cannot be "
                    "registered individually, and must not have already "
                    "been run."
                )
            self._edits_list.append(edit)
            edit._run()
            if edit._is_valid:
                self._valid_subedits.add(edit)

        self._is_valid = bool(self._valid_subedits)


class AttributeEdit(BaseEdit):
    """Edit that changes a MutableAttribute object to a new value."""
    def __init__(self, attr_dict, register_edit=True):
        """Initiailize edit.

        Args:
            attr_dict (dict(MutableAttribute, variant)): dictionary of
                attributes with new values to set them to.
            reigster_edit (bool): whether or not to register this edit.
        """
        super(AttributeEdit, self).__init__(register_edit)
        self._attr_dict = attr_dict
        self._orig_attr_dict = {}
        for attr in self._attr_dict:
            if not isinstance(attr, MutableAttribute):
                raise EditError(
                    "attr_dict in AttributeEdit must be keyed by "
                    "MutableAttribute objects."
                )
            self._orig_attr_dict[attr] = attr.value
        self._modified_attrs = set()

    def _run(self):
        """Run edit."""
        for attr, value in self._attr_dict.items():
            if attr.set_value(value) and not self._registered:
                self._modified_attrs.add(value)
        if not self._registered:
            self._is_valid = bool(self._modified_attrs)

    def _inverse_run(self):
        """Run edit inverse."""
        for attr, value in self._orig_attr_dict.items():
            attr.set_value(value)

    def _update(self, attr_dict):
        """Update attr dict for continuous run functionality.

        args:
            attr_dict (dict(MutableAttribute, variant)): dictionary of
                attributes with new values to update them to.
        """
        for attr in attr_dict:
            if not isinstance(attr, MutableAttribute):
                raise EditError(
                    "attr_dict in AttributeEdit must be keyed by "
                    "MutableAttribute objects."
                )
        self._attr_dict.update(attr_dict)
        for attr, value in self._attr_dict.items():
            if attr not in self._orig_attr_dict:
                self._orig_attr_dict[attr] = attr.value
            if attr.set_value(value):
                self._modified_attrs.add(value)
            else:
                self._modified_attrs.discard(value)
        self._is_valid = bool(self._modified_attrs)


class HostedDataEdit(SimpleEdit):
    """Edit to switch the data of a host from one object to another."""
    def __init__(self, old_data, new_data, register_edit=True):
        """Initiailize edit.

        Args:
            old_data (_Hosted): old data of host.
            new_data (_Hosted): new data of host.
            reigster_edit (bool): whether or not to register this edit.
        """
        self._is_valid = (old_data != new_data)
        super(HostedDataEdit, self).__init__(
            run_func=partial(new_data._switch_host, old_data._host),
            inverse_run_func=partial(old_data._switch_host, new_data._host),
            register_edit=register_edit,
        )
