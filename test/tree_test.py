"""Test for edits."""

from collections import OrderedDict
import os
import shutil
import unittest

from api.tree._base_tree_item import BaseTreeItem
from api.tree.task import Task
from api.tree.task_category import TaskCategory
from api.tree.task_root import TaskRoot


class TaskTreeTest(unittest.TestCase):
    """Test full task tree."""

    def setUp(self, *args):
        """Run before each test."""
        task_dir = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "task_tree"
        )
        self.temp_task_dir = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "test_task_tree"
        )
        self.tree_root = TaskRoot.from_directory(task_dir)

        base_task_dict = {
            'status': 'Unstarted',
            'type': 'General'
        }
        task_1_dict = dict(base_task_dict)
        task_1_dict.update({
            'subtasks': OrderedDict([
                ('subtask_1', base_task_dict),
                ('subtask_2', base_task_dict)
            ])
        })
        self.tree_dict = OrderedDict({
            'categories': OrderedDict([
                (
                    'category_1',
                    {
                        'subcategories': OrderedDict([
                            (
                                'subcategory_1',
                                {
                                    'tasks': OrderedDict([
                                        ('task_2', base_task_dict),
                                        ('task_1', task_1_dict)
                                    ])
                                }
                            ),
                            (
                                'subcategory_2',
                                {
                                    'tasks': OrderedDict([
                                        ('task_1', base_task_dict)
                                    ])
                                }
                            )
                        ]),
                        'tasks':  OrderedDict([
                            ('task_1', base_task_dict)
                        ])
                    }
                )
            ])
        })

    def tearDown(self):
        """Run after each test.

        Remove the temporary task directory if it's been written to.
        """
        if os.path.isdir(self.temp_task_dir):
            shutil.rmtree(self.temp_task_dir)

    def test_tree_read(self):
        """Test the tree reads correctly from a directory."""
        self.assertEqual(
            self.tree_root.to_dict(),
            self.tree_dict
        )

    def test_tree_write(self):
        """Test the tree writes correctly to a directory.

        This test assumes that the tree read functions are correct.
        """
        self.tree_root.set_directory_path(self.temp_task_dir)
        self.tree_root.add_category(TaskCategory("Test"))
        self.tree_root.write()

        self.tree_root = TaskRoot.from_directory(self.temp_task_dir)
        self.tree_dict["categories"].update(
            OrderedDict([
                ("Test", OrderedDict())
            ])
        )
        self.assertEqual(
            self.tree_root.to_dict(),
            self.tree_dict
        )
