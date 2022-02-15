"""User preference classes."""


from .serializable import BaseSerializable


class _BaseUserPrefs(BaseSerializable):
    """Base user preferences class."""


class _GeneralUserPrefs(_BaseUserPrefs):
    """Class for general user preferences relating to the application."""


class _ProjectUserPrefs(_BaseUserPrefs):
    """Class for user preferences relating to a specific schedule project."""
