"""Task class."""

from collections import OrderedDict
from functools import partial
import os
import shutil
import tempfile

from scheduler.api.serialization.serializable import (
    SaveType,
    SerializableFileTypes,
)
from ._base_filters import KeepChildrenOfType
from ._base_tree_item import BaseTreeItem
from .task import Task


class TaskFilter(KeepChildrenOfType):
    """Filter for tasks in child dict."""
    def __init__(self):
        super(TaskFilter, self).__init__(Task)


class TaskCategoryFilter(KeepChildrenOfType):
    """Filter for task categories in child dict."""
    def __init__(self):
        super(TaskCategoryFilter, self).__init__(TaskCategory)



class TaskCategory(BaseTreeItem):
    """Class representing a task category.

    This class has two types of children: subcategories and tasks.
    """
    _SAVE_TYPE = SaveType.DIRECTORY
    _ORDER_FILE = "category{0}".format(SerializableFileTypes.ORDER)
    _MARKER_FILE = _ORDER_FILE

    _SUBDIR_KEY = "subcategories"
    _SUBDIR_DICT_TYPE = OrderedDict
    _FILE_KEY = "tasks"
    _FILE_CLASS = Task
    _FILE_DICT_TYPE = OrderedDict

    CATEGORIES_KEY = _SUBDIR_KEY
    TASKS_KEY = "tasks"

    def __init__(self, name, parent=None):
        """Initialise category class.

        Args:
            name (str): name of task.
            parent (Task or None): parent of current category, if it's a
                subcategory.
        """
        super(TaskCategory, self).__init__(name, parent)
        self._allowed_child_types = [TaskCategory, Task]

        # subcategory methods
        self.create_subcategory = self.create_child
        self.create_new_subcategory = partial(
            self.create_new_child,
            default_name="subcategory"
        )
        self.add_subcategory = self.add_child
        self.create_sibling_category = self.create_sibling
        self.create_new_sibling_category = partial(
            self.create_new_sibling,
            default_name="category"
        )
        self.add_sibling_category = self.add_sibling
        self.remove_subcategory = self.run_method_with_filter(
            self.remove_child,
            TaskCategoryFilter,
        )
        self.remove_subcategories = self.run_method_with_filter(
            self.remove_children,
            TaskCategoryFilter,
        )
        self.get_subcategory = self.run_method_with_filter(
            self.get_child,
            TaskCategoryFilter
        )
        self.get_subcategory_at_index = self.run_method_with_filter(
            self.get_child_at_index,
            TaskCategoryFilter
        )
        self.get_all_subcategories = self.run_method_with_filter(
            self.get_all_children,
            TaskCategoryFilter
        )
        self.num_subcategories = self.run_method_with_filter(
            self.num_children,
            TaskCategoryFilter
        )
        self.num_subcategory_descendants = self.run_method_with_filter(
            self.num_descendants,
            TaskCategoryFilter
        )

        # task methods
        self.create_task = partial(
            self.create_child,
            child_type=Task,
        )
        self.create_new_task = partial(
            self.create_new_child,
            default_name="task",
            child_type=Task,
        )
        self.add_task = self.add_child
        self.remove_task = self.run_method_with_filter(
            self.remove_child,
            TaskFilter
        )
        self.remove_tasks = self.run_method_with_filter(
            self.remove_children,
            TaskFilter
        )
        self.get_task = self.run_method_with_filter(
            self.get_child,
            TaskFilter
        )
        self.get_task_at_index = self.run_method_with_filter(
            self.get_child_at_index,
            TaskFilter
        )
        self.get_all_tasks = self.run_method_with_filter(
            self.get_all_children,
            TaskFilter
        )
        self.num_tasks = self.run_method_with_filter(
            self.num_children,
            TaskFilter
        )
        self.num_task_descendants = self.run_method_with_filter(
            self.num_descendants,
            TaskFilter
        )

    def run_method_with_filter(self, method, filter_class):
        """Decorator to run method with filtered child_dict.

        Args:
            method (function): method to decorate.
            filter_class (BaseFilter class): type of filter to use.

        Returns:
            (function): decorated method.
        """
        def decorated_method(*args, **kwargs):
            with self.filter_children([filter_class()]):
                return method(*args, **kwargs)
        return decorated_method

    @property
    def _subcategories(self):
        """Get subcategories, ie. children that are categories.

        Returns:
            (OrderedDict): subdict of self._children consisting of all children
                that are categories.
        """
        with self.filter_children([TaskCategoryFilter()]):
            return self._children

    @property
    def _tasks(self):
        """Get this category's tasks, ie. children that are tasks.

        Returns:
            (OrderedDict): subdict of self._children consisting of all children
                that are tasks.
        """
        with self.filter_children([TaskFilter()]):
            return self._children

    # TODO: see comment over identical function in task class. This is just
    # here as a quick hack to help with calendar_item / calendar_item_dialog
    # category attributes, we should rename this function and fix that stuff
    # up when we rename the task types. Obvs the name is wrong here as it
    # actually gives a top level task category.
    def top_level_task(self):
        """Get top level task category that this task is a subtask of.

        Returns:
            (Task): top level task item.
        """
        top_level_task_category = self
        # using this rather than isinstance checks that parent is specifically
        # a TaskCategory object and not a subclass of it
        while top_level_task_category.parent.__class__ == TaskCategory:
            top_level_task_category = top_level_task_category.parent
        return top_level_task_category

    def to_dict(self):
        """Get json compatible dictionary representation of class.

        The structure  is:
        {
            subcategories: {
                subcategory1_name: subcategory1_dict,
                subcategory2_name: subcategory2_dict,
                ...
            },
            tasks: {
                task1_name: task1_dict,
                task2_name: task2_dict,
                ...
            }
        }
        Note that this does not contain a name field, as the name is expected
        to be added as a key to this dictionary in the tasks json files.

        Returns:
            (OrderedDict): dictionary representation.
        """
        json_dict = {}
        if self._subcategories:
            subcategories_dict = OrderedDict()
            for subcategory_name, subcategory in self._subcategories.items():
                subcategories_dict[subcategory_name] = subcategory.to_dict()
            json_dict[self.CATEGORIES_KEY] = subcategories_dict
        if self._tasks:
            tasks_dict = OrderedDict()
            for task_name, task in self._tasks.items():
                tasks_dict[task_name] = task.to_dict()
            json_dict[self.TASKS_KEY] = tasks_dict
        return json_dict

    @classmethod
    def from_dict(cls, json_dict, name, parent=None):
        """Initialise class from dictionary representation.

        The json_dict is expected to be structured as described in the to_dict
        docstring.

        Args:
            json_dict (OrderedDict): dictionary representation.
            name (str): name of category.
            parent (Category or None): parent of current category, if it's a
                subcategory.

        Returns:
            (TaskCategory): category class for given dict.
        """
        category = cls(name, parent)
        subcategories = json_dict.get(cls.CATEGORIES_KEY, {})
        for subcategory_name, subcategory_dict in subcategories.items():
            subcategory = TaskCategory.from_dict(
                subcategory_dict,
                subcategory_name,
                category
            )
            category.add_subcategory(subcategory)
        tasks = json_dict.get(cls.TASKS_KEY, {})
        for task_name, task_dict in tasks.items():
            task = Task.from_dict(task_dict, task_name)
            category.add_task(task)
        return category
