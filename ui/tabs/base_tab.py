"""Base Tab class."""

from functools import partial
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.widgets.outliner import Outliner


class BaseTab(QtWidgets.QWidget):
    """Base Tab class."""

    MODEL_UPDATED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, tree_root, tree_manager, outliner, parent=None):
        """Initialise tab.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager item.
            outliner (Outliner): outliner widget associated with this tab.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTab, self).__init__(parent)

        self.tree_manager = tree_manager
        self.tree_root = tree_root
        self.outliner = outliner

        self.outer_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.outer_layout)

        self.MODEL_UPDATED_SIGNAL.connect(
            self._update_outliner
        )
        self.outliner.MODEL_UPDATED_SIGNAL.connect(
            self._update_and_return_focus_to_outliner
        )

    # TODO: neaten this section - should they probably both just always update
    # everything? ie. no need for the separate outliner and tab update functions?
    def _update_outliner(self):
        """Update outliner to sync with model.

        This function returns focus back to this tab widget after updating.
        """
        self.outliner.update()
        self.setFocus()

    def _update_and_return_focus_to_outliner(self):
        """Update main view, then return focus to outliner after."""
        self.update()
        self.outliner.setFocus()

    def update(self):
        """Update main view to sync with model."""
        raise NotImplementedError(
            "This needs to be reimplemented in subclasses."
        )
