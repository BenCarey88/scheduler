"""Base Tab class."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.managers import TreeManager

from scheduler.ui.widgets.outliner import Outliner


class BaseTab(QtWidgets.QWidget):
    """Base Tab class."""
    def __init__(self, name, project, parent=None):
        """Initialise tab.

        Args:
            name (str): name of tab (to pass to manager classes).
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTab, self).__init__(parent)
        self.name = name
        self.tree_manager = project.get_tree_manager(name)
        self.outliner = Outliner(self, self.tree_manager, parent=self)

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
        """Update outliner to sync with model, then return focus to this."""
        self.outliner.update()
        self.setFocus()

    def _update_and_return_focus_to_outliner(self):
        """Update main view, then return focus to outliner after."""
        self.update()
        self.outliner.setFocus()

    def update(self):
        """Update main view to sync with model."""
        raise NotImplementedError(
            "update method needs to be implemented in subclasses."
        )
