"""Planner list view."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.calendar.planned_item import (
    PlannedItemImportance,
    PlannedItemSize,
)

from scheduler.ui.models.list import PlannerListModel
from scheduler.ui.tabs.base_calendar_view import BaseListView


class PlannerListView(BaseListView):
    """Tracker table view."""
    def __init__(self, name, project, time_period, parent=None):
        """Initialise planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            time_period (PlannedItemTimePeriod): type of time period to
                view over.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        self.open_dialog_on_drop_event = False
        self.planner_manager = project.get_planner_manager()
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

        self.header().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        for column in range(self.model().columnCount()):
            self.resizeColumnToContents(column)

        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)        
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)

        self.setSortingEnabled(True)

        self.setItemDelegate(
            PlannedItemDelegate(
                self.planner_manager,
                self.tree_manager,
                model,
            )
        )
        self.open_editors()
        model.modelReset.connect(self.update)
        model.dataChanged.connect(self.update)

    def resizeEvent(self, event):
        """Resize event.

        Args:
            event (QtCore.QEvent): the event.
        """
        super(PlannerListView, self).resizeEvent(event)
        self.open_editors()

    def open_editors(self):
        """Open persistent editors on each column."""
        model = self.model()
        for i in range(model.rowCount()):
            for j in range(model.columnCount()):
                index = model.index(i, j, QtCore.QModelIndex())
                if (model.get_column_name(index) not in
                        [model.IMPORTANCE_COLUMN, model.SIZE_COLUMN]):
                    continue
                if index.isValid():
                    if self.isPersistentEditorOpen(index):
                        self.closePersistentEditor(index)
                    self.openPersistentEditor(index)

    def update(self):
        """Update view."""
        self.open_editors()
        super(PlannerListView, self).update()

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


class PlannedItemDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for planned items."""
    def __init__(
            self,
            planner_manager,
            tree_manager,
            model,
            parent=None):
        """Initialise planned item delegate item.

        Args:
            planner_manager (PlannerManager): planner manager object.
            tree_manager (TreeManager): tree manager object.
            model (QtCore.QAbstractItemModel): the model this is modelling.
            parent (QtWidgets.QWidget or None): Qt parent of delegate.
        """
        super(PlannedItemDelegate, self).__init__(parent)
        self.model = model
        self.planner_manager = planner_manager
        self.tree_manager = tree_manager

    def createEditor(self, parent, option, index):
        """Create editor widget for edit role.

        Args:
            parent (QtWidgets.QWidget): parent widget.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.

        Returns:
            (QtWidgets.QWidget): editor widget.
        """
        column_name = self.model.get_column_name(index)
        if column_name == self.model.IMPORTANCE_COLUMN:
            editor_widget = QtWidgets.QComboBox(parent=parent)
            editor_widget.addItem("")
            editor_widget.addItems(PlannedItemImportance.VALUES_LIST)
            return editor_widget
        elif column_name == self.model.SIZE_COLUMN:
            editor_widget = QtWidgets.QComboBox(parent=parent)
            editor_widget.addItem("")
            editor_widget.addItems(PlannedItemSize.VALUES_LIST)
            return editor_widget
        return super(PlannedItemDelegate, self).createEditor(
            parent,
            option,
            index,
        )
