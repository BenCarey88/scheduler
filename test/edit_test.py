"""Test for edits."""

from collections import OrderedDict
import unittest

from api.edit.tree_edit import BaseTreeEdit, OrderedDictOp, OrderedDictEdit
from api.tree._base_tree_item import BaseTreeItem
from api.tree.task import Task


class OrderedDictEditTest(unittest.TestCase):
    """Test ordered dict edit operations."""

    def setUp(self, *args):
        """Run before each test."""
        self.ordered_dict = OrderedDict([
            ("a", "A"),
            ("b", "B"),
            ("c", "C"),
            ("d", "D"),
        ])
        self.original_ordered_dict = OrderedDict(self.ordered_dict)
        return super(OrderedDictEditTest, self).setUp(*args)

    def test_add(self):
        """Test add operation."""
        edit = OrderedDictEdit(
            OrderedDict([("z", "Z")]),
            OrderedDictOp.ADD
        )
        edit._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("a", "A"),
                ("b", "B"),
                ("c", "C"),
                ("d", "D"),
                ("z", "Z"),
            ])
        )
        edit._inverse()._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_insert(self):
        """Test insert operation."""
        edit = OrderedDictEdit(
            OrderedDict([("z", (2, "Z"))]),
            OrderedDictOp.INSERT
        )
        edit._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("a", "A"),
                ("b", "B"),
                ("z", "Z"),
                ("c", "C"),
                ("d", "D"),
            ])
        )
        edit._inverse()._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_remove(self):
        """Test remove operation."""
        edit = OrderedDictEdit(
            OrderedDict([("b", None), ("d", None)]),
            OrderedDictOp.REMOVE
        )
        edit._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("a", "A"),
                ("c", "C"),
            ])
        )
        edit._inverse()._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_rename(self):
        """Test rename operation."""
        edit = OrderedDictEdit(
            OrderedDict([("a", "z"), ("b", "y")]),
            OrderedDictOp.RENAME
        )
        edit._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("z", "A"),
                ("y", "B"),
                ("c", "C"),
                ("d", "D"),
            ])
        )
        edit._inverse()._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_modify(self):
        """Test modify operation."""
        edit = OrderedDictEdit(
            OrderedDict([("c", "Z"), ("a", "Y")]),
            OrderedDictOp.MODIFY
        )
        edit._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("a", "Y"),
                ("b", "B"),
                ("c", "Z"),
                ("d", "D"),
            ])
        )
        edit._inverse()._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_move(self):
        """Test move operation."""
        edit = OrderedDictEdit(
            OrderedDict([("b", 2), ("d", 1), ("c", 3)]),
            OrderedDictOp.MOVE
        )
        edit._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("a", "A"),
                ("d", "D"),
                ("b", "B"),
                ("c", "C"),
            ])
        )
        edit._inverse()._run(self.ordered_dict)
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )


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
        edit = BaseTreeEdit(
            OrderedDict([("child1", "new_name")]),
            OrderedDictOp.RENAME
        )
        edit._run(self.tree_item)
        self.assertEqual(
            list(self.tree_item._children.keys()),
            ["new_name", "child2"]
        )
        self.assertEqual(
            self.tree_item.get_child("new_name").name, "new_name"
        )
        edit._inverse()._run(self.tree_item)
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

    # def test_(self):
    #     """Test Update History."""
    #     edit = BaseTreeEdit(
    #         OrderedDict([("child1", "new_name")]),
    #         OrderedDictOp.RENAME
    #     )
    #     edit._run(self.tree_item)
    #     self.assertEqual(
    #         list(self.tree_item._children.keys()),
    #         ["new_name", "child2"]
    #     )
    #     self.assertEqual(
    #         self.tree_item.get_child("new_name").name, "new_name"
    #     )
    #     edit._inverse()._run(self.tree_item)
    #     self.assertEqual(
    #         list(self.tree_item._children.keys()),
    #         list(self.original_tree_item._children.keys())
    #     )

