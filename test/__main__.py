"""Run all unittests."""

import unittest

from .edit_test import OrderedDictEditTest, BaseTreeEditTest
from .tree_test import TaskTreeTest


if __name__ == '__main__':
    unittest.main()
