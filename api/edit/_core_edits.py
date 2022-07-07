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
            validity_check_edits=None):
        """Initialize composite edit.

        The edits passed to the edits_list must have their register flag
        set to False, and be unregistered.

        Args:
            edits_list (list(BaseEdit)): list of edits to compose.
            reverse_order_for_inverse (bool): if True, we reverse the order
                of the edits for the inverse.
            validity_check_edits (list(BaseEdit) or None): if given,
                determine validity based just on this sublist of edits.
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
        super(CompositeEdit, self).__init__()
        validity_edits = fallback_value(validity_check_edits, self._edits_list)
        self._is_valid = any([edit._is_valid for edit in validity_edits])

    def _run(self):
        """Run each edit in turn."""
        for edit in self._edits_list:
            edit._run()

    def _inverse_run(self):
        """Run each inverse edit in reverse order of edits_list."""
        if self._reverse_order_for_inverse:
            inverse_edits_list = reversed(self._edits_list)
        else:
            inverse_edits_list = self._edits_list
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

        self._is_valid = any([
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


class HostedDataEdit(SimpleEdit):
    """Edit to switch the data of a host from one object to another."""
    def __init__(self, old_data, new_data):
        """Initiailize edit.

        Args:
            old_data (Hosted): old data of host.
            new_data (Hosted): new data of host.
        """
        if (not isinstance(old_data, Hosted)
                or not isinstance(new_data, Hosted)):
            raise EditError(
                "args passed to HostedDataEdit must be Hosted class objects."
            )
        super(HostedDataEdit, self).__init__(
            run_func=partial(new_data._switch_host, old_data.host),
            inverse_run_func=partial(old_data._switch_host, new_data.host),
        )
        self._is_valid = (old_data != new_data)
