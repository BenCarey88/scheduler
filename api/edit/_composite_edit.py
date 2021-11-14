"""Composite edit class for combination of multiple edits."""

from _base_edit import BaseEdit, EditError


class CompositeEdit(BaseEdit):
    """Edit made up of a combination of other edit types."""

    def __init__(self, edits_list, register_edit=True):
        """Initialize composite edit.

        The edits passed to the edits_list must have their register flag
        set to False, and be unregistered.

        Args:
            edits_list (list(BaseEdit)): list of edits to compose.
            reigster_edit (bool): whether or not to register this edit.
        """
        super(CompositeEdit, self).__init__(register_edit)
        for edit in edits_list:
            if edit._register_edit or edit._registerd or edit.has_been_run:
                raise EditError(
                    "Edits passed to CompositeEdit class cannot be "
                    "registered individually, and must not have already "
                    "been run."
                )
        self.edits_list = edits_list
        # no need to define inverse if this is an inverse
        self.define_inverse = not self._is_inverse

    def _run(self):
        """Run each edit in turn, then create inverse edits dict.

        Note that if we're creating an inverse, we need to create it here as
        we can only guarantee that each sub-edit will have an inverse after it
        has been run.
        """
        inverse_edits_list = []
        for edit in self.edits_list:
            edit.__run()
            if self.define_inverse:
                inverse_edits_list.insert(0, edit._inverse())

        if self.define_inverse:
            self._inverse_edit = CompositeEdit.as_inverse(
                edits_list=inverse_edits_list,
                register_edit=False,
            )
            self.define_inverse = False
