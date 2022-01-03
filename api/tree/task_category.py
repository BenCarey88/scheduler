"""Task class."""

from collections import OrderedDict
from functools import partial
import os
import shutil
import tempfile

from ._base_filters import KeepChildrenOfType
from ._base_tree_item import BaseTreeItem
from .exceptions import TaskFileError
from .task import Task
from ._file_utils import (
    is_tree_directory,
    check_directory_can_be_written_to
)


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

    TREE_FILE_MARKER = "category.info"
    CATEGORIES_KEY = "subcategories"
    TASKS_KEY = "tasks"

    def __init__(self, name, parent=None):
        """Initialise category class.

        Args:
            name (str): name of task.
            parent (Task or None): parent of current category, if it's a
                subcategory.
        """
        super(TaskCategory, self).__init__(name, parent)
        self.allowed_child_types = [TaskCategory, Task]

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
        while isinstance(top_level_task_category.parent, TaskCategory):
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

    def write(self, directory_path):
        """Write data to directory tree.

        The structure is:
            category_tree_dir:
                subcategory_1_tree_dir:
                subcategory_2_tree_dir:
                task_1.json
                task_2.json
                TREE_FILE_MARKER

        The TREE_FILE_MARKER file saves the official ordering as this
        will be lost in the directory.

        Args:
            directory_path (str): path to directory to write to.
        """
        check_directory_can_be_written_to(
            directory_path,
            self.TREE_FILE_MARKER
        )

        tmp_dir = None
        if os.path.exists(directory_path):
            tmp_dir = tempfile.mkdtemp(
                suffix="{0}_backup_".format(os.path.basename(directory_path)),
                dir=os.path.dirname(directory_path),
            )
            shutil.move(directory_path, tmp_dir)
        os.mkdir(directory_path)
        task_category_file = os.path.join(
            directory_path,
            self.TREE_FILE_MARKER
        )
        with open(task_category_file, "w") as file_:
            file_.write(
                "\n".join([child.name for child in self.get_all_children()])
            )

        for subcategory in self.get_all_subcategories():
            subcategory_directory = os.path.join(
                directory_path,
                subcategory.name
            )
            subcategory.write(subcategory_directory)

        for task in self.get_all_tasks():
            task_file = os.path.join(
                directory_path,
                "{0}.json".format(task.name)
            )
            task.write(task_file)

        if tmp_dir:
            shutil.rmtree(tmp_dir)

    @classmethod
    def from_directory(
            cls,
            directory_path,
            parent=None):
        """Create TaskCategory object from category directory.

        Args:
            directory_path (str): path to category directory.
            parent (TaskCategory or None): parent item.

        Raises:
            (TaskFileError): if the directory doesn't exist or isn't a task
                directory (ie. doesn't have a TREE_FILE_MARKER)

        Returns:
            (TaskCategory): TaskCategory object populated with categories from
                directory tree.
        """
        if not is_tree_directory(directory_path, cls.TREE_FILE_MARKER):
            raise TaskFileError(
                "Directory {0} is not a valid task root directory".format(
                    directory_path
                )
            )
        category_name = os.path.basename(directory_path)
        category_item = cls(name=category_name, parent=parent)

        task_category_file = os.path.join(directory_path, cls.TREE_FILE_MARKER)
        with open(task_category_file, "r") as file_:
            child_order = file_.read().split("\n")

        for name in child_order:
            if not name:
                # ignore empty strings
                continue
            path = os.path.join(directory_path, name)
            if is_tree_directory(path, TaskCategory.TREE_FILE_MARKER):
                subcategory = TaskCategory.from_directory(path, category_item)
                category_item.add_subcategory(subcategory)
            elif (os.path.isfile("{0}.json".format(path))):
                task = Task.from_file("{0}.json".format(path), category_item)
                category_item.add_task(task)

        return category_item
