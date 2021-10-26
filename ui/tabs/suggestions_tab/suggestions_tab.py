"""Suggestions Tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.tabs.base_tab import BaseTab


class SuggestionsTab(BaseTab):
    """Suggestions tab."""

    def __init__(self, tree_root, parent=None):
        """Setup suggestions tab main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(SuggestionsTab, self).__init__(tree_root, parent)

        self.view = QtWidgets.QWidget(self)
        self.outer_layout.addWidget(self.view)

    def update(self):
        pass
