"""Base Tab class."""

from PyQt5 import QtCore, QtGui, QtWidgets

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

    def on_outliner_current_changed(self, new_item):
        """Callback for what to do when current is changed in outliner.

        Args:
            new_item (BaseTreeItem): new item selected in outliner.
        """
        pass
