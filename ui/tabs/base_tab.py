"""Base Tab class."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.widgets.outliner import Outliner


class BaseTab(QtWidgets.QWidget):
    """Base Tab class."""

    MODEL_UPDATED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, tree_root, outliner, parent=None):
        """Initialise tab.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            outliner (Outliner): outliner widget associated with this tab.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTab, self).__init__(parent)

        self.tree_root = tree_root
        self.outliner = outliner

        self.outer_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.outer_layout)

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
