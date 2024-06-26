"""Core edit types, used as building blocks of other edits."""

from functools import partial

from scheduler.api.common.object_wrappers import BaseObjectWrapper, Hosted
from scheduler.api.utils import fallback_value
from ._base_edit import BaseEdit, EditError


class SimpleEdit(BaseEdit):
    """Simple edit class where _run and inverse can both be predefined."""
    def __init__(
            self,
            run_func,
            inverse_run_func,
            object_to_edit=None):
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
        """
        super(SimpleEdit, self).__init__()
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
            use_inverse_flag=False):
        """Initialise edit with run function.

        Args:
            run_func (function): function used for _inverse_run_run. This
                function must take zero, one or two inputs: the object_to_edit
                (depending on whether this is passed to the __init__), and a
                boolean inverse flag, determining whether the function is being
                used for _run, or inverse _run (depending on the value of
                use_inverse_flag)
            object_to_edit (variant or None): the object(s) to be edited.
                If given, this will be passed as an argument to run_func.
            use_inverse_flag (bool): if True, run_func accepts an inverse
                argument determining whether or not it's running as an inverse.
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
        )


class CompositeEdit(BaseEdit):
    """Edit made up of a combination of other edit types."""

    def __init__(
            self,
            edits_list,
            reverse_order_for_inverse=True,
            keep_last_for_inverse=None,
            validity_check_edits=None,
            require_all_edits_valid=False):
        """Initialize composite edit.

        The edits passed to the edits_list must have their register flag
        set to False, and be unregistered.

        Args:
            edits_list (list(BaseEdit)): list of edits to compose.
            reverse_order_for_inverse (bool): if True, we reverse the order
                of the edits for the inverse.
            keep_last_for_inverse (list(BaseEdit) or None): if given, keep
                these edits last for the inverse.
            validity_check_edits (list(BaseEdit) or None): if given,
                determine validity based just on this sublist of edits.
            require_all_subedits_valid (bool): if True, the edit is valid
                only if all its subedits are (or all subedits in the
                validity_check_edits arg, if given). Otherwise, it is valid
                if any one of those subedits is valid. Either way, validity
                requires the existence of at least one subedit.
        """
        for edit in edits_list:
            if edit._register_edit or edit._registered or edit._has_been_done:
                raise EditError(
                    "Edits passed to CompositeEdit class cannot be "
                    "registered individually, and must not have already "
                    "been run."
                )
        self._edits_list = edits_list
        self._reverse_order_for_inverse = reverse_order_for_inverse
        self._keep_last_for_inverse = keep_last_for_inverse or []
        super(CompositeEdit, self).__init__()
        validity_edits = fallback_value(validity_check_edits, self._edits_list)
        # NOTE: this is_valid check is a bit dodgy, can fail since the starting
        # conditions of later edits in the edit list will be effected by the
        # earlier edits. Will often need to use custom logic in subclasses.
        boolean_operator = any
        if require_all_edits_valid:
            boolean_operator = all
        self._is_valid = bool(self._edits_list) and boolean_operator(
            [edit._is_valid for edit in validity_edits]
        )

    def _run(self):
        """Run each edit in turn."""
        for edit in self._edits_list:
            edit._run()

    def _inverse_run(self):
        """Run each inverse edit in reverse order of edits_list."""
        if self._reverse_order_for_inverse:
            inverse_edits_list = list(reversed(self._edits_list))
        else:
            inverse_edits_list = self._edits_list[:]
        for edit in self._keep_last_for_inverse:
            if edit in inverse_edits_list:
                index = inverse_edits_list.index(edit)
                inverse_edits_list.append(inverse_edits_list.pop(index))
        for edit in inverse_edits_list:
            edit._inverse_run()


class AttributeEdit(BaseEdit):
    """Edit that changes a MutableAttribute object to a new value."""
    def __init__(self, attr_dict):
        """Initiailize edit.

        Args:
            attr_dict (dict(MutableAttribute, variant)): dictionary of
                attributes with new values to set them to.
        """
        super(AttributeEdit, self).__init__()
        self._attr_dict = attr_dict
        self._orig_attr_dict = {}
        for attr in self._attr_dict:
            if not isinstance(attr, BaseObjectWrapper):
                raise EditError(
                    "attr_dict in AttributeEdit must be keyed by "
                    "MutableAttributes or MutableHostedAttributes."
                )
            self._orig_attr_dict[attr] = attr.value

        self._is_valid = bool(attr_dict) and any([
            self._orig_attr_dict[attr] != self._attr_dict[attr]
            for attr in self._attr_dict
        ])

    def _run(self):
        """Run edit."""
        for attr, value in self._attr_dict.items():
            attr.set_value(value)

    def _inverse_run(self):
        """Run edit inverse."""
        for attr, value in self._orig_attr_dict.items():
            attr.set_value(value)

    def _get_attr_value_change_string(self, attr):
        """Get string describing value change for attribute.

        Args:
            attr (MutableAttribute): attribute to check.

        Returns:
            (str or None): string describing value change for attribute,
                unless attribute is unnamed, or value is unchanged, in which
                case return None.
        """
        if not attr.name:
            return None
        orig_value = self._orig_attr_dict.get(attr, attr.value)
        new_value = self._attr_dict.get(attr, attr.value)
        if orig_value == new_value:
            return None
        return "{0}: {1} --> {2}".format(
            attr.name,
            str(orig_value),
            str(new_value)
        )

    def get_description(self, object_=None, object_name=None):
        """Get description for attr edit.

        Implemented as separate function rather than as description property
        because base edits shouldn't have descriptions. However, this can be
        used by subclasses.

        Args:
            object_ (variant or None): the object we're editing attributes of,
                if given.
            object_name (str or None): the name of the object, if given.

        Returns:
            (str): description.
        """
        attr_change_strings = [
            self._get_attr_value_change_string(attr)
            for attr in self._attr_dict
        ]
        start_string = "Edit attributes"
        if object_ is not None or object_name:
            start_string += " of "
        if object_ is not None:
            start_string += object_.__class__.__name__ + " "
        if object_name:
            start_string += object_name
        start_string += "\n\t\t"
        return (
            "{0}{1}".format(
                start_string,
                "\n\t\t".join([a for a in attr_change_strings if a])
            )
        )


class ActivateHostedDataEdit(SimpleEdit):
    """Edit to activate hosted data."""
    def __init__(self, hosted_data):
        """Initiailize edit.

        Args:
            hosted_data (Hosted): data to activate.
        """
        if not isinstance(hosted_data, Hosted):
            raise EditError(
                "args passed to ActivateHostedDataEdit must be Hosted objects."
            )
        super(ActivateHostedDataEdit, self).__init__(
            run_func=hosted_data._activate,
            inverse_run_func=hosted_data._deactivate,
        )
        self._is_valid = hosted_data.defunct


class DeactivateHostedDataEdit(SimpleEdit):
    """Edit to deactivate hosted data."""
    def __init__(self, hosted_data):
        """Initiailize edit.

        Args:
            hosted_data (Hosted): data to deactivate.
        """
        if not isinstance(hosted_data, Hosted):
            raise EditError(
                "args for DeactivateHostedDataEdit must be Hosted objects."
            )
        super(DeactivateHostedDataEdit, self).__init__(
            run_func=hosted_data._deactivate,
            inverse_run_func=hosted_data._activate,
        )
        self._is_valid = (not hosted_data.defunct)


class ReplaceHostedDataEdit(SimpleEdit):
    """Edit to replace one hosted data object with another."""
    def __init__(self, old_data, new_data):
        """Initiailize edit.

        Args:
            old_data (Hosted): old hosted data. This is expected to be
                activated already.
            new_data (Hosted): new data to replace it with. This is expected
                to be inactive.
        """
        if (not isinstance(old_data, Hosted)
                or not isinstance(new_data, Hosted)):
            raise EditError(
                "args passed to ReplaceHostedDataEdit must be Hosted objects."
            )
        super(ReplaceHostedDataEdit, self).__init__(
            run_func=partial(new_data._activate, old_data.host),
            inverse_run_func=old_data._activate,
        )
        # NOTE that the inverse func just reactivates the old data which will
        # automatically steal the old host back and deactivate the new data
        self._is_valid = (old_data != new_data)


class RedirectHostEdit(SimpleEdit):
    """Redirect one data's host to another data's host."""
    def __init__(self, old_data, new_data):
        """Initialize.

        Args:
            old_data (Hosted): data whose host we should redirect.
            new_data (Hosted): data whose host we should redirect to.
        """
        if (not isinstance(old_data, Hosted)
                or not isinstance(new_data, Hosted)):
            raise EditError(
                "args passed to RedirectHostEdit must be Hosted objects."
            )
        super(RedirectHostEdit, self).__init__(
            run_func=partial(old_data._redirect_host, new_data.host),
            inverse_run_func=partial(old_data._redirect_host, None),
        )
        self._is_valid = (old_data != new_data)
