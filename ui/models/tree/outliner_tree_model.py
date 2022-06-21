"""Task tree model for outliner."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree import filters
from scheduler.api.tree.task import Task, TaskType
from scheduler.api.tree.task_category import TaskCategory
from ._base_tree_model import BaseTreeModel

from scheduler.ui import constants


class OutlinerTreeModel(BaseTreeModel):
    """Outliner tree model.

    This model is to be used in the task outliner. It's intended to expand
    up to the first task items under each category but not show any subtasks.
    """

    def __init__(
            self,
            tree_manager,
            hide_filtered_items=False,
            parent=None):
        """Initialise task category tree model.

        Args:
            tree_manager (TreeManager): tree manager item.
            hide_filtered_items (bool): if True, use the child_filter from the
                tree manager to filter out all items whose checkboxes are
                deselected in the outliner.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        child_filters = []
        self._hide_filtered_items = hide_filtered_items
        if hide_filtered_items and tree_manager.child_filter:
            child_filters.append(tree_manager.child_filter)
        super(OutlinerTreeModel, self).__init__(
            tree_manager,
            filters=child_filters,
            mime_data_format=constants.OUTLINER_TREE_MIME_DATA_FORMAT,
            parent=parent,
        )

    def data(self, index, role):
        """Get data for given item item and role.

        Args:
            index (QtCore.QModelIndex): index of item item.
            role (QtCore.Qt.Role): role we want data for.

        Returns:
            (QtCore.QVariant): data for given item and role.
        """
        if not index.isValid():
            return QtCore.QVariant()
        if self.get_column_name(index) == self.NAME_COLUMN:
            if role == QtCore.Qt.ItemDataRole.CheckStateRole:
                item = index.internalPointer()
                if item:
                    return not self.tree_manager.is_selected_for_filtering(item)
            if role == QtCore.Qt.ItemDataRole.ForegroundRole:
                item = index.internalPointer()
                if item and self.tree_manager.is_filtered_out(item):
                    return constants.INACTIVE_TEXT_COLOR
            if role == QtCore.Qt.ItemDataRole.FontRole:
                item = index.internalPointer()
                if item:
                    if isinstance(item, TaskCategory):
                        font = QtGui.QFont()
                        font.setBold(True)
                        return font
                    if (isinstance(item, Task)
                            and item.type == TaskType.ROUTINE):
                        font = QtGui.QFont()
                        font.setItalic(True)
                        return font
        return super(OutlinerTreeModel, self).data(index, role)

    def setData(self, index, value, role):
        """Set data at given index to given value.

        Implementing this method allows the tree model to be editable.

        Args:
            index (QtCore.QModelIndex): index of item we're setting data for.
            value (QtCore.QVariant): value to set for data.
            role (QtCore.Qt.Role): role we want to set data for.

        Returns:
            (bool): True if setting data was successful, else False.
        """
        if (role == QtCore.Qt.ItemDataRole.CheckStateRole
                and self.get_column_name(index) == self.NAME_COLUMN):
            if not index.isValid():
                return False
            item = index.internalPointer()
            if not item:
                return False
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
                self.tree_manager.unfilter_item(item)
                if self.tree_manager.ancestor_sibs_selected_for_filter(item):
                    self.tree_manager.unfilter_ancestoral_siblings(item)
                else:
                    self.tree_manager.filter_ancestoral_siblings(item)
            else:
                if self.tree_manager.is_selected_for_filtering(item):
                    self.tree_manager.unfilter_item(item)
                else:
                    self.tree_manager.filter_item(item)
            if self._hide_filtered_items:
                self.set_items_hidden(True)
            self.dataChanged.emit(index, index)
            return True
        return super(OutlinerTreeModel, self).setData(index, value, role)

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        if self.get_column_name(index) == self.NAME_COLUMN:
            flags = (
                QtCore.Qt.ItemFlag.ItemIsSelectable |
                QtCore.Qt.ItemFlag.ItemIsEditable |
                QtCore.Qt.ItemFlag.ItemIsUserCheckable |
                QtCore.Qt.ItemFlag.ItemIsDragEnabled |
                QtCore.Qt.ItemFlag.ItemIsDropEnabled
            )
            item = index.internalPointer()
            parent_item = item.parent
            if parent_item and self.tree_manager.is_filtered_out(parent_item):
                return flags
            return QtCore.Qt.ItemFlag.ItemIsEnabled | flags
        return super(OutlinerTreeModel, self).flags(index)

    def set_items_hidden(self, hide):
        """Hide or unhide filtered items in outliner.

        Args:
            hide (bool): if True, hide items, else unhide them.

        Returns:
            (bool): whether or not action was successful.
        """
        self._hide_filtered_items = hide
        if hide:
            return self.set_filters([self.tree_manager.child_filter])
        else:
            return self.set_filters([])
