"""Filter view for viewing filters."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.edit.edit_callbacks import CallbackItemType

from .filter_dialog import FilterDialog


class FilterView(QtWidgets.QListView):
    """Filter view."""
    def __init__(self, tree_manager, outliner, parent=None):
        """Initialize filter view.

        Args:
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner view this filter applies to.
            parent (QtWidgets.QWidget or None): parent widget, if given.
        """
        super(FilterView, self).__init__(parent=parent)
        self.setModel(FilterListModel(tree_manager, outliner))
        self.setItemDelegate(FilterItemDelegate(tree_manager, self))
        self.outliner = outliner
        self._is_active = False

    def reset_model(self):
        """Reset model."""
        self.model().beginResetModel()
        self.model().endResetModel()

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        if self._is_active and callback_type[0] == CallbackItemType.FILTER:
            self.reset_model()

    def on_tab_changed(self):
        """Callback for when we change to this tab.

        For speed purposes, some updates are done to all tabs (even inactive
        tabs) when editing, and some are only picked up when changing to
        that tab. This should be monitored and may need to change if we
        start to see lags either during edits or when changing tab.
        """
        self.reset_model()


class FilterListModel(QtCore.QAbstractListModel):
    """List model for filter view."""
    def __init__(self, tree_manager, outliner, parent=None):
        """Initialize model.

        Args:
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner view this filter applies to.
            parent (QtGui.QWidget or None): parent widget, if given.
        """
        super(FilterListModel, self).__init__(parent=parent)
        self.tree_manager = tree_manager
        self.outliner = outliner

    def rowCount(self, parent=None):
        """Get number of rows."""
        return len(self.tree_manager.field_filters_dict)

    def _get_filter_from_index(self, index):
        """Get filter name for given model index.

        Args:
            index (QtCore.QModelIndex): index to query.

        Returns:
            (BaseFilter or None): filter at given index, if found.
        """
        row = index.row()
        if 0 <= row < len(self.tree_manager.field_filters_dict):
            return list(self.tree_manager.field_filters_dict.values())[row]
        return None

    def data(self, index, role):
        """Get data.

        Args:
            index (QtCore.QModelIndex): index to get data for.
            role (int): data role.

        Returns:
            (QVariant): data.
        """
        text_roles = [
            QtCore.Qt.ItemDataRole.DisplayRole,
            QtCore.Qt.ItemDataRole.EditRole,
        ]
        if role in text_roles + [QtCore.Qt.ItemDataRole.CheckStateRole]:
            filter_ = self._get_filter_from_index(index)
            if filter_ is not None:
                if role in text_roles:
                    return filter_.name
                if role == QtCore.Qt.ItemDataRole.CheckStateRole:
                    return 2 * (self.tree_manager.field_filter == filter_)
        return QtCore.QVariant()

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
        if (role == QtCore.Qt.ItemDataRole.CheckStateRole):
            if not index.isValid():
                return False
            filter_ = self._get_filter_from_index(index)
            if not filter_:
                return False
            self.tree_manager.set_active_field_filter(
                filter_ if value else None
            )
            self.outliner.on_field_filter_changed()
            return True
        return super(FilterListModel, self).setData(index, value, role)

    def flags(self, index):
        """Get item flags.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        return (
            QtCore.Qt.ItemFlag.ItemIsEnabled |
            QtCore.Qt.ItemFlag.ItemIsSelectable |
            QtCore.Qt.ItemFlag.ItemIsEditable |
            QtCore.Qt.ItemFlag.ItemIsUserCheckable
        )

    def headerData(self, section, orientation, role):
        """Get header data.

        Args:
            section (int): header section.
            orientation (QtCore.Qt.Orientation): header orientation.
            role (int): header role.

        Returns:
            (QVariant): header data.
        """
        return QtCore.QVariant()


class FilterItemDelegate(QtWidgets.QStyledItemDelegate):
    """Filter item delegate."""
    def __init__(self, tree_manager, filter_view, parent=None):
        """Initialise delegate item.

        Args:
            tree_manager (TreeManager): tree manager object.
            filter_view (FilterView): the view.
            parent (QtWidgets.QWidget or None): Qt parent of delegate.
        """
        super(FilterItemDelegate, self).__init__(parent)
        self.tree_manager = tree_manager
        self.view = filter_view

    def createEditor(self, parent, option, index):
        """Create editor widget for edit role.

        Args:
            parent (QtWidgets.QWidget): parent widget.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.

        Returns:
            (QtWidgets.QWidget): editor widget.
        """
        row = index.row()
        if row >= 0:
            filter_ = list(self.tree_manager.field_filters_dict.values())[row]
            dialog = FilterDialog(self.tree_manager, filter_, parent=parent)
            return dialog
        return super(FilterItemDelegate, self).createEditor(
            parent,
            option,
            index,
        )
