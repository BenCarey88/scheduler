"""Task class."""

from collections import OrderedDict
from functools import partial

from .base_tree_item import BaseTreeItem
from .task import Task


class TaskCategory(BaseTreeItem):
    """Class representing a task category.

    This class has two types of children: subcategories and tasks.
    """

    def __init__(self, name, parent=None):
        """Initialise category class.

        Args:
            name (str): name of task.
            parent (Task or None): parent of current category, if it's a
                subcategory.
        """
        super(TaskCategory, self).__init__(name, parent)

        # subcategory methods
        self.create_subcategory = self.create_child
        self.add_subcategory = self.add_child
        self.get_subcategory = partial(
            self.get_child,
            child_dict=self._subcategories
        )
        self.get_subcategory_at_index = partial(
            self.get_child_at_index,
            child_dict=self._subcategories
        )
        self.get_all_subcategories = partial(
            self.get_all_children,
            child_dict=self._subcategories
        )
        self.num_subcategories = partial(
            self.num_children,
            child_dict=self._subcategories
        )

        # task methods
        self.create_task = partial(
            self.create_child,
            child_type=Task,
        )
        self.add_task = self.add_child
        self.get_task = partial(
            self.get_child,
            child_dict=self._tasks
        )
        self.get_task_at_index = partial(
            self.get_child_at_index,
            child_dict=self._tasks
        )
        self.get_all_tasks = partial(
            self.get_all_children,
            child_dict=self._tasks
        )
        self.num_tasks = partial(
            self.num_children,
            child_dict=self._tasks
        )

    @property
    def _subcategories(self):
        """Get subcategories, ie. children that are categories.

        Returns:
            (OrderedDict): subdict of self._children consisting of all children
                that are categories.
        """
        _subcategories = OrderedDict()
        for child_name, child in self._children.items():
            if child.__class__ == TaskCategory:
                _subcategories[child_name] = child
        return _subcategories

    @property
    def _tasks(self):
        """Get this category's tasks, ie. children that are tasks.

        Returns:
            (OrderedDict): subdict of self._children consisting of all children
                that are tasks.
        """
        _tasks = OrderedDict()
        for child_name, child in self._children.items():
            if child.__class__ == Task:
                _tasks[child_name] = child
        return _tasks

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
        to be added as a key to this dictionary in the tasks json files (see
        the task_data module for details on this).

        Returns:
            (OrderedDict): dictionary representation.
        """
        json_dict = {}
        if self._subcategories:
            subcategories_dict = OrderedDict()
            for subcategory_name, subcategory in self._subcategories.items():
                subcategories_dict[subcategory_name] = subcategory.to_dict()
            json_dict["subcategories"] = subcategories_dict
        if self._tasks:
            tasks_dict = OrderedDict()
            for task_name, task in self._tasks.items():
                tasks_dict[task_name] = task.to_dict()
            json_dict["tasks"] = tasks_dict
        return json_dict

    @classmethod
    def from_dict(cls, json_dict, name, parent=None):
        """Initialize class from dictionary representation.

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
        subcategories = json_dict.get("subcategories", {})
        for subcategory_name, subcategory_dict in subcategories.items():
            subcategory = cls.from_dict(subcategory_dict, subcategory_name, category)
            category.add_subcategory(subcategory)
        tasks = json_dict.get("tasks", {})
        for task_name, task_dict in tasks.items():
            task = Task.from_dict(task_dict, task_name)
            category.add_task(task)
        return category
