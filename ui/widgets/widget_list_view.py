"""List view of widgets."""

from PyQt5 import QtCore, QtGui, QtWidgets


class WidgetListView(QtWidgets.QListView):
    """Base list view showing list of other widgets"""
    ITEM_SPACING = 5

    def __init__(self, widget_list, parent=None):
        """Initialize class instance.

        Args:
            widget_list (list(QtWidgets.QWidget)): list of widgets to show.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(WidgetListView, self).__init__(parent=parent)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.widget_list = widget_list
        model = WidgetListModel(["" for _ in widget_list])
        self.setModel(model)
        self.setItemDelegate(WidgetListDelegate(self))
        self.setSpacing(self.ITEM_SPACING)
        self.open_editors()

    def insert_widget(self, widget, row):
        """Insert widget at given row.

        Args:
            widget (QtWidgets.QWidget): widget to insert.
            row (int): row to insert at.
        """
        self.model().insert_widget(widget, row)

    def remove_widget(self, row):
        """Remove widget at given row.

        Args:
            widget (QtWidgets.QWidget): widget to insert.
            row (int): row to remove widget from.
        """
        self.model().remove_widget(row)

    def move_widget(self, old_row, new_row):
        """Move widget to new row.

        Args:
            old_row (int): row widget starts at.
            new_row (int): row to move widget to.
        """
        self.model().move_widget(old_row, new_row)

    def resizeEvent(self, event):
        """Resize event.

        Args:
            event (QtCore.QEvent): the event.
        """
        super(WidgetListView, self).resizeEvent(event)
        self.updateEditorGeometries()

    def open_editor(self, row, update=True):
        """Open persistent editors on given row.

        This should be called whenever the widget on that row needs to be
        updated.

        Args:
            row (int or None): if given, only open editor on this row.
            update (bool): if True, update viewport afterwards.
        """
        index = self.model().index(row, 0, QtCore.QModelIndex())
        if index.isValid():
            if self.isPersistentEditorOpen(index):
                self.closePersistentEditor(index)
            self.openPersistentEditor(index)
            self.update(index)
        if update:
            self.scheduleDelayedItemsLayout()

    def open_editors(self):
        """Open persistent editors on each row.

        Args:
            row (int or None): if given, only open editor on this row.
        """
        for row, _ in enumerate(self.widget_list):
            self.open_editor(row, update=False)
        self.scheduleDelayedItemsLayout()


class WidgetListModel(QtCore.QAbstractListModel):
    """Model to be used by widget list view."""
    def __init__(self, widget_list, parent=None):
        """Initialize model.

        Args:
            widget_list (list(QtWidgets.QWidget)): list of widgets.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(WidgetListModel, self).__init__(parent=parent)
        self.widget_list = widget_list

    def rowCount(self, parent=None):
        """Get number of rows."""
        return len(self.widget_list)

    def data(self, index, role):
        """Get data.

        Args:
            index (QtCore.QModelIndex): index to get data for.
            role (int): data role.

        Returns:
            (QVariant): data.
        """
        return QtCore.QVariant()

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

    def insert_widget(self, widget, row):
        """Insert widget at given row.

        Args:
            widget (QtWidgets.QWidget): widget to insert.
            row (int): row to insert at.
        """
        if 0 <= row <= len(self.widget_list):
            self.beginInsertRows(QtCore.QModelIndex(), row, row)
            self.widget_list.insert(row, widget)
            self.endInsertRows()

    def remove_widget(self, row):
        """Remove widget at given row.

        Args:
            widget (QtWidgets.QWidget): widget to insert.
            row (int): row to remove widget from.
        """
        if 0 <= row < len(self.widget_list):
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            self.widget_list.pop(row)
            self.endRemoveRows()

    def move_widget(self, old_row, new_row):
        """Move widget to new row.

        Args:
            old_row (int): row widget starts at.
            new_row (int): row to move widget to.
        """
        if (0 <= old_row < len(self.widget_list)
                and 0 <= old_row < len(self.widget_list)):
            # TODO: work out if we need to +-1 to new_row if > old_row
            self.beginMoveRows(
                QtCore.QModelIndex(),
                old_row,
                old_row,
                QtCore.QModelIndex(),
                new_row,
                new_row,
            )
            widget = self.widget_list.pop(old_row)
            self.widget_list.insert(new_row, widget)
            self.endMoveRows()


class WidgetListDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for multi-list view."""
    WIDTH_BUFFER = 10

    def __init__(self, widget_list_view, parent=None):
        """Initialise delegate item.

        Args:
            widget_list_view (WidgetListView): the widget list view this is
                a delegate for.
            parent (QtWidgets.QWidget or None): Qt parent of delegate.
        """
        super(WidgetListDelegate, self).__init__(parent)
        self.widget_list = widget_list_view.widget_list
        self.widget_list_view = widget_list_view

    def sizeHint(self, option, index):
        """Get size hint for delegate.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index to get size hint for.
        """
        widget = self.widget_list[index.row()]
        return widget.sizeHint()

    def createEditor(self, parent, option, index):
        """Create editor widget for edit role.

        Args:
            parent (QtWidgets.QWidget): parent widget.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.

        Returns:
            (QtWidgets.QWidget): editor widget.
        """
        widget = self.widget_list[index.row()]
        widget.setParent(parent)
        widget.setMaximumWidth(parent.width())
        return widget

    def destroyEditor(self, editor, index):
        """Override destroyEditor so that editor widgets aren't destroyed."""
        pass

    def updateEditorGeometry(self, editor, option, index):
        """Update editor geometry.

        Args:
            editor (QtWidgets.QWidget): the editor.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): the index of the editor.
        """
        editor.setFixedWidth(editor.parent().width() - self.WIDTH_BUFFER)
        return super().updateEditorGeometry(editor, option, index)
