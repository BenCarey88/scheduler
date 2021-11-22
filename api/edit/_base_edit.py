"""Base edit class, containing edits that can be added to the edit log."""

from .edit_log import EDIT_LOG


class EditError(Exception):
    pass


class BaseEdit(object):
    """Base class representing an edit that we can register in the log.

    In general, subclasses need to implement _run and _inverse_run.
    """

    def __init__(self, register_edit=True):
        """Initialise edit.

        Args:
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).

        Attributes:
            _register_edit (bool): see arg.
            _registered (bool): determines if the edit has been registered
                or not.
            _has_been_done (bool): used by undo/redo to determine if the
                edit has been done (and hence can be undone) or not (and
                hence can be run/redone).
            _name (str): name to use for edit in edit log.
            _description (str): description to use for edit in edit log.
        """
        self._register_edit = register_edit
        self._registered = False
        self._has_been_done = False
        self._name = "Unnamed Edit"
        self._description = ""

    @classmethod
    def create_and_run(cls, *args, **kwargs):
        """Create and run an edit.

        This is what should be used by client classes in all cases I can
        currently think of: there shouldn't be any need for a client class
        to maintain an edit after initialisation or call any of its other
        methods; this allows us to create the edit, run it and then (if it
        gets registered) hand ownership of it over to the EDIT_LOG.

        Args:
            args (tuple): args to pass to __init__.
            kwargs (dict): kwargs to pass to __init__.
        """
        edit = cls(*args, **kwargs)
        edit.run()

    def run(self):
        """Call edit function externally, and register with edit log if needed.

        This can only be called the once, if the edit is to be registered.
        When the EDIT_LOG wants to run the edit again for undoing/redoing, this
        is handled directly through the _run method.
        """
        if self._registered:
            raise EditError(
                "Edit object cannot be run externally after registration."
            )
        self._run()
        self._has_been_done = True
        if self._register_edit:
            EDIT_LOG.add_edit(self)
            self._registered = True

    def _run(self):
        """Run edit function.

        If extra data is required for the implementation of _inverse_run (eg.
        the inverse_diff_dict in OrderedDictEdit), it is the responsibility
        of this function to ensure this data is defined.
        """
        raise NotImplementedError(
            "_run must be implemented in BaseEdit subclasses."
        )

    def _inverse_run(self):
        """Run inverse of edit function to undo edit.

        This should only be called after the _run function has been called, as
        it may be the case that some things required for the implementation of
        this method are defined in during _run (eg. inverse_diff_dict in
        OrderedDictEdit).
        """
        raise NotImplementedError(
            "_inverse_run must be reimplemented in BaseEdit subclasses."
        )

    def _undo(self):
        """Undo edit function."""
        if not self._has_been_done:
            raise EditError(
                "Can't call undo on edit that's already been undone."
            )
        self._inverse_run()
        self._has_been_done = False

    def _redo(self):
        """Redo the edit function."""
        if self._has_been_done:
            raise EditError(
                "Can't call redo on edit that's not been undone."
            )
        self._run()
        self._has_been_done = True

    @property
    def name(self):
        """Get name of edit, to be displayed in edit log.
        
        Returns:
            (str): name of edit. This should be reimplemented in any subclasses
                that clients will actually call directly (or they can just
                redefine self._name).
        """
        return self._name

    @property
    def description(self):
        """Get description of edit to be used in edit log descriptions.

        Returns:
            (str): description of edit. This should be reimplemented in any
                subclasses that clients will actually call directly (or they
                can just redefine self._description).
        """
        return self._description
