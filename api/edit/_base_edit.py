"""Base edit class, containing edits that can be added to the edit log."""

from uuid import uuid4

from .edit_log import EDIT_LOG


class EditError(Exception):
    """General error class for all edit exceptions."""


class BaseEdit(object):
    """Base class representing an edit that we can register in the log.

    In general, subclasses need to implement _run and _inverse_run.
    """

    def __init__(self):
        """Initialise edit.

        Attributes:
            _register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone). By default this is true, but can be changed by
                creating the edit with the class method create_unregistered.
            _registered (bool): determines if the edit has been registered
                or not.
            _continuous_run_in_progress (bool): tells us if the edit is
                currently being continuously run and so can be updated.
            _is_valid (bool): determines if edit is valid or not. This is used
                by the edit log to determine whether or not we should add the
                edit.
            _has_been_done (bool): used by undo/redo to determine if the
                edit has been done (and hence can be undone) or not (and
                hence can be run/redone).
            _name (str): name to use for edit in edit log.
            _description (str): description to use for edit in edit log.
            _id (str): id of edit, used to compare to other edits, and used as
                an index in edit_log.
        """
        self._register_edit = True
        self._registered = False
        self._continuous_run_in_progress = False
        self._is_valid = True
        self._has_been_done = False
        self._name = "Unnamed Edit"
        self._description = ""
        # self._id = uuid4()

    @classmethod
    def create_and_run(cls, *args, **kwargs):
        """Create and run an edit.

        This is what should be used by client classes in most cases: there
        shouldn't be any need for most client classes to maintain an edit
        after initialisation or call any of its other methods; this allows
        us to create the edit, run it and then (if it gets registered) hand
        ownership of it over to the EDIT_LOG.

        Exceptions to this rule are:
            - when creating an unregistered edit as part of a composite edit
            - when creating an edit to be used as part of a continuous run

        Args:
            args (tuple): args to pass to __init__.
            kwargs (dict): kwargs to pass to __init__.

        Returns:
            (bool): whether or not edit was successful (and hence added to
                the edit log).
        """
        edit = cls(*args, **kwargs)
        return edit.run()

    @classmethod
    def create_unregistered(cls, *args, **kwargs):
        """Create an unregistered edit. Used for subedits of composite edits.

        Args:
            args (tuple): args to pass to __init__.
            kwargs (dict): kwargs to pass to __init__.

        Returns:
            (BaseEdit): the edit object.
        """
        edit = cls(*args, **kwargs)
        edit._register_edit = False
        return edit

    def _check_validity(self):
        """Check if edit is valid. This is done after run and update.

        This can be used to check validitiy of the edits. Override this in
        base class for validity checks.
        """
        pass

    def run(self):
        """Call edit function externally, and register with edit log if needed.

        This can only be called the once, if the edit is to be registered.
        When the EDIT_LOG wants to run the edit again for undoing/redoing, this
        is handled directly through the _run method.

        Returns:
            (bool): whether or not edit was successful (and hence added to
                the edit log).
        """
        if self._registered:
            raise EditError(
                "Edit object cannot be run externally after registration."
            )
        if self._continuous_run_in_progress:
            raise EditError(
                "Edit object cannot call run when a continuous_run is already "
                "in progress."
            )
        if self._has_been_done:
            raise EditError("Cannot run edit multiple times without undo.")
        if self._register_edit and EDIT_LOG.is_locked:
            # don't run registerable edits if they can't be added to log
            return
        self._run()
        self._check_validity()
        self._has_been_done = True
        if self._register_edit:
            self._registered = EDIT_LOG.add_edit(self)
        return self._is_valid

    def begin_continuous_run(self):
        """Run edit continuously.

        This runs the edit but allows it to be updated before adding to the log
        (using update_continuous_run method). This requires end_continuous_run
        to be called afterwards in order to unlock the edit log and finish
        registering the edit.
        """
        if self._registered:
            raise EditError(
                "Edit object cannot be run externally after registration."
            )
        if self._register_edit:
            if EDIT_LOG.is_locked:
                # don't run registerable edits if they can't be added to log
                return
            EDIT_LOG.begin_add_edit(self)
        self._run()
        self._continuous_run_in_progress = True

    def update_continuous_run(self, *args, **kwargs):
        """Update and run changes on continuous edit.

        Args:
            args (list): args to pass to _update method.
            kwargs (dict): kwargs to pass to _update method.
        """
        if self._registered:
            raise EditError(
                "Edit object cannot be run externally after registration."
            )
        if not self._continuous_run_in_progress:
            return
        self._update(*args, **kwargs)

    def end_continuous_run(self):
        """Finish updating continuous edit and add to edit log.
        
        Returns:
            (bool): whether or not edit was successful (and hence added to
                the edit log).
        """
        if self._registered:
            raise EditError(
                "Edit object cannot be run externally after registration."
            )
        if not self._continuous_run_in_progress:
            return
        self._check_validity()
        if self._register_edit:
            self._has_been_done = True
            self._registered = EDIT_LOG.end_add_edit()
        self._continuous_run_in_progress = False
        return self._is_valid

    def _run(self):
        """Run edit function.

        If extra data is required for the implementation of _inverse_run (eg.
        the inverse_diff_dict in ContainerEdit), it is the responsibility
        of this function to ensure this data is defined.
        """
        raise NotImplementedError(
            "_run must be implemented in BaseEdit subclasses."
        )

    def _update(self, *args, **kwargs):
        """Update parameters of edit and run updates.

        This is used during continuous run functionality and so only needs to
        be implemented in edit classes that support this.
        """
        raise NotImplementedError(
            "_update not implemented. Class doesn't support continous edits."
        )

    def _inverse_run(self):
        """Run inverse of edit function to undo edit.

        This should only be called after the _run function has been called, as
        it may be the case that some things required for the implementation of
        this method are defined in during _run (eg. inverse_diff_dict in
        ContainerEdit).
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

    # @property
    # def id(self):
    #     """Get id of edit, to be used as an index in the edit log.

    #     Returns:
    #         (str): edit id.
    #     """
    #     return self._id

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
