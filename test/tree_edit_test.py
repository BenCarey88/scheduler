"""Test for tree edits."""

from collections import OrderedDict
import unittest

from scheduler.api.common.date_time import DateTime
from scheduler.api.constants import ItemStatus

from api.edit.tree_edit import RenameChildrenEdit
from api.edit.task_edit import UpdateTaskHistoryEdit
from api.tree._base_tree_item import BaseTreeItem
from api.tree.task import Task

from .utils import create_ordered_dict_from_tuples


class TreeItem(BaseTreeItem):
    """Override Base tree item so it's not abstract."""
    def to_dict(self):
        pass
    @classmethod
    def from_dict(cls):
        pass


class BaseTreeEditTest(unittest.TestCase):
    """Test base tree edit operations."""

    def setUp(self, *args):
        """Run before each test."""
        self.tree_items = {}
        for key in ("default", "original"):
            self.tree_items[key] = TreeItem("root")
            self.tree_items[key]._children = OrderedDict([
                ("child1", TreeItem("child1")),
                ("child2", TreeItem("child2")),
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
        date_time = DateTime(2021, 11, 14, 21, 49, 0)
        history_edit = UpdateTaskHistoryEdit(
            self.task_item,
            date_time,
            ItemStatus.IN_PROGRESS,
            comment="TESTING",
        )
        history_edit.run()
        # # TODO: task status edit logic is pretty dodgy atm, currently
        # # we only allow changing status if we do it at current datetime,
        # # which is pretty dumb. Change that so that we can uncomment this
        # # part of test:
        # self.assertEqual(
        #     self.task_item.status,
        #     ItemStatus.IN_PROGRESS,
        # )
        self.assertEqual(
            self.task_item.history._dict,
            create_ordered_dict_from_tuples([
                (date_time.date(), [
                    ("status", ItemStatus.IN_PROGRESS),
                    ("comments", [
                        (date_time.time(), "TESTING")
                    ])
                ])
            ])
        )
        history_edit._inverse_run()
        self.assertEqual(
            self.task_item.status,
            ItemStatus.UNSTARTED,
        )
        self.assertEqual(
            self.task_item.history._dict,
            OrderedDict()
        )
