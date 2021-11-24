"""Suggestions Tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.tabs.base_tab import BaseTab


class SuggestionsTab(BaseTab):
    """Suggestions tab."""

    def __init__(self, tree_root, tree_manager, outliner, parent=None):
        """Setup suggestions tab main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner widget.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(SuggestionsTab, self).__init__(
            tree_root,
            tree_manager,
            outliner,
            parent=parent
        )
        self.view = QtWidgets.QWidget(self)
        self.outer_layout.addWidget(self.view)

    def update(self):
        pass
