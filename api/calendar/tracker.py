"""Tracker file reader."""
# TODO: should this module live in another location?

from scheduler.api.serialization.serializable import BaseSerializable


class Tracker(BaseSerializable):
    """Tracker class."""
    TRACKED_TASKS_KEY = "tracked_tasks"

    def __init__(self, task_root):
        """Initialize class.

        Args:
            task_root (TaskRoot): the root task object.
        """
        super(Tracker, self).__init__()
        self.task_root = task_root
        self._tracked_tasks = []

    def get_tracked_tasks(self):
        """Get tasks selected for tracking.

        Returns:
            (list(Task)): list of tracked tasks.
        """
        return self._tracked_tasks

    @classmethod
    def from_dict(cls, dictionary, task_root):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): the dictionary we're deserializing from.
            task_root (TaskRoot): the root task object.
        """
        tracker = cls(task_root)
        task_paths = dictionary.get(cls.TRACKED_TASKS_KEY, [])
        for task_path in task_paths:
            task = task_root.get_item_at_path(task_path, search_archive=True)
            if task:
                tracker._tracked_tasks.append(task)
        return tracker

    def to_dict(self):
        """Serialize class as dictionary.

        Returns:
            (dict): the serialized dictionary.
        """
        return {
            self.TRACKED_TASKS_KEY: [
                task.path for task in self._tracked_tasks
            ]
        }
