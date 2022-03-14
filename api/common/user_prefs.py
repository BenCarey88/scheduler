"""User preference classes."""

import os

from scheduler.api import constants, utils
from scheduler.api.serialization.serializable import (
    BaseSerializable
)
from scheduler.api.serialization.default import (
    serialize_dict,
    deserialize_dict
)


class UserPrefsError(Exception):
    """Exception class for all user pref related errors."""


class BaseUserPrefs(BaseSerializable):
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
        """
        super(BaseUserPrefs, self).__init__()
        self._user_prefs_dict = {}
        self._functions_dict = {}

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
            name (str or list): name of attribute to get, or list of keys
                representing path to attribute in dict.
            default (variant): default value to set, if wanted.

        Returns:
            (variant or None): the user prefs attribute if found.
        """
        if isinstance(name, list):
            dict_value = self._user_prefs_dict
            for key in name:
                dict_value = dict_value.get(key)
                if not isinstance(dict_value, dict):
                    break
            return dict_value if dict_value is not None else default
        return self._user_prefs_dict.get(name, default)

    def set_attribute(self, name, value, default=None):
        """Set user preference with given name to given value.

        Args:
            name (str or list): name of attribute to set, or list of keys
                representing path to attribute in dict.
            value (variant): value to set.
            default (variant): default value that's used when getting this
                attribute - if this is the same as value then we just delete
                the given key from the dictionary.
        """
        prefs_dict = self._user_prefs_dict
        if isinstance(name, list):
            if len(name) == 0:
                return
            for key in name[:-1]:
                prefs_dict = prefs_dict.setdefault(key, {})
                if not isinstance(prefs_dict, dict):
                    return
            name = name[-1]
        if default is not None and value == default:
            if name in prefs_dict:
                del prefs_dict[name]
        else:
            prefs_dict[name] = value

    @classmethod
    def from_dict(cls, dictionary):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): Serialized dictionary.

        Returns:
            (BaseUserPrefs): user prefs class instance.
        """
        user_prefs = cls()
        user_prefs._user_prefs_dict = deserialize_dict(dictionary)
        return user_prefs

    def to_dict(self):
        """Create dict from class.

        Returns:
            (dict): Serialized dictionary.
        """
        return serialize_dict(
            self._user_prefs_dict,
            delete_empty_containers=True
        )


class AppUserPrefs(BaseUserPrefs):
    """Class for general user preferences relating to the application."""
    _STORE_SAVE_PATH = True


class ProjectUserPrefs(BaseUserPrefs):
    """Class for user preferences relating to a specific schedule project."""

    def __init__(self, tree_root):
        """Initialise project user prefs.

        Args:
            tree_root (TaskRoot): root of task tree for project.
        """
        super(ProjectUserPrefs, self).__init__()
        self._tree_root = tree_root

    @classmethod
    def from_dict(cls, dictionary, tree_root):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): Serialized dictionary.
            tree_root (TaskRoot): root of task tree for project.

        Returns:
            (ProjectUserPrefs): user prefs class instance.
        """
        user_prefs = cls(tree_root)
        user_prefs._user_prefs_dict = deserialize_dict(
            dictionary,
            tree_root=tree_root
        )
        return user_prefs

    def to_dict(self):
        """Create dict from class.

        Returns:
            (dict): Serialized dictionary.
        """
        return serialize_dict(
            self._user_prefs_dict,
            tree_root=self._tree_root,
            delete_empty_containers=True
        )


# app user prefs are a constant across the program
APP_USER_PREFS = AppUserPrefs.safe_read(constants.USER_PREFS_FILE)


def get_app_user_pref(name, default=None):
    """Get app user preference with given name.

    Args:
        name (str or list): name of attribute to get, or list of keys
            representing path to attribute in dict.
        default (variant): default value to set, if wanted.

    Returns:
        (variant or None): the user prefs attribute if found.
    """
    return APP_USER_PREFS.get_attribute(name, default)


def set_app_user_pref(name, value):
    """Set user preference with given name to given value.

    Args:
        name (str or list): name of attribute to set, or list of keys
            representing path to attribute in dict.
        value (variant): value to set.
    """
    APP_USER_PREFS.set_attribute(name, value)


def get_active_project():
    """Get path to active scheduler project from app user prefs.

    Returns:
        (str or None): path to active project.
    """
    active_project = get_app_user_pref("active_project")
    if active_project is None:
        return active_project
    return os.path.normpath(active_project)


def set_active_project(active_project):
    """Set path to active scheduler project from app user prefs.

    Args:
        active_project (str): path to active project.
    """
    set_app_user_pref(os.path.normpath(active_project))


def save_app_user_prefs():
    """Save application user preferences."""
    APP_USER_PREFS.write()
