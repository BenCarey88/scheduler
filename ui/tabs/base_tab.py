"""Base Tab class."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.edit.edit_callbacks import CallbackItemType

from scheduler.ui.widgets.outliner import Outliner
from scheduler.ui.widgets.outliner_panel import OutlinerPanel


class BaseTab(QtWidgets.QWidget):
    """Base Tab class."""
    def __init__(self, filter_type, project, parent=None):
        """Initialise tab.

        Args:
            filter_type (FilterType): filter_type that tab uses. This is
                currently the name of the tab as well.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTab, self).__init__(parent=parent)
        self.name = filter_type
        self.tree_manager = project.get_tree_manager()
        self.filter_manager = project.get_filter_manager(filter_type)
        self.outliner_panel = OutlinerPanel(
            self,
            filter_type,
            project,
            parent=self,
        )
        self.outliner = self.outliner_panel.outliner
        self.filter_view = self.outliner_panel.filter_view
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
        if callback_type[0] == CallbackItemType.TREE and self._is_active:
            self.outliner_panel.pre_edit_callback(callback_type, *args)

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        item_type = callback_type[0]
        if item_type != CallbackItemType.FILTER:
            self.filter_manager.clear_filter_caches()
        if (self._is_active and
                item_type in (CallbackItemType.TREE, CallbackItemType.FILTER)):
            self.outliner_panel.post_edit_callback(callback_type, *args)
        self.update()

    def set_active(self, value):
        """Mark tab as active/inactive when the user changes tab.

        Args:
            value (bool): whether to set as inactive.
        """
        self._is_active = value
        self.outliner._is_active = value
        self.filter_view._is_active = value

    def on_tab_changed(self):
        """Callback for when we change to this tab.

        For speed purposes, some updates are done to all tabs (even inactive
        tabs) when editing, and some are only picked up when changing to
        that tab. This should be monitored and may need to change if we
        start to see lags either during edits or when changing tab.
        """
        self.outliner_panel.on_tab_changed()
        self.update()
