"""Planner list view."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.calendar.planned_item import PlannedItem
from scheduler.api.constants import TimePeriod
from scheduler.api.edit.edit_callbacks import CallbackItemType, CallbackType

from scheduler.ui.models.list import PlannerListModel
from scheduler.ui.tabs.base_calendar_view import (
    BaseListView,
    BaseTitledView,
)


class TitledPlannerListView(BaseTitledView):
    """Planner list view with title."""
    HOVERED_ITEM_SIGNAL = QtCore.pyqtSignal(PlannedItem)
    HOVERED_ITEM_REMOVED_SIGNAL = QtCore.pyqtSignal()

    def __init__(
            self,
            name,
            project,
            time_period,
            parent=None):
        """Initialise planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            time_period (TimePeriod): type of time period to
                view over.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        self.planner_list_view = PlannerListView(name, project, time_period)
        super(TitledPlannerListView, self).__init__(
            name,
            project,
            self.planner_list_view,
            parent=parent,
        )
        self.planner_list_view.installEventFilter(self)
        self.hide_day_change_buttons = (time_period == TimePeriod.WEEK)

    def setup(self):
        """Additional setup after tab init."""
        super(TitledPlannerListView, self).setup()
        self.planner_list_view.HOVERED_ITEM_SIGNAL.connect(
            self.HOVERED_ITEM_SIGNAL.emit
        )
        self.planner_list_view.HOVERED_ITEM_REMOVED_SIGNAL.connect(
            self.HOVERED_ITEM_REMOVED_SIGNAL.emit
        )

    def eventFilter(self, obj, event):
        """Event filter for when object is clicked.

        Args:
            obj (QtCore.QObject): QObject that event is happening on.
            event (QtCore.QEvent): event that is happening.
        """
        if (obj == self.planner_list_view
                and event.type() == QtCore.QEvent.Leave):
            self.planner_list_view.hovered_item = None
            self.planner_list_view.HOVERED_ITEM_REMOVED_SIGNAL.emit()
        return False


class PlannerListView(BaseListView):
    """Planner list view."""
    HOVERED_ITEM_SIGNAL = QtCore.pyqtSignal(PlannedItem)
    HOVERED_ITEM_REMOVED_SIGNAL = QtCore.pyqtSignal()

    RECT_TEXT_WIDTH_BUFFER = 45

    def __init__(
            self,
            name,
            project,
            time_period,
            parent=None):
        """Initialise planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            time_period (TimePeriod): type of time period to view over.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        self.open_dialog_on_drop_event = False
        self.planner_manager = project.get_planner_manager(name)
        model = PlannerListModel(
            project.get_tree_manager(name),
            self.planner_manager,
            time_period=time_period,
            open_dialog_on_drop_event=self.open_dialog_on_drop_event,
        )
        super(PlannerListView, self).__init__(
            name,
            project,
            model,
            parent=parent,
        )
        self.hovered_item = None
        self.setUniformRowHeights(True)

        self.setSizeAdjustPolicy(self.SizeAdjustPolicy.AdjustToContents)

        header = self.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)

        for column in range(self.model().columnCount()):
            self.resizeColumnToContents(column)

        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)        
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)

        self.setSortingEnabled(True)
        model.rowsInserted.connect(self.VIEW_UPDATED_SIGNAL.emit)
        model.rowsRemoved.connect(self.VIEW_UPDATED_SIGNAL.emit)
        model.rowsMoved.connect(self.VIEW_UPDATED_SIGNAL.emit)
        model.dataChanged.connect(self.VIEW_UPDATED_SIGNAL.emit)
        model.modelReset.connect(self.VIEW_UPDATED_SIGNAL.emit)

    def on_view_changed(self):
        """Callback for when this view is loaded."""
        super(PlannerListView, self).on_view_changed()
        self.model().beginResetModel()
        self.model().endResetModel()

    def on_outliner_filter_changed(self, *args):
        """Callback for what to do when filter is changed in outliner."""
        super(PlannerListView, self).on_outliner_filter_changed(*args)
        self.model().beginResetModel()
        self.model().endResetModel()

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(PlannerListView, self).pre_edit_callback(callback_type, *args)
        if not self._is_active:
            return
        if callback_type in [CallbackType.TREE_REMOVE, CallbackType.TREE_ADD]:
            self.model().pre_full_update()
        if callback_type[0] != CallbackItemType.PLANNER:
            return

        if callback_type == CallbackType.PLANNER_ADD:
            item, calendar_period, row = args
            if calendar_period == self.calendar_period:
                self.model().pre_item_added(item, row)

        elif callback_type == CallbackType.PLANNER_REMOVE:
            item, calendar_period, row = args
            if calendar_period == self.calendar_period:
                self.model().pre_item_removed(item, row)

        elif callback_type == CallbackType.PLANNER_MOVE:
            item, old_period, old_row, new_period, new_row = args
            if old_period == new_period == self.calendar_period:
                self.model().pre_item_moved(item, old_row, new_row)
            elif old_period == self.calendar_period:
                self.model().pre_item_removed(item, old_row)
            elif new_period == self.calendar_period:
                self.model().pre_item_added(item, new_row)

        elif callback_type == CallbackType.PLANNER_MODIFY:
            item, period, row, new_item, new_period, new_row = args
            if period == new_period == self.calendar_period and row != new_row:
                self.model().pre_item_moved(item, row, new_row)
            elif period == self.calendar_period:
                self.model().pre_item_removed(item, row)
            elif new_period == self.calendar_period:
                self.model().pre_item_added(new_item, new_row)

        elif callback_type == CallbackType.PLANNER_FULL_UPDATE:
            calendar_period = args[0]
            if calendar_period == self.calendar_period:
                self.model().pre_full_update()

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(PlannerListView, self).post_edit_callback(callback_type, *args)
        if not self._is_active:
            return
        if callback_type in [CallbackType.TREE_REMOVE, CallbackType.TREE_ADD]:
            self.model().on_full_update()
        if callback_type[0] != CallbackItemType.PLANNER:
            return

        if callback_type == CallbackType.PLANNER_ADD:
            item, calendar_period, row = args
            if calendar_period == self.calendar_period:
                self.model().on_item_added(item, row)

        elif callback_type == CallbackType.PLANNER_REMOVE:
            item, calendar_period, row = args
            if calendar_period == self.calendar_period:
                self.model().on_item_removed(item, row)

        elif callback_type == CallbackType.PLANNER_MOVE:
            item, old_period, old_row, new_period, new_row = args
            if old_period == new_period == self.calendar_period:
                self.model().on_item_moved(item, old_row, new_row)
            elif old_period == self.calendar_period:
                self.model().on_item_removed(item, old_row)
            elif new_period == self.calendar_period:
                self.model().on_item_added(item, new_row)

        elif callback_type == CallbackType.PLANNER_MODIFY:
            item, period, row, new_item, new_period, new_row = args
            if period == new_period == self.calendar_period:
                if row != new_row:
                    self.model().on_item_moved(item, row, new_row)
                else:
                    self.model().on_item_modified(item, new_item)
            elif period == self.calendar_period:
                self.model().on_item_removed(item, row)
            elif new_period == self.calendar_period:
                self.model().on_item_added(new_item, new_row)

        elif callback_type == CallbackType.PLANNER_FULL_UPDATE:
            calendar_period = args[0]
            if calendar_period == self.calendar_period:
                self.model().on_full_update()

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        modifiers = event.modifiers()

        if not modifiers:
            # del: remove item
            if event.key() == QtCore.Qt.Key_Delete:
                current_index = self.currentIndex()
                if current_index is not None:
                    if self.model().remove_item(current_index, force=False):
                        self.update()

        elif modifiers == QtCore.Qt.ControlModifier:
            # ctrl+del: force remove item
            if event.key() == QtCore.Qt.Key_Delete:
                current_index = self.currentIndex()
                if current_index is not None:
                    if self.model().remove_item(current_index, force=True):
                        self.update()

        super(PlannerListView, self).keyPressEvent(event)

    def get_rect_for_item(
            self,
            planned_item,
            relative_to=None,
            stop_at_text_end=False,
            x_max=None,
            y_max=None):
        """Get rect corresponding to planned item.

        Args:
            planned_item (PlannedItem): planned item.
            relative_to (QtCore.QWidget or None): widget to set it relative to.
                If None
            stop_at_text_end (bool): if True, bound the rectangle by the end
                of the text.
            x_max (int or None): max x value, if given.
            y_max (int or None): max y value, if given.

        Returns:
            (QtCore.QRectF or None): rectangle for item if found, either in
                this widget's view space, or relative to given widget.
        """
        row = planned_item.index()
        if row is None:
            return None
        column = self.model().columnCount(QtCore.QModelIndex()) - 1
        index_start = self.model().index(row, 0, QtCore.QModelIndex())
        index_end = self.model().index(row, column, QtCore.QModelIndex())
        if not index_start.isValid() or not index_end.isValid():
            return None
        rect_start = self.visualRect(index_start)
        rect_end = self.visualRect(index_end)

        if stop_at_text_end:
            text = self.model().data(
                index_end,
                QtCore.Qt.ItemDataRole.DisplayRole,
            )
            label = QtWidgets.QLabel()
            label.setText(text)
            rect_end = QtCore.QRect(
                rect_end.left(),
                rect_end.top(),
                label.sizeHint().width() + self.RECT_TEXT_WIDTH_BUFFER,
                rect_end.height(),
            )
            label.deleteLater()

        if relative_to is None:
            top_left = rect_start.topLeft()
            bottom_right = rect_end.bottomRight()
        else:
            top_left = self.viewport().mapTo(
                relative_to,
                rect_start.topLeft()
            )
            bottom_right = self.viewport().mapTo(
                relative_to,
                rect_end.bottomRight()
            )
        bottom = (
            bottom_right.y() if y_max is None
            else min(bottom_right.y(), y_max)
        )
        right = (
            bottom_right.x() if x_max is None
            else min(bottom_right.x(), x_max)
        )
        return QtCore.QRectF(
            top_left,
            QtCore.QPoint(right, bottom),
        )

    def mouseMoveEvent(self, event):
        """Override mouse move event to highlight connections.

        Args:
            event (QtCore.QEvent): the mouse move event.
        """
        index = self.indexAt(event.pos())
        planned_item = index.internalPointer()
        if planned_item is not None:
            self.hovered_item = planned_item
            self.HOVERED_ITEM_SIGNAL.emit(planned_item)
        elif self.hovered_item is not None:
            self.hovered_item = None
            self.HOVERED_ITEM_REMOVED_SIGNAL.emit()
        super(PlannerListView, self).mouseMoveEvent(event)
