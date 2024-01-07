"""Tracker timetable view."""

from PyQt5 import QtCore, QtWidgets

from scheduler.api.edit.edit_callbacks import CallbackType as CT

from scheduler.ui.models.list import HistoryListModel
from scheduler.ui.models.table import HistoryWeekModel
from scheduler.ui.tabs.base_calendar_view import BaseWeekTableView

from scheduler.ui import utils


class HistoryTimeTableView(BaseWeekTableView):
    """Tracker table view."""
    def __init__(self, name, project, num_days=7, parent=None):
        """Initialise tracker table view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            num_days (int): num days to use.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(HistoryTimeTableView, self).__init__(
            name,
            project,
            HistoryWeekModel(project.calendar, num_days=num_days),
            parent=parent,
        )
        self.history_manager = project.get_history_manager()
        self.setItemDelegate(HistoryDelegate(self))
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.open_editors()

    def on_view_changed(self):
        """Callback for when this view is loaded."""
        super(HistoryTimeTableView, self).on_view_changed()
        self.model().beginResetModel()
        self.model().endResetModel()
        self.update()

    def on_outliner_filter_changed(self, *args):
        """Callback for what to do when filter is changed in outliner."""
        super(HistoryTimeTableView, self).on_outliner_filter_changed(*args)
        self.model().beginResetModel()
        self.model().endResetModel()
        self.update()

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(HistoryTimeTableView, self).pre_edit_callback(
            callback_type,
            *args,
        )
        if (self._is_active
                and callback_type in [CT.TREE_MODIFY, CT.TREE_REMOVE]):
            self.model().beginResetModel()

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(HistoryTimeTableView, self).post_edit_callback(
            callback_type,
            *args,
        )
        if (self._is_active
                and callback_type in [CT.TREE_MODIFY, CT.TREE_REMOVE]):
            self.model().endResetModel()
            self.update()

    def update(self):
        """Update widget and viewport."""
        self.open_editors()
        super(HistoryTimeTableView, self).update()

    def resize_table(self):
        """Resize table view."""
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def resizeEvent(self, event):
        """Resize event.

        Args:
            event (QtCore.QEvent): the event.
        """
        super(HistoryTimeTableView, self).resizeEvent(event)
        self.open_editors()
        self.resize_table()

    def open_editors(self):
        """Open persistent editors on each column."""
        model = self.model()
        for i in range(model.num_rows):
            for j in range(model.num_cols):
                index = model.index(i, j, QtCore.QModelIndex())
                if index.isValid():
                    if self.isPersistentEditorOpen(index):
                        self.closePersistentEditor(index)
                    self.openPersistentEditor(index)
        self.viewport().update()

    def row_count(self):
        """Get number of rows of table.

        Returns:
            (int): number of rows.
        """
        return self.model().rowCount(QtCore.QModelIndex())

    def column_count(self):
        """Get number of columns of table.

        Returns:
            (int): number of columns.
        """
        return self.model().columnCount(QtCore.QModelIndex())


class HistoryDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for history view."""
    def __init__(self, table, parent=None):
        """Initialise task delegate item.
        
        Args:
            table (QtWidgets.QTableView): table widget this is delegate of.
            parent (QtWidgets.QWidget or None): Qt parent of delegate.
        """
        super(HistoryDelegate, self).__init__(parent)
        self.table = table
        self.tree_manager = table.tree_manager
        self.history_manager = table.history_manager
        self.filter_manager = table.filter_manager

    @property
    def calendar_week(self):
        """Get calendar week.

        Implemented as a property to stay up to date  with parent class.

        Returns:
            (CalendarWeek): calendar week
        """
        return self.table.calendar_week

    def sizeHint(self, option, index):
        """Get size hint for this item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item.

        Returns:
            (QtCore.QSize): size hint.
        """
        return self.get_fixed_size()

    def get_fixed_size(self):
        """Get fixed size for widgets.

        Returns:
            (QtCore.QSize): size hint.
        """
        table_size = self.table.viewport().size()
        line_width = 1
        rows = self.table.row_count() or 1
        cols = self.table.column_count() or 1
        width = (table_size.width() - (line_width * (cols - 1))) / cols
        height = (table_size.height() -  (line_width * (rows - 1))) / rows
        return QtCore.QSize(width, height)

    def createEditor(self, parent, option, index):
        """Create editor widget for edit role.

        Args:
            parent (QtWidgets.QWidget): parent widget.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.

        Returns:
            (QtWidgets.QWidget): editor widget.
        """
        calendar_day = self.calendar_week.get_day_at_index(index.column())
        editor_widget = QtWidgets.QTreeView(parent=parent)
        editor_widget.setFixedSize(self.get_fixed_size())
        editor_widget.setModel(
            HistoryListModel(
                self.tree_manager,
                self.history_manager,
                self.filter_manager,
                calendar_day,
            )
        )
        editor_widget.setHeaderHidden(True)
        editor_widget.setItemsExpandable(False)

        editor_widget.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        editor_widget.setDragEnabled(True)
        editor_widget.setDropIndicatorShown(True)
        editor_widget.viewport().setAcceptDrops(True)

        utils.set_style(editor_widget, "history_delegate.qss")
        return editor_widget
