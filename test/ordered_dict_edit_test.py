"""Test for edits."""

from collections import OrderedDict
import unittest

from api.edit.tree_edit import BaseTreeEdit, OrderedDictOp, OrderedDictEdit
from api.tree._base_tree_item import BaseTreeItem
from api.tree.task import Task

from .utils import create_ordered_dict_from_tuples


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
            ordered_dict=self.ordered_dict,
            diff_dict=OrderedDict([("z", "Z")]),
            op_type=OrderedDictOp.ADD,
        )
        edit.run()
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
        edit._undo()
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_insert(self):
        """Test insert operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.ordered_dict,
            diff_dict=OrderedDict([("z", (2, "Z"))]),
            op_type=OrderedDictOp.INSERT,
        )
        edit.run()
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
        edit._undo()
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_remove(self):
        """Test remove operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.ordered_dict,
            diff_dict=OrderedDict([("b", None), ("d", None)]),
            op_type=OrderedDictOp.REMOVE,
        )
        edit.run()
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("a", "A"),
                ("c", "C"),
            ])
        )
        edit._undo()
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_rename(self):
        """Test rename operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.ordered_dict,
            diff_dict=OrderedDict([("a", "z"), ("b", "y")]),
            op_type=OrderedDictOp.RENAME,
        )
        edit.run()
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("z", "A"),
                ("y", "B"),
                ("c", "C"),
                ("d", "D"),
            ])
        )
        edit._undo()
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_modify(self):
        """Test modify operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.ordered_dict,
            diff_dict=OrderedDict([("c", "Z"), ("a", "Y")]),
            op_type=OrderedDictOp.MODIFY,
        )
        edit.run()
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("a", "Y"),
                ("b", "B"),
                ("c", "Z"),
                ("d", "D"),
            ])
        )
        edit._undo()
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )

    def test_move(self):
        """Test move operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.ordered_dict,
            diff_dict=OrderedDict([("b", 2), ("d", 1), ("c", 3)]),
            op_type=OrderedDictOp.MOVE,
        )
        edit.run()
        self.assertEqual(
            self.ordered_dict,
            OrderedDict([
                ("a", "A"),
                ("d", "D"),
                ("b", "B"),
                ("c", "C"),
            ])
        )
        edit._undo()
        self.assertEqual(
            self.ordered_dict,
            self.original_ordered_dict
        )


class OrderedDictRecursiveEditTest(unittest.TestCase):
    """Test recursive ordered dict edit operations."""

    def setUp(self, *args):
        """Run before each test."""
        self.recursive_dict = create_ordered_dict_from_tuples([
            ("dict", [
                ("subdict", [
                    ("a", "A"),
                    ("b", "B")
                ]),
                ("a", "A"),
                ("b", "B")
            ]),
            ("a", "A"),
            ("b", "B"),
        ])
        self.original_recursive_dict = OrderedDict(self.recursive_dict)
        return super(OrderedDictRecursiveEditTest, self).setUp(*args)

    def test_add_recursive(self):
        """Test recursive add operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.recursive_dict,
            diff_dict=create_ordered_dict_from_tuples([
                ("dict", [
                    ("subdict", [
                        ("c", "C")
                    ]),
                    ("d", "D")
                ]),
                ("e", "E")
            ]),
            op_type=OrderedDictOp.ADD,
            recursive=True,
        )
        edit.run()
        self.assertEqual(
            self.recursive_dict,
            create_ordered_dict_from_tuples([
            ("dict", [
                ("subdict", [
                    ("a", "A"),
                    ("b", "B"),
                    ("c", "C")
                ]),
                ("a", "A"),
                ("b", "B"),
                ("d", "D"),
            ]),
            ("a", "A"),
            ("b", "B"),
            ("e", "E"),
        ])
        )
        edit._undo()
        self.assertEqual(
            self.recursive_dict,
            self.original_recursive_dict
        )

    def test_insert_recursive(self):
        """Test recursive insert operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.recursive_dict,
            diff_dict=create_ordered_dict_from_tuples([
                ("dict", [
                    ("subdict", [
                        ("c", (0, "C"))
                    ]),
                    ("d", (1, "D"))
                ]),
                ("e", (2, "E"))
            ]),
            op_type=OrderedDictOp.INSERT,
            recursive=True,
        )
        edit.run()
        self.assertEqual(
            self.recursive_dict,
            create_ordered_dict_from_tuples([
                ("dict", [
                    ("subdict", [
                        ("c", "C"),
                        ("a", "A"),
                        ("b", "B")
                    ]),
                    ("d", "D"),
                    ("a", "A"),
                    ("b", "B")
                ]),
                ("a", "A"),
                ("e", "E"),
                ("b", "B")
            ])
        )
        edit._undo()
        self.assertEqual(
            self.recursive_dict,
            self.original_recursive_dict
        )

    def test_remove_recursive(self):
        """Test recursive remove operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.recursive_dict,
            diff_dict=create_ordered_dict_from_tuples([
                ("dict", [
                    ("subdict", None),
                    ("b", None)
                ]),
                ("a", None)
            ]),
            op_type=OrderedDictOp.REMOVE,
            recursive=True,
        )
        edit.run()
        self.assertEqual(
            self.recursive_dict,
            create_ordered_dict_from_tuples([
                ("dict", [
                    ("a", "A")
                ]),
                ("b", "B")
            ])
        )
        edit._undo()
        self.assertEqual(
            self.recursive_dict,
            self.original_recursive_dict
        )

    def test_rename_recursive(self):
        """Test recursive rename operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.recursive_dict,
            diff_dict=create_ordered_dict_from_tuples([
                ("dict", [
                    ("subdict", "SUBDICT"),
                    ("b", "B")
                ]),
                ("a", "A")
            ]),
            op_type=OrderedDictOp.RENAME,
            recursive=True,
        )
        edit.run()
        self.assertEqual(
            self.recursive_dict,
            create_ordered_dict_from_tuples([
                ("dict", [
                    ("SUBDICT", [
                        ("a", "A"),
                        ("b", "B")
                    ]),
                    ("a", "A"),
                    ("B", "B")
                ]),
                ("A", "A"),
                ("b", "B"),
            ])
        )
        edit._undo()
        self.assertEqual(
            self.recursive_dict,
            self.original_recursive_dict
        )

    def test_modify_recursive(self):
        """Test recursive modify operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.recursive_dict,
            diff_dict=create_ordered_dict_from_tuples([
                ("dict", [
                    ("subdict", None),
                    ("a", "Y")
                ]),
                ("a", "Z")
            ]),
            op_type=OrderedDictOp.MODIFY,
            recursive=True,
        )
        edit.run()
        self.assertEqual(
            self.recursive_dict,
            create_ordered_dict_from_tuples([
                ("dict", [
                    ("subdict", None),
                    ("a", "Y"),
                    ("b", "B")
                ]),
                ("a", "Z"),
                ("b", "B"),
            ])
        )
        edit._undo()
        self.assertEqual(
            self.recursive_dict,
            self.original_recursive_dict
        )

    def test_move_recursive(self):
        """Test recursive move operation."""
        edit = OrderedDictEdit(
            ordered_dict=self.recursive_dict,
            diff_dict=create_ordered_dict_from_tuples([
                ("dict", [
                    ("subdict", 2),
                ]),
                ("a", 0)
            ]),
            op_type=OrderedDictOp.MOVE,
            recursive=True,
        )
        edit.run()
        self.assertEqual(
            self.recursive_dict,
            create_ordered_dict_from_tuples([
                ("a", "A"),
                ("dict", [
                    ("a", "A"),
                    ("b", "B"),
                    ("subdict", [
                        ("a", "A"),
                        ("b", "B")
                    ])
                ]),
                ("b", "B"),
            ])
        )
        edit._undo()
        self.assertEqual(
            self.recursive_dict,
            self.original_recursive_dict
        )
