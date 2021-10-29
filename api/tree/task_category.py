"""Task class."""

from collections import OrderedDict
from functools import partial
import os
import shutil
import tempfile

from .base_tree_item import BaseTreeItem
from .exceptions import TaskFileError
from .task import Task
from .tree_utils import (
    is_tree_directory,
    check_directory_can_be_written_to
)


class TaskCategory(BaseTreeItem):
    """Class representing a task category.

    This class has two types of children: subcategories and tasks.
    """

    TASK_CATEGORY_MARKER = "category.info"

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
        self.create_new_subcategory = partial(
            self.create_new_child,
            default_name="subcategory"
        )
        self.add_subcategory = self.add_child
        self.create_sibling_category = self.create_sibling
        self.create_new_sibling_category = partial(
            self.create_new_sibling,
            default_name = "category"
        )
        self.add_sibling_category = self.add_sibling
        self.remove_subcategory = self.run_method_with_subdict(
            self.remove_child,
            "subcategories"
        )
        self.remove_subcategories = self.run_method_with_subdict(
            self.remove_children,
            "subcategories"
        )
        self.get_subcategory = self.run_method_with_subdict(
            self.get_child,
            "subcategories"
        )
        self.get_subcategory_at_index = self.run_method_with_subdict(
            self.get_child_at_index,
            "subcategories"
        )
        self.get_all_subcategories = self.run_method_with_subdict(
            self.get_all_children,
            "subcategories"
        )
        self.num_subcategories = self.run_method_with_subdict(
            self.num_children,
            "subcategories"
        )
        self.num_subcategory_descendants = self.run_method_with_subdict(
            self.num_descendants,
            "subcategories"
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
        self.remove_task = self.run_method_with_subdict(
            self.remove_child,
            "tasks"
        )
        self.remove_tasks = self.run_method_with_subdict(
            self.remove_children,
            "tasks"
        )
        self.get_task = self.run_method_with_subdict(
            self.get_child,
            "tasks"
        )
        self.get_task_at_index = self.run_method_with_subdict(
            self.get_child_at_index,
            "tasks"
        )
        self.get_all_tasks = self.run_method_with_subdict(
            self.get_all_children,
            "tasks"
        )
        self.num_tasks = self.run_method_with_subdict(
            self.num_children,
            "tasks"
        )
        self.num_task_descendants = self.run_method_with_subdict(
            self.num_descendants,
            "tasks"
        )

    def run_method_with_subdict(self, method, tree_type):
        """Decorator to run method with different child_dict.

        Args:
            method (function): method to decorate.
            tree_type (str): type of tree to use.

        Returns:
            (function): decorated method.
        """
        # TODO: feels like we could replace the entire idea of child_dict
        # keyword just with filters, and then use that in this func instead
        # Just need to sort out the recursive imports for filters.

        def decorated_method(*args, **kwargs):
            # NOTE: this dict must be done inside this function
            # otherwise we calculate the values when the decorator is called
            # rather than when the decorated method is called
            child_dict = {
                "tasks": self._tasks,
                "subcategories": self._subcategories
            }.get(tree_type)
            if child_dict is None:
                raise Exception("tree_type {0} not defined".format(tree_type))
            return method(*args, child_dict=child_dict, **kwargs)
        return decorated_method

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
        to be added as a key to this dictionary in the tasks json files.

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
        subcategories = json_dict.get("subcategories", {})
        for subcategory_name, subcategory_dict in subcategories.items():
            subcategory = cls.from_dict(subcategory_dict, subcategory_name, category)
            category.add_subcategory(subcategory)
        tasks = json_dict.get("tasks", {})
        for task_name, task_dict in tasks.items():
            task = Task.from_dict(task_dict, task_name)
            category.add_task(task)
        return category

    def write(self, directory_path, marker=TASK_CATEGORY_MARKER):
        """Write data to directory tree.

        The structure is:
            category_tree_dir:
                subcategory_1_tree_dir:
                subcategory_2_tree_dir:
                task_1.json
                task_2.json
                TASK_CATEGORY_MARKER

        The TASK_CATEGORY_MARKER file saves the official ordering as this
        will be lost in the directory.

        Args:
            directory_path (str): path to directory to write to.
            marker (str): name of marker file that marks this as a tree.
        """
        check_directory_can_be_written_to(directory_path, marker)

        tmp_dir = None
        if os.path.exists(directory_path):
            tmp_dir = tempfile.mkdtemp(dir=os.path.dirname(directory_path))
            shutil.move(directory_path, tmp_dir)
        os.mkdir(directory_path)
        task_category_file = os.path.join(directory_path, marker)
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
            parent=None,
            marker=TASK_CATEGORY_MARKER):
        """Create TaskCategory object from category directory.

        Args:
            directory_path (str): path to category directory.
            parent (TaskCategory or None): parent item.
            marker (str): name of marker file that marks this as a tree.

        Raises:
            (TaskFileError): if the directory doesn't exist or isn't a task
                directory (ie. doesn't have a TASK_CATEGORY_MARKER)

        Returns:
            (TaskCategory): TaskCategory object populated with categories from
                directory tree.
        """
        if not is_tree_directory(directory_path, marker):
            raise TaskFileError(
                "Directory {0} is not a valid task root directory".format(
                    directory_path
                )
            )
        category_name = os.path.basename(directory_path)
        category_item = cls(name=category_name, parent=parent)

        task_category_file = os.path.join(directory_path, marker)
        with open(task_category_file, "r") as file_:
            child_order = file_.read().split("\n")

        for name in child_order:
            path = os.path.join(directory_path, name)
            if is_tree_directory(path, cls.TASK_CATEGORY_MARKER):
                subcategory = TaskCategory.from_directory(path, category_item)
                category_item.add_subcategory(subcategory)
            elif (os.path.isfile("{0}.json".format(path))):
                task = Task.from_file("{0}.json".format(path), category_item)
                category_item.add_task(task)
        return category_item
