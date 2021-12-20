"""Core edit types, used as building blocks of other edits."""

from functools import partial

from ._base_edit import BaseEdit, EditError


class SimpleEdit(BaseEdit):
    """Simple edit class where _run and inverse can both be predefined.

    This requires that both functions take in the same single argument,
    representing the object(s) that this edit will modify.
    """
    def __init__(
            self,
            object_to_edit,
            run_func,
            inverse_run_func,
            register_edit=True):
        """Initialise edit with run and inverse functions.

        Args:
            object_to_edit (variant): the object(s) to be edited. This will
                be passed as an argument to run_func and inverse_run_func.
            run_func (function): function used for _run.
            inverse_run_func (function): function used for _inverse_run.
            register_edit (bool): whether or not to register this edit in
                the EDIT_LOG.
        """
        super(SimpleEdit, self).__init__(register_edit=register_edit)
        self._run = partial(run_func, object_to_edit)
        self._inverse_run = partial(inverse_run_func, object_to_edit)


class SelfInverseSimpleEdit(SimpleEdit):
    """Special case of simple edit where run_func defines inverse too."""

    def __init__(
            self,
            object_to_edit,
            run_func,
            register_edit=True):
        """Initialise edit with run function.

        Args:
            object_to_edit (variant): the object(s) to be edited. This will
                be passed as an argument to run_func.
            run_func (function): function used for _inverse_run_run. This
                function must take two inputs: the object_to_edit, and a
                boolean inverse flag, determining whether the function is being
                used for _run, or inverse _run.
            register_edit (bool): whether or not to register this edit in
                the EDIT_LOG.
        """
        super(SelfInverseSimpleEdit, self).__init__(
            object_to_edit=object_to_edit,
            run_func=partial(run_func, inverse=False),
            inverse_run_func=partial(run_func, inverse=True),
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
        for edit in edits_list:
            if edit._register_edit or edit._registered or edit._has_been_done:
                raise EditError(
                    "Edits passed to CompositeEdit class cannot be "
                    "registered individually, and must not have already "
                    "been run."
                )
        self.edits_list = edits_list
        self.reverse_order_for_inverse = reverse_order_for_inverse

    def _run(self):
        """Run each edit in turn."""
        for edit in self.edits_list:
            edit._run()

    def _inverse_run(self):
        """Run in each inverse edit in reverse order or edits_list."""
        if self.reverse_order_for_inverse:
            inverse_edits_list = reversed(self.edits_list)
        else:
            inverse_edits_list = self.edits_list
        for edit in inverse_edits_list:
            edit._inverse_run()


class ContinuousEdit(BaseEdit):
    """Edit that can be updated as it's being run.

    This is for things like moving the time / date of a calendar date, whic
    can be done by dragging and dropping.
    """
    def __init__(self, register_edit=True):
        """Initialize continuous edit.

        Args:
            reigster_edit (bool): whether or not to register this edit.
        """
        super(ContinuousEdit, self).__init__(register_edit)

# or maybe scrap this and add updating ability to base edit
