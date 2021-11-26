"""Filters for children in tree models.

Includes all base filters as well as filters for specific tree types.
"""

from ._base_filters import (
    NoFilter,
    FullPrune,
    KeepChildrenOfType,
    RemoveChildrenById,
    RemoveChildrenOfType,
    RemoveGivenChildren,
    RemoveSubChildrenOfType,
    RestrictToGivenChildren
)
from .task import Task
from .task_category import (
    TaskCategory,
    TaskCategoryFilter,
    TaskFilter
)


class NoTasks(RemoveChildrenOfType):
    """Filter to remove all tasks from child dicts."""
    def __init__(self):
        super(NoTasks, self).__init__(Task)


class NoSubtasks(RemoveSubChildrenOfType):
    """Filter to remove all subtasks from child dicts."""
    def __init__(self):
        super(NoSubtasks, self).__init__(Task)
