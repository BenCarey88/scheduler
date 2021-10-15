"""Base Tab class."""

from PyQt5 import QtCore, QtGui, QtWidgets

from .widgets.outliner import Outliner


class BaseTab(QtWidgets.QSplitter):
    """Base Tab class."""

    MODEL_UPDATED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, tree_root, parent=None):
        """Initialise tab.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTab, self).__init__(parent)

        self.tree_root = tree_root
        self.setChildrenCollapsible(False)

        self.outliner = Outliner(self.tree_root, self)
        self.addWidget(self.outliner)

        self.outliner.MODEL_UPDATED_SIGNAL.connect(
            self.update
        )
        self.MODEL_UPDATED_SIGNAL.connect(
            self.outliner.update
        )

    def update(self):
        """Update main view to sync with model."""
        raise Exception(
            "This needs to be reimplemented in subclasses."
        )
