"""Base edit class, containing edits that can be added to the edit log."""

from functools import partial

from .edit_log import EDIT_LOG


class EditError(Exception):
    pass


class BaseEdit(object):
    """Base class representing an edit that we can register in the log.

    The standard order of processes in an edit class is as follows:

    create_and_run:
        - This is the intended standard way to create an edit. It calls
            edit.__init__ and then edit.run
    __init__:
        - The edit is initialized, with a flag to determine if edit will be
            registered.
        - In some cases this can also define the inverse edit, but sometimes
            it is easier to define this as part of the _run method.
    run:
        - If the edit has already been registered, an error is raised
        - Otherwise this calls edit._run
    _run:
        - _run function is reimplemented in subclasses and defines the actual
            process of the edit operation.
        - If the edit's _inverse_edit attribute is None at this point, this
            process will also need to define the edit_inverse attribute, with
            the as_inverse method of this class or some other edit class.
    as_inverse:
        - Creates an instance of an edit class with _registered=True set (so
            that we can't get a double-registation of an edit and its inverse).
    run:
        - After _run completes, the run function checks if the edit should be
            registered and adds it to the edit log if so. Note that if EDIT_LOG
            is locked, the edit would still not actually be registered here.
    undo/redo:
        - if the edit is registered, these methods can then be called from the
            EDIT_LOG. These will call the inverse edit's or the edit's _run
            method respectively.

    In general, subclasses should reimplement __init__ and _run, and ensure
    that during one of these methods, the _inverse_edit is defined.
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
            _edit_inverse (BaseEdit): another edit whose _run method should
                undo the modifications made by this edit.
            _is_inverse (bool): used to determine if this edit is an inverse or
                not. Inverse edits have limited functionality compared to a 
                regular edit since the only thing we need to use them for is
                their _run method - they should never be registered and we
                don't need to calculate their inverses. This attribute is used
                to enforce those limitations.
            _name (str): name to use for edit in edit log.
            _description (str): description to use for edit in edit log.

        A note on inverse edits:
            In theory, we don't need an inverse_edit object - all we need is
            an inverse_run function. However, in implementations it is often
            easier to define the inverse functionality through another edit
            object, to avoid rewriting the same logic. For subclasses where
            we can easily define the edit and its inverse before running,
            use the SimpleEdit class below.
        """
        self._register_edit = register_edit
        self._registered = False
        self._has_been_done = False
        self._inverse_edit = None
        self._is_inverse = False
        self._name = "Unnamed Edit"
        self._description = "Unnamed Edit Description"

    @classmethod
    def as_inverse(cls, *args, **kwargs):
        """Initiailise edit as an inverse to another edit.

        Args:
            args (tuple): args to pass to __init__.
            kwargs (dict): kwargs to pass to __init__.

        Returns:
            (BaseEdit): the edit, with _is_inverse attribute set to True.
        """
        edit = cls(*args, **kwargs)
        edit._is_inverse = True
        return edit

    @classmethod
    def create_and_run(cls, *args, **kwargs):
        """Create and run an edit.

        This is what should be used by client classes in all cases I can
        currently think of: there shouldn't be any need for a cleint class
        to maintain an edit after initialisation or call any of its other
        methods, so this allows us to create the edit, run it and then
        (if it gets registered) hand ownership of it over to the EDIT_LOG.

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

        It is the responsibility of subclasses to ensure that the _edit_inverse
        attribute is defined by the end of the time registration happens at the
        end of this method. This should be done either during the subclass
        implementation of __init__ or during the implementation of _run (since
        in many cases it is easier to define _run and its inverse together).
        """
        if self._is_inverse:
            raise EditError(
                "Inverse edit object should never be run externally."
            )
        if self._registered:
            raise EditError(
                "Edit object cannot be run externally after registration."
            )
        self._run()
        self._has_been_done = True
        if self._register_edit:
            if self._edit_inverse is None:
                raise EditError(
                    "Edit inverse must be defined before registration."
                )
            EDIT_LOG.add_edit(self)
            self._registered = True

    def _run(self):
        """Run edit and create the edit inverse if not made yet."""
        raise NotImplementedError(
            "_run must be implemented in BaseEdit subclasses."
        )

    def _inverse(self):
        """Get inverse edit object.

        This should only be called after the run function has been called.
        It is the responsibility of either the _run method (the first time it
        is called) or the __init__ method to define the _inverse_edit object.

        Returns:
            (BaseEdit): Inverse BaseEdit, used to undo this one.
        """
        if self._is_inverse:
            raise EditError(
                "Inverse edit cannot call _inverse function."
            )
        if self._inverse_edit:
            return self._inverse_edit
        raise EditError(
            "_inverse can only be called after edit has been run "
            "and registered."
        )

    def _undo(self):
        """Undo edit function."""
        if self._is_inverse:
            raise EditError(
                "Cannot call _undo on inverse edit."
            )
        if not self._has_been_done:
            raise EditError(
                "Can't call undo on edit that's already been undone."
            )
        inverse_edit = self._inverse()
        inverse_edit._run_with_args(inverse_edit._arguments)
        self._has_been_done = False

    def _redo(self):
        """Redo the edit function."""
        if self._has_been_done:
            raise EditError(
                "Can't call redo on edit that's not been undone"
            )
        self._run_with_args(self._arguments)
        self._has_been_done = True

    @property
    def name(self):
        """Get name of edit, to be displayed in edit log.
        
        Returns:
            (str): name of edit. This should be reimplemented in any subclasses
                that clients will actually call directly.
        """
        return self._name

    @property
    def desrciption(self):
        """Get descriptor of edit to be used in edit log descriptions.

        Returns:
            (str): description of edit. This should be reimplemented in any
                subclasses that clients will actually call directly.
        """
        return self._description


class SimpleEdit(BaseEdit):
    """Simple edit class where _run and inverse can both be predefined.

    This requires that both functions take in the same single argument,
    representing the object(s) that this edit will modify.

    Users can implement this either by passing in both a run_func and an
    inverse_run_func arg to the __init__, or as a subclass where they
    implement the internal _run_func and _inverse_run_func methods.
    """
    def __init__(
            self,
            object_to_edit,
            run_func=None,
            inverse_run_func=None,
            register_edit=True):
        """Initialise edit with run and inverse functions.

        Args:
            object_to_edit (variant): the object(s) to be edited. This will
                be passed as an argument to run_func and inverse_run_func.
            run_func (function or None): function used for _run. If None, we
                use the internal _run_func method instead.
            inverse_run_func (function or None): function used for inverse's
                _run. If None, we use the internal _run_func_inverse instead.
            register_edit (bool): whether or not to register this edit in
                the EDIT_LOG.
        """
        super(SimpleEdit, self).__init__(register_edit=register_edit)
        if run_func:
            self._run_func = run_func
        if inverse_run_func:
            self._inverse_run_func = inverse_run_func
        if not self._is_inverse:
            self._inverse_edit = SimpleEdit.as_inverse(
                object_to_edit=object_to_edit,
                run_func=self._inverse_run_func,
                inverse_run_func=self._run_func,
                register_edit=False,
            )
        self._run = partial(self._run_func, object_to_edit)

    def _run_func(self, object_to_edit):
        """Function used by self._run.

        This is just an alternative to passing in the run_func to __init__,
        allowing subclasses to implement this method instead.

        Args:
            object_to_edit (variant): the object(s) to be edited.
        """
        raise NotImplementedError(
            "SimpleEdit _run_func method must be implemented if run_func arg "
            " is not passed to __init__."
        )

    def _inverse_run_func(self):
        """Function used by inverse's self._run.

        This is just an alternative to passing in _inverse_run_func to
        __init__, allowing subclasses to implement this method instead.

        Args:
            object_to_edit (variant): the object(s) to be edited.
        """
        raise NotImplementedError(
            "SimpleEdit _inverse_run_func method must be implemented if "
            "inverse_run_func arg is not passed to __init__."
        )


class SelfInverseSimpleEdit(SimpleEdit):
    """Special case of simple edit where run_func defines inverse too."""

    def __init__(self, object_to_edit, run_func=None, register_edit=True):
        """Initialise edit with run function.

        Args:
            object_to_edit (variant): the object(s) to be edited. This will
                be passed as an argument to run_func.
            run_func (function or None): function used for _run and inverse
                _run. This function must take two inputs: the object_to_edit,
                and a boolean inverse flag, determining whether the function
                is being used for _run, or inverse _run. If None, this must
                be implemented in self._run_func instead.
            register_edit (bool): whether or not to register this edit in
                the EDIT_LOG.
        """
        if run_func:
            self._run_func = partial(run_func, inverse=False)
        self._inverse_run_func = partial(self._run_func, inverse=True)
        super(SelfInverseSimpleEdit, self).__init__(
            object_to_edit=object_to_edit,
            run_func=self._run_func,
            inverse_run_func=self._inverse_run_func,
            register_edit=register_edit
        )

    def _run_func(self, object_to_edit, inverse):
        """Function used by self._run.

        This is just an alternative to passing in the run_func to __init__,
        allowing subclasses to implement this method instead.

        Args:
            object_to_edit (variant): the object(s) to be edited.
            inverse (bool): whether we're using for _run or inverse _run.
        """
        raise NotImplementedError(
            "SelfInverseSimpleEdit _run_func method must be implemented if "
            " run_func arg is not passed to __init__."
        )
