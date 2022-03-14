"""Test for tree edits."""

from collections import OrderedDict
import datetime
import unittest

from api.edit.tree_edit import RenameChildrenEdit
from api.edit.task_edit import UpdateTaskHistoryEdit
from api.tree._base_tree_item import BaseTreeItem
from api.tree.task import Task, TaskStatus

from .utils import create_ordered_dict_from_tuples


class BaseTreeEditTest(unittest.TestCase):
    """Test base tree edit operations."""

    def setUp(self, *args):
        """Run before each test."""
        self.tree_items = {}
        for key in ("default", "original"):
            self.tree_items[key] = BaseTreeItem("root")
            self.tree_items[key]._children = OrderedDict([
                ("child1", BaseTreeItem("child1")),
                ("child2", BaseTreeItem("child2")),
            ])
        self.tree_item = self.tree_items["default"]
        self.original_tree_item = self.tree_items["original"]
        return super(BaseTreeEditTest, self).setUp(*args)

    def test_rename(self):
        """Test rename operation."""
        edit = RenameChildrenEdit(
            self.tree_item,
            OrderedDict([("child1", "new_name")]),
        )
        edit.run()
        self.assertEqual(
            list(self.tree_item._children.keys()),
            ["new_name", "child2"]
        )
        self.assertEqual(
            self.tree_item.get_child("new_name").name, "new_name"
        )
        edit._undo()
        self.assertEqual(
            list(self.tree_item._children.keys()),
            list(self.original_tree_item._children.keys())
        )


class TaskEditTest(unittest.TestCase):
    """Test task edit operations."""

    def setUp(self, *args):
        """Run before each test."""
        self.task_items = {}
        for key in ("default", "original"):
            self.task_items[key] = Task("root")
            self.task_items[key]._children = OrderedDict([
                ("subtask1", Task("subtask1")),
                ("subtask1", Task("subtask1")),
            ])
        self.task_item = self.task_items["default"]
        self.original_task_item = self.task_items["original"]
        return super(TaskEditTest, self).setUp(*args)

    def test_update_history(self):
        """Test Update History."""
        date_time = datetime.datetime(2021, 11, 14, 21, 49, 0)
        history_edit = UpdateTaskHistoryEdit(
            self.task_item,
            date_time,
            TaskStatus.IN_PROGRESS,
            comment="TESTING",
        )
        history_edit.run()
        self.assertEqual(
            self.task_item.status,
            TaskStatus.IN_PROGRESS,
        )
        self.assertEqual(
            self.task_item.history._dict,
            create_ordered_dict_from_tuples([
                (str(date_time.date()), [
                    ("status", TaskStatus.IN_PROGRESS),
                    ("comments", [
                        (str(date_time.time()), "TESTING")
                    ])
                ])
            ])
        )
        history_edit._inverse_run()
        self.assertEqual(
            self.task_item.status,
            TaskStatus.UNSTARTED,
        )
        self.assertEqual(
            self.task_item.history._dict,
            OrderedDict()
        )
