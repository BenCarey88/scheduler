"""Base edit class, containing edits that can be added to the edit log."""


from .edit_log import EDIT_LOG


class EditError(Exception):
    pass


class Arguments(object):
    """Utility class representing arguments to pass to a function.

    The Edit classes make a lot of use of generalised args and kwargs: the
    arguments passed to the __call__ function have to be saved as attributes
    of the edit so they can be reused for undo/redo functionality. The
    as_inverse method also allows passing in args and kwargs to pass onto
    __init__. To simplify this process, and avoid confusion when multiple args
    and kwargs are passed to the same function (as with as_inverse), this
    class is used to represent a collection of args and kwargs for a function.
    """
    def __init__(self, *args, **kwargs):
        """Initialise arguments object from args and kwargs.

        Args:
            args (tuple or None): arguments, if any passed.
            kwargs (dict or None): key word arguments, if any passed.
        """
        self.args = args
        self.kwargs = kwargs

    def pass_to(self, func):
        """Pass these arguments to a function and run it.

        Args:
            func (function): function to pass these arguments to.

        Returns:
            (variant): whatever the function returns.
        """
        return func(*self.args, **self.kwargs)


# TODO: this may be super annoying to think about/do so feel free to ignore
# but: is there any actual point to separating the initialisation and the
# calling of an edit?
# conceptually they are different things (define the type of change to make,
# then apply it to a specific object) and the args passed reflect this
# difference. Practically it may also be unneccessarily confusing/annoying
# to have to throw all that info into an init
# BUUUUT
# changing could bring these potential positives:
#   1) no need for 2 separate calls in each implementation of an edit
#   2) potentially nicer internal structure, without the need to maintain
#       separate call arguments and init arguments - but potentially this
#       could be a lot messier too tbh, really not sure.
#   3) arguably, while the __init__ and __call__ are doing separate things,
#       then conceptually, an edit is a bunch of changes APPLIED to an object
#       so the object does belong in the init
#   4) moreover, there is no use case for creating an edit without running
#       __call__ so why are these done separately
#   5) as_inverse is already passing the call_args as part of init, so it
#       basically just doing that same process.
# 
#

# effectively it would be same internal structure except now:
# __init__ (call_args (or maybe call it edited_object? if removing Arguments class), ...) -->
#       there's an option to just always call _run on a single argument, the edit object
#       / the edit_object_data representing the object(s) to be edited
# _run_and_register (rename from __call__ , has no args as just uses self.call_args) -->
#       no longer needs to raise error since gets called on initialisation
# _run_from_args_object (if still using Arguments object) -->
# _run -->
# some __init__ (or maybe still as_inverse, just to pass register_edits=False/similar)

class BaseEdit(object):
    """Base class representing an edit that we can register in the log.

    The order of processes in an edit class is quite carefully chosen in order
    to allow edits to be run and registered and have their inverses defined.
    In essence, the order is as follows:

    __init__:
        - The edit is initialized, with a flag to determine if edit will be
            registered.
    __call__:
        - The edit is called by a client class.
        - This populates the edit's args and kwargs attributes, which allows
            the edit to save the arguments it's called with.
        - This then calls edit._run
    _run:
        - Run function is reimplemented in subclasses and defines the actual
            process of the edit operation.
        - If the edit's _inverse_edit attribute is None, this process will
            also need to define the edit_inverse attribute, which should use
            the as_inverse method of this class or some other edit class.
    as_inverse:
        - Returns an instance of an edit class with a _run method that should
            undo the changes made by the edit this method is called from. It's
            up to the caller to ensure that this method does indeed have a _run
            that functions as an undo by passing in the correct call_args and
            init_args.
            The inverse has _registered=True set to ensure we can't get a
            double-registation of an edit and its inverse.
    __call__:
        - after _run completes, the __call__ function checks if the edit should
            be registered and adds it to the edit log if so. Note that if the
            edit log is locked, the edit would still not actually be registered
            here.
    undo/redo:
        - if the edit is registered, these methods can then be called from the
            edit log. These will call the inverse edit's or the edit's _run
            method respectively.

    In general, subclasses should reimplement __init__ and _run (including the
    defining inverse functionality of _run).
    """

    def __init__(self, register_edit=True):
        """Initialise edit.

        Args:
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        self._register_edit = register_edit
        self._registered = False
        self._has_been_run = False
        self._arguments = None
        # TODO: when edit log isn't open, should we set this to True / have
        # some other variable to ensure we don't waste time defining an inverse
        # when we can't register the edit anyway? Does that logic work for
        # compound edits? Almost certainly fine in practice but in theory it's
        # possible for the edit log to open after an unregistered edit is made
        # but before it's passed to a CompositeEdit
        self._inverse_edit = None

    @classmethod
    def from_arguments(cls, arguments):
        """For neatness, initialises a class from an arguments object.

        Args:
            arguments (Arguments): arguments object containing all arguments
                needed for the class __init__.
        """
        return arguments.pass_to(cls)

    def __call__(self, *args, **kwargs):
        """Call edit function externally, and register with edit log if needed.

        This can only be called the once. Other calls are handled internally
        through the _run method and only used for undoing / redoing.

        It is the responsibility of subclasses to ensure that the _edit_inverse
        attribute is defined by the end of the time registration happens at the
        end of this method. This should be done either during the subclass
        implementation of __init__ or during the implementation of _run, for
        cases where _run (since in many cases it is easier to define _run and
        its inverse together).

        Args:
            args (tuple): list of args this was called with, to be passed to
                _run and also saved so they can be used with undo/redo.
            kwargs (dict): dict of kwargs this was called with, to be passed
                to _run and also saved so they can be used with undo/redo.
        """
        if self._registered:
            raise EditError(
                "Edit object cannot be called externally after registration."
            )
        self._arguments = Arguments(*args, **kwargs)

        self._run(*args, **kwargs)

        self._has_been_run = True
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

    def _run_with_args(self, arguments):
        """For convenience, reimplements _run method with an arguments object.

        Args:
            arguments (Arguments): arguments object to be passed to _run
                method.
        """
        return arguments.pass_to(self._run)

    @classmethod
    def as_inverse(cls, call_args, init_args):
        """Initiailise edit as an inverse to another edit.

        Inverse edits are treated as already registered, as they are
        effectively just an attribute of the original edit (which must
        have been registered before calling this method).

        Args:
            call_args (Arguments): args to pass to _run.
            init_args (Arguments): args to pass to __init__.

        Returns:
            (BaseEdit): the edit.
        """
        edit = cls.from_arguments(init_args)
        edit._registered = True
        edit._arguments = call_args
        return edit

    def _inverse(self):
        """Get inverse edit object.

        This needs to be run after the __call__ function is first called.
        It is the responsibility of the _run method (called by __call__) to
        also create the _inverse_edit object if it doesn't currently exist.

        Returns:
            (BaseEdit): Inverse BaseEdit, used to undo this one.
        """
        if self._inverse_edit:
            return self._inverse_edit
        raise EditError(
            "_inverse can only be called after edit has been run "
            "and registered."
        )

    # TODO: maybe add an underscore to this and redo, and just imagine
    # EDIT_LOG is a friend of this class
    # just to drive home that after creating an edit we should never
    # manually interact with it again.
    def undo(self):
        """Undo edit function."""
        if not self._has_been_run:
            raise EditError(
                "Can't call undo on edit that's already been undone"
            )
        inverse_edit = self._inverse()
        inverse_edit._run_with_args(inverse_edit._arguments)
        self._has_been_run = False

    def redo(self):
        """Redo the edit function."""
        if self._has_been_run:
            raise EditError(
                "Can't call redo on edit that's not been undone"
            )
        self._run_with_args(self._arguments)
        self._has_been_run = True


class BaseDiffEdit(BaseEdit):
    """Edit class driven by a diff data value.

    Most (if not all) edits will be driven by a diff_data value passed to the
    initializer (often an ordered dictionary).
    This is a utility class to allow us to define edits of this type without
    having to redefine the __init__ every time.
    """

    def __init__(self, diff_data, register_edit=True):
        """Initialise edit.

        Args:
            diff_data (variant): variable representing the modifications that
                will need to be made. How to interpret this will be defined in
                the _run method.
            register_edit (bool): whether or not to register this edit."""
        self.diff_data = diff_data
        super(BaseDiffEdit, self).__init__(register_edit=register_edit)


class SimpleEdit(BaseEdit):
    """Simple edit class where _run and inverse can both be predefined.

    This class can only be used in cases where _run and its inverse would
    use identical arguments (this is usually the case for non-composite
    edits anyway since the arguments to _run are the object(s) being
    edited, which will be the same for an edit and its inverse).
    """
    def __init__(self, run_func, inverse_run_func, register_edit=True):
        """Initialise edit with run and inverse functions.

        Args:
            run_func (function): function used for _run.
            inverse_run_func (function): function used for inverse's _run.
            register_edit (bool): whether or not to register this edit in
                the EDIT_LOG.
        """
        super(SimpleEdit, self).__init__(register_edit=register_edit)
        self.run_func = run_func
        self.inverse_run_func = inverse_run_func

    def _run(self, *args, **kwargs):
        """Run function and define its inverse.

        Args:
            args (tuple)
        """
        self.run_func(*args, **kwargs)
        self._inverse_edit = SimpleEdit.as_inverse(
            call_args=Arguments(*args, **kwargs),
            init_args=Arguments(
                run_func=self.inverse_run_func,
                inverse_run_func=self.run_func,
            )
        )


class SelfInverseSimpleEdit(SimpleEdit):
    """Special case of simple edit where run_func is its own inverse."""
    def __init__(self, run_func, register_edit=True):
        """Initialise edit with run function.

        Args:
            run_func (function): function used for _run and inverse _run.
            register_edit (bool): whether or not to register this edit in
                the EDIT_LOG.
        """
        super(SelfInverseSimpleEdit, self).__init__(
            run_func=run_func,
            inverse_run_func=run_func,
            register_edit=register_edit
        )
