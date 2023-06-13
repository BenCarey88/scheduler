"""Task category class."""

from collections import OrderedDict

from scheduler.api.serialization.serializable import (
    SaveType,
    SerializableFileTypes,
)
from scheduler.api.serialization import item_registry
from .exceptions import DuplicateChildNameError
from .base_task_item import BaseTaskItem
from .task import Task


class TaskCategory(BaseTaskItem):
    """Class representing a task category.

    This class has two types of children: subcategories and tasks.
    """
    _SAVE_TYPE = SaveType.DIRECTORY
    _ORDER_FILE = "category{0}".format(SerializableFileTypes.ORDER)
    _INFO_FILE = "category{0}".format(SerializableFileTypes.INFO)
    _MARKER_FILE = _ORDER_FILE

    _SUBDIR_KEY = "subcategories"
    _SUBDIR_DICT_TYPE = OrderedDict
    _FILE_KEY = "tasks"
    _FILE_CLASS = Task
    _FILE_DICT_TYPE = OrderedDict

    CATEGORIES_KEY = _SUBDIR_KEY
    TASKS_KEY = "tasks"
    ID_KEY = "id"    

    DEFAULT_NAME = "category"

    def __init__(self, name, parent=None):
        """Initialise category class.

        Args:
            name (str): name of task.
            parent (Task or None): parent of current category, if it's a
                subcategory.
        """
        super(TaskCategory, self).__init__(name, parent)
        self._allowed_child_types = [TaskCategory, Task]

    @property
    def _subcategories(self):
        """Get subcategories, ie. children that are categories.

        Returns:
            (OrderedDict): subdict of self._children consisting of all children
                that are categories.
        """
        return OrderedDict([
            (category.name, category)
            for category in self._children.values()
            if isinstance(category, TaskCategory)
        ])

    @property
    def _tasks(self):
        """Get this category's tasks, ie. children that are tasks.

        Returns:
            (OrderedDict): subdict of self._children consisting of all children
                that are tasks.
        """
        return OrderedDict([
            (task.name, task)
            for task in self._children.values()
            if isinstance(task, Task)
        ])

    # TODO: see comment over identical function in task class. This is just
    # here as a quick hack to help with scheduled_item / scheduled_item_dialog
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

    def clone(self):
        """Create skeletal clone of item, missing parent and children.

        Returns:
            (TaskCategory): cloned item.
        """
        category = TaskCategory(self.name)
        category._color = self._color
        return category

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
        to be added as a key to this dictionary.

        Returns:
            (OrderedDict): dictionary representation.
        """
        json_dict = {self.ID_KEY: self._get_id()}
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
    def from_dict(cls, json_dict, name, history_data=None, parent=None):
        """Initialise class from dictionary representation.

        The json_dict is expected to be structured as described in the to_dict
        docstring.

        Args:
            json_dict (OrderedDict): dictionary representation.
            name (str): name of category.
            history_data (HistoryData or None): history data struct to pass
                to children __init__s.
            parent (Category or None): parent of current category, if it's a
                subcategory.

        Returns:
            (TaskCategory): category class for given dict.
        """
        category = cls(name, parent)
        category._activate()
        id = json_dict.get(cls.ID_KEY, None)
        if id is not None:
            # TODO: this bit means categories are now added to item registry.
            # This was done to make deserialization of task history dicts
            # work. Keep an eye on this, I want to make sure it doesn't slow
            # down loading too much.
            item_registry.register_item(id, category)
        subcategories = json_dict.get(cls.CATEGORIES_KEY, {})
        for subcategory_name, subcategory_dict in subcategories.items():
            subcategory = TaskCategory.from_dict(
                subcategory_dict,
                subcategory_name,
                history_data=history_data,
                parent=category,
            )
            category._children[subcategory_name] = subcategory
        tasks = json_dict.get(cls.TASKS_KEY, {})
        for task_name, task_dict in tasks.items():
            task = Task.from_dict(
                task_dict,
                task_name,
                history_data=history_data,
                parent=category
            )
            if task_name in category._children:
                raise DuplicateChildNameError(
                    "Serialized category {0} has a subcategory and a task "
                    "with the same name {1}".format(
                        name,
                        task_name
                    )
                )
            category._children[task_name] = task
        return category
