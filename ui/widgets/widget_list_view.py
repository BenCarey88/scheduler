"""List view of widgets."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.utils import fallback_value


class WidgetListView(QtWidgets.QListView):
    """Base list view showing list of other widgets"""
    ITEM_SPACING = 5
    WIDGET_MARGIN_BUFFER = 2
    SCROLL_BAR_STEP = 20

    def __init__(self, widget_list, item_spacing=None, parent=None):
        """Initialize class instance.

        Args:
            widget_list (list(QtWidgets.QWidget)): list of widgets to show.
            item_spacing (int): vertical spacing for widgets.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(WidgetListView, self).__init__(parent=parent)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(self.SCROLL_BAR_STEP)
        self._widget_list = []
        self._has_spacers = (item_spacing is not None)
        self._item_spacing = item_spacing
        for i, widget in enumerate(widget_list):
            if self._has_spacers:
                self._widget_list.append(
                    Spacer(item_spacing, enable=(i != 0))
                )
            self._widget_list.append(widget)

        model = WidgetListModel(["" for _ in self._widget_list])
        self.setModel(model)
        self.setItemDelegate(WidgetListDelegate(self))
        self.setSpacing(self.ITEM_SPACING)
        self.open_editors()

    def get_widgets(self):
        """Get non-gap widgets.

        Returns:
            (list(QtWidget.QWidget)): the widgets.
        """
        if self._has_spacers:
            return self._widget_list[1::2]
        return self._widget_list

    def iter_widgets(self):
        """Iterate through non-gap widgets.

        Yields:
            (QtWidget.QWidget): the widgets.
        """
        if self._has_spacers:
            for widget in self._widget_list[1::2]:
                yield widget
        else:
            for widget in self._widget_list:
                yield widget

    def get_widget(self, index):
        """Get widget at index (ignoring gap-widgets).

        Returns:
            (QtWidget.QWidget or None): the widget, if found.
        """
        if self._has_spacers:
            if 0 <= 2 * index < len(self._widget_list):
                return self._widget_list[2 * index + 1]
            elif -len(self._widget_list) <= 2 * index < 0:
                return self._widget_list[2 * (index + 1) - 1]
        else:
            if -len(self._widget_list) <= index < len(self._widget_list):
                return self._widget_list[index]
        return None

    def _row_is_in_range(self, row, allow_equal=False):
        """Check if given row is within range of widget list.

        Args:
            row (int): row to check.
            allow_equal (bool): if True, we count a row as in range if it's
                equal to the number of widgets.

        Returns:
            (bool): whether or not row is in range.
        """
        if self._has_spacers:
            row = 2 * row
        if allow_equal:
            return 0 <= row <= len(self._widget_list)
        else:
            return 0 <= row < len(self._widget_list)

    def insert_widget(self, row, widget):
        """Insert widget at given row.

        Args:
            row (int): row to insert at.
            widget (QtWidgets.QWidget): widget to insert.
        """
        if not self._row_is_in_range(row, allow_equal=True):
            return
        if self._has_spacers:
            if row == 0 and len(self._widget_list > 0):
                # enable first spacer if we're adding a new first one
                self._widget_list[0].enable()
            spacer = Spacer(self._item_spacing, row != 0)
            self.model().insert_widgets(2 * row, [spacer, widget])
        else:
            self.model().insert_widgets(row, [widget])

    def remove_widget(self, row):
        """Remove widget at given row.

        Args:
            widget (QtWidgets.QWidget): widget to insert.
            row (int): row to remove widget from.
        """
        if not self._row_is_in_range(row):
            return
        if self._has_spacers:
            if row == 0 and len(self._widget_list > 2):
                # disable second spacer if we're removing first one
                self._widget_list[2].disable()
            self.model().remove_widgets(2 * row, 2)
        else:
            self.model().remove_widgets(row, 1)

    def move_widget(self, old_row, new_row):
        """Move widget to new row.

        Args:
            old_row (int): row widget starts at.
            new_row (int): row to move widget to.
        """
        if (old_row == new_row
                or not self._row_is_in_range(old_row) 
                or not self._row_is_in_range(new_row)):
            return
        if self._has_spacers:
            if old_row == 0:
                # if moving first spacer, enable it and disable second one
                self._widget_list[0].enable()
                self._widget_list[2].disable()
            if new_row == 0:
                # if moving before first spacer, enable it and disable new one
                self._widget_list[0].enable()
                self._widget_list[2 * old_row].disable()
            self.model().move_widgets(2 * old_row, 2 * new_row, 2)
        else:
            self.model().move_widgets(old_row, new_row, 1)

    def resizeEvent(self, event):
        """Resize event.

        Args:
            event (QtCore.QEvent): the event.
        """
        super(WidgetListView, self).resizeEvent(event)
        self.updateEditorGeometries()
        self.scheduleDelayedItemsLayout()

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
        for row, _ in enumerate(self._widget_list):
            self.open_editor(row, update=False)
        self.scheduleDelayedItemsLayout()

    def sizeHint(self):
        """Get size hint.

        Returns:
            (QtCore.QSize): size hint.
        """
        widget_heights = sum([
            w.sizeHint().height() + self.WIDGET_MARGIN_BUFFER
            for w in self._widget_list
        ])
        spacing_heights = self.ITEM_SPACING * (2 * len(self._widget_list))
        height = widget_heights + spacing_heights
        width = super(WidgetListView, self).sizeHint().width()
        return QtCore.QSize(width, height)


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

    def flags(self, index):
        """Get item flags.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        return QtCore.Qt.ItemFlag.ItemIsEnabled

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

    def insert_widgets(self, row, widgets):
        """Insert widgets at given row.

        Args:
            row (int): row to insert at.
            widgets (list(QtWidgets.QWidget) or QtWidgets.QWidget): widget
                or widgets to insert.
        """
        if not isinstance(widgets, list):
            widgets = [widgets]
        if len(widgets) > 0 and 0 <= row <= len(self.widget_list):
            self.beginInsertRows(
                QtCore.QModelIndex(),
                row,
                row + len(widgets) - 1
            )
            self.widget_list[row:row] = widgets
            self.endInsertRows()

    def remove_widgets(self, row, num_rows_to_remove=1):
        """Remove widgets at given row.

        Args:
            row (int): row to remove widget from.
            num_rows_to_remove (int): number of subsequent rows to
                remove from.
        """
        if (0 <= row < len(self.widget_list)
                and num_rows_to_remove > 0
                and row + num_rows_to_remove <= len(self.widget_list)):
            self.beginRemoveRows(
                QtCore.QModelIndex(),
                row,
                row + num_rows_to_remove - 1,
            )
            del self.widget_list[row : row + num_rows_to_remove]
            self.endRemoveRows()

    def move_widgets(self, old_row, new_row, num_rows_to_move=1):
        """Move widget to new row.

        Args:
            old_row (int): row widgets start at.
            new_row (int): row to move widgets to. This is the index
                we want the first of the moved widgets to have after
                moving (note this conflicts with the new_row arg in
                Qt's beginMoveRows, which is the index before the item
                that we want to move the widgets to sit behind (or the
                length of the list if we want to move it to the end)).
            num_rows_to_move (int): number of subsequent rows to move.
        """
        if (0 <= old_row < len(self.widget_list)
                and 0 <= new_row < len(self.widget_list)
                and old_row != new_row
                and old_row + num_rows_to_move <= len(self.widget_list)
                and new_row + num_rows_to_move <= len(self.widget_list)):
            if new_row > old_row:
                new_row += num_rows_to_move
            self.beginMoveRows(
                QtCore.QModelIndex(),
                old_row,
                old_row + num_rows_to_move - 1,
                QtCore.QModelIndex(),
                new_row,
            )
            widgets_to_move = self.widget_list[
                old_row : old_row + num_rows_to_move
            ]
            del self.widget_list[old_row : num_rows_to_move]
            self.widget_list[new_row:new_row] = widgets_to_move
            self.endMoveRows()


class Spacer(QtWidgets.QFrame):
    """Simple widget to act as a spacer in the widget list."""
    def __init__(self, spacing, enable=True, parent=None):
        """Initalize.

        Args:
            spacing (int): spacing to set.
            enable (bool): whether or not to enable the item.
            parent (QtWidgets.QWidget or None): parent item.
        """
        super(Spacer, self).__init__(parent=parent)
        self._spacing = spacing
        self._main_layout = QtWidgets.QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self.setLayout(self._main_layout)
        self._add_spacer(spacing if enable else 0)

    def _add_spacer(self, spacing):
        """Add spacer item.

        Args:
            spacing (int): spacing for item.
        """
        self._spacer = QtWidgets.QSpacerItem(spacing, spacing)
        self._main_layout.addSpacerItem(self._spacer)

    def _remove_spacer(self):
        """Remove spacer item."""
        self._main_layout.removeItem(self._spacer)
        self._spacer = None

    def enable(self):
        """Enable spacer."""
        self._remove_spacer()
        self._add_spacer(self._spacing)

    def disable(self):
        """Disable spacer."""
        self._remove_spacer()
        self._add_spacer(0)


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
        self.widget_list = widget_list_view._widget_list
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
        # editor.setFixedHeight(1000)
        # print ("Updating")
        return super().updateEditorGeometry(editor, option, index)
