"""Composite edit class for combination of multiple edits."""

from _base_edit import Arguments, BaseEdit, EditError


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
                    "registered individually."
                )
        self.edits_list = edits_list

    def _run(self, arguments_list):
        """Run each edit in turn, then create inverse edits dict.

        Args:
            arguments_list (list(Argument)): list of argument objects
                containing args and kwargs to be passed to each edit.
        """
        if len(arguments_list) != len(self.edits_list):
            raise EditError(
                "CompositeEdit must be run with the same number of "
                "distinct (args, kwargs) tuples as composite edits."
            )
        inverse_edits_list = []
        inverse_arguments_list = []
        for edit, arguments in zip(self.edits_list, arguments_list):
            edit._run_with_args(arguments)
            edit_inverse = edit._inverse()
            inverse_edits_list.insert(0, edit_inverse)
            inverse_arguments_list.insert(0, edit_inverse._arguments)

        self._inverse_edit = CompositeEdit.as_inverse(
            call_args=Arguments(inverse_arguments_list),
            init_args=Arguments(edits_list=inverse_edits_list),
        )
