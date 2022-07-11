"""Base Tab class."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.edit.edit_callbacks import CallbackItemType

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
        super(BaseTab, self).__init__(parent=parent)
        self.name = name
        self.tree_manager = project.get_tree_manager(name)
        self.outliner = Outliner(self, self.tree_manager, parent=self)
        self._is_active = False

        self.outer_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.outer_layout)

    def on_outliner_current_changed(self, new_item):
        """Callback for what to do when current is changed in outliner.

        Args:
            new_item (BaseTaskItem): new item selected in outliner.
        """
        pass

    def on_outliner_filter_changed(self, *args):
        """Callback for what to do when filter is changed in outliner."""
        pass

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        if callback_type[0] == CallbackItemType.TREE:
            self.outliner.pre_edit_callback(callback_type, *args)

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        if callback_type[0] == CallbackItemType.TREE:
            self.outliner.post_edit_callback(callback_type, *args)

    def set_active(self, value):
        """Mark tab as active/inactive when the user changes tab.

        Args:
            value (bool): whether to set as inactive.
        """
        self._is_active = value
        self.outliner._is_active = value
