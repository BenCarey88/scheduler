"""User preference classes."""

import os

from scheduler.api import constants, utils
from scheduler.api.common.serializable import (
    BaseSerializable,
    SerializationError
)


class UserPrefsError(Exception):
    """Exception class for all user pref related errors."""


class _BaseUserPrefs(BaseSerializable):
    """Base user preferences class."""

    def __init__(self):
        """Initialise class.

        Attributes:
            user_prefs_dict (dict): json-serializable dictionary representing
                user preferences to save between sessions.
            functions_dict (dict): dictionary of functions that gets populated
                and used by the register_and_initialize decorator factory.
                These can't be serialized and so get repopulated each time the
                app is opened, but are used to define how to apply some of the
                saved user pref values.
            file_path (str): path of file to read/write from/to.
        """
        self._user_prefs_dict = {}
        self._functions_dict = {}
        self._file_path = ""

    def register_method(self, method):
        """Decorator to register a method and run it.

        This is intended to be used with methods that users call to alter the
        state of the ui when we want to save the altered state. Then, in the
        __init__ of the ui class, we can call initialize_methods to run that
        method with the saved values.

        This decorator can only be used on methods of classes, as opposed to
        standalone functions. Note that the args and kwargs of the decorated
        function will be added to the user prefs, so it can only be used on
        functions that take in serializable arguments.

        Args:
            method (function): the method to decorate.

        Returns:
            (function): the decorated function, which will now register the
                arguments that it's called with.
        """
        class_name = utils.get_class_name_from_method(method)
        func_name = method.__name__
        # register method
        if self._functions_dict.get(class_name, {}).get(func_name):
            raise UserPrefsError(
                "Cannot register multiple functions for class {0} "
                "with name {1}".format(class_name, func_name)
            )
        self._functions_dict.setdefault(class_name, {})[func_name] = method
        # when we run it, register new argument values
        def decorated_method(class_instance, *args, **kwargs):
            self._user_prefs_dict.setdefault(class_name, {})[func_name] = (
                args, kwargs
            )
            return method(class_instance, *args, **kwargs)
        return decorated_method

    def initialize_methods(self, class_instance):
        """Initialize registered methods for class instance using saved values.

        Args:
            class_instance (variant): the class instance we're initializing.
        """
        class_name = type(class_instance).__name__
        args_and_kwargs_dict = self._user_prefs_dict.get(class_name, {})
        methods_dict = self._functions_dict.get(class_name, {})
        for method_name, args_and_kwargs in args_and_kwargs_dict.items():
            method = methods_dict.get(method_name)
            if method is not None:
                args, kwargs = args_and_kwargs
                method(class_instance, *args, **kwargs)

    def get_attribute(self, name, default=None):
        """Get user preference with given name.

        Args:
            name (str): name of attribute to get.
            default (variant): default value to set, if wanted.

        Returns:
            (variant or None): the user prefs attribute if found.
        """
        return self._user_prefs_dict.get(name, default)

    def set_attribute(self, name, value):
        """Set user preference with given name to given value.

        Args:
            name (str): name of attribute to set.
           value (variant): value to set.
        """
        self._user_prefs_dict[name] = value

    @classmethod
    def from_dict(cls, dictionary):
        """Initialise class from dictionary."""
        user_prefs = cls()
        user_prefs._user_prefs_dict = dictionary
        return user_prefs

    def to_dict(self):
        """Create dict from class.

        Returns:
            (dict): Serialized dictionary.
        """
        return self._user_prefs_dict

    @classmethod
    def from_file_or_new(cls, file_path=None):
        """Load user prefs from file if exists, else create new user prefs.

        Args:
            file_path (str or None): path to try to load from, if given.

        Returns:
            (_BaseUserPrefs): user prefs class instance.
        """
        if file_path is None:
            return cls()
        try:
            user_prefs = cls.from_file(file_path)
        except SerializationError:
            user_prefs = cls()
        user_prefs._file_path = file_path
        return user_prefs

    def write(self):
        """Write class to file."""
        if not self._file_path:
            raise UserPrefsError("No file path set, can't write user prefs")
        self.to_file(self._file_path)


class _AppUserPrefs(_BaseUserPrefs):
    """Class for general user preferences relating to the application."""

    @property
    def project_user_prefs_file(self):
        """Get path to user prefs class for active schedule project.

        Returns:
            (str or None): file path to project user prefs, if an active
                project is set.
        """
        project_path = self._user_prefs_dict.get("active_project")
        if project_path is None:
            return project_path
        return os.path.join(
            project_path,
            "user_prefs.json"
        )


class _ProjectUserPrefs(_BaseUserPrefs):
    """Class for user preferences relating to a specific schedule project."""


APP_USER_PREFS = _AppUserPrefs.from_file_or_new(
    constants.USER_PREFS_FILE
)
PROJECT_USER_PREFS = _ProjectUserPrefs.from_file_or_new(
    APP_USER_PREFS.project_user_prefs_file
)


def get_app_user_pref(name, default=None):
    """Get app user preference with given name.

    Args:
        name (str): name of attribute to get.
        default (variant): default value to set, if wanted.

    Returns:
        (variant or None): the user prefs attribute if found.
    """
    return APP_USER_PREFS.get_attribute(name, default)


def set_app_user_pref(name, value):
    """Set user preference with given name to given value.

    Args:
        name (str): name of attribute to set.
        value (variant): value to set.
    """
    APP_USER_PREFS.set_attribute(name, value)


def save_app_user_prefs():
    """Save application user preferences."""
    APP_USER_PREFS.write()


def update_project_user_prefs():
    """Switch to the new project user prefs when active project is changed.

    This assumes the active project has already been updated in the app user
    preferences.
    """
    try:
        PROJECT_USER_PREFS.write()
    except UserPrefsError:
        pass
    PROJECT_USER_PREFS = _ProjectUserPrefs.from_file_or_new(
        APP_USER_PREFS.project_user_prefs_file
    )


def get_project_user_pref(name, default=None):
    """Get app user preference with given name.

    Args:
        name (str): name of attribute to get.
        default (variant): default value to set, if wanted.

    Returns:
        (variant or None): the user prefs attribute if found.
    """
    return PROJECT_USER_PREFS.get_attribute(name, default)


def set_project_user_pref(name, value):
    """Set user preference with given name to given value.

    Args:
        name (str): name of attribute to set.
        value (variant): value to set.
    """
    PROJECT_USER_PREFS.set_attribute(name, value)


def save_project_user_prefs():
    """Save project user preferences."""
    PROJECT_USER_PREFS.write()