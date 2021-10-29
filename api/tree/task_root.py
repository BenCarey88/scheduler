"""Root task item.

At any one time the scheduler ui should have one TaskRoot item that is
used across all its tabs and widgets.
"""

from .exceptions import TaskFileError
from .task_category import TaskCategory


class TaskRoot(TaskCategory):
    """Object representing all the task data for the scheduler."""

    TASK_ROOT_MARKER = "root.info"
    ROOT_NAME = "Root"

    def __init__(self, directory_path=None, *args, **kwargs):
        """Initialise TaskRoot item.

        Args:
            directory_path (str or None): path to directory this should be
                saved to, or None if not set yet.
            *args (list): additional args to allow parent class classmethod
                to use this init.
            **kwargs (dict): additional kwargs to allow parent class
                classmethod to use this init.
        """
        super(TaskRoot, self).__init__(name=self.ROOT_NAME, parent=None)
        self._directory_path = directory_path

    def set_directory_path(self, directory_path):
        """Change directory path to read/write from/to.

        Args:
            directory_path (str): new directory path.
        """
        self._directory_path = directory_path

    def get_directory_path(self):
        """Get directory path to read/write from/to.
        
        Returns:
            directory_path (str): name of directory path.
        """
        return self._directory_path

    def write(self):
        """Write data to directory tree."""
        if not self._directory_path:
            raise TaskFileError(
                "Directory path has not been set on task root."
            )
        super(TaskRoot, self).write(
            self._directory_path,
            self.TASK_ROOT_MARKER
        )

    @classmethod
    def from_directory(cls, directory_path):
        """Create TaskRoot object from task directory.

        Args:
            directory_path (str): path to tasks directory.

        Raises:
            (TaskFileError): if the directory doesn't exist or isn't a task
                directory (ie. doesn't have a TASK_ROOT_MARKER)

        Returns:
            (TaskRoot): TaskRoot object populated with tasks from directory
                tree.
        """
        root = super(TaskRoot, cls).from_directory(
            directory_path,
            marker=cls.TASK_ROOT_MARKER
        )
        root.set_directory_path(directory_path)
        return root
