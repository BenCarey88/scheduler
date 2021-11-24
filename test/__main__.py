"""Run all unittests."""

import unittest

from .ordered_dict_edit_test import (
    OrderedDictEditTest,
    OrderedDictRecursiveEditTest
)
from .tree_edit_test import BaseTreeEditTest, TaskEditTest
from .tree_test import TaskTreeTest


if __name__ == '__main__':
    unittest.main()
