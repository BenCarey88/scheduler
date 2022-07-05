"""Task widget for Task Tab."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.widgets.base_tree_view import BaseTreeView
from scheduler.ui.models.tree import TaskTreeModel
from scheduler.ui import utils


class TaskViewWidget(BaseTreeView):
    """Task Tree Widget.

    This widget holds the tree view for the various tasks.
    """
    # TODO: I sense most of this height stuff is actually irrelevant
    # go through and remove any unneeded ones
    HEIGHT_BUFFER = 10
    MIN_WIDTH = 1000

    def __init__(self, tree_manager, task_item, tab, parent=None):
        """Initialise task category widget.

        Args:
            tree_manager (TreeManager): tree manager item.
            task_item (Task): task category tree item.
            tab (TaskTab): task tab this widget is a descendant of.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskViewWidget, self).__init__(tree_manager, parent=parent)
        self._only_delete_current_item = True
        self.tree_manager = tree_manager
        self.task_item = task_item
        self.tab = tab
        tab.task_widget_tree.add_or_update_item(task_item, task_view=self)

        # setup model and delegate
        model = TaskTreeModel(tab.tree_manager, task_item, parent=self)
        self.setItemDelegate(TaskDelegate(model, parent=self))
        self.setModel(model)
        self.expandAll()
        self.setItemsExpandable(False)
        # model.dataChanged.connect(self.tab.update)

        # height = task_item.num_descendants() * TaskDelegate.HEIGHT
        # self.setFixedHeight(height + self.HEIGHT_BUFFER)
        self.setMinimumWidth(self.MIN_WIDTH)
        # self.setSizePolicy(
        #     QtWidgets.QSizePolicy.Policy.MinimumExpanding,
        #     QtWidgets.QSizePolicy.Policy.MinimumExpanding,
        # )
        self.setSizeAdjustPolicy(self.SizeAdjustPolicy.AdjustToContents)
        self.setUniformRowHeights(True)

        # Remove expand decorations and border
        utils.set_style(self, "task_widget.qss")

        # Turn off scrollbar policy or we get flashing scrollbars on update
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        header = self.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.setHeaderHidden(True)
        self.selectionModel().currentChanged.connect(
            partial(self.tab.switch_active_task_view, self.task_item)
        )
        self._current_item = None
        # self.select_subtask_item()

    # def select_subtask_item(self):
    #     """Select the subtask item marked as active in the task tab."""
    #     if (self.tab.selected_subtask_item and
    #             self.task_item.path in self.tab.selected_subtask_item.path):
    #         item_index = self.tab.selected_subtask_item.index()
    #         if item_index is not None:
    #             index = self.model().createIndex(
    #                 item_index,
    #                 0,
    #                 self.tab.selected_subtask_item
    #             )
    #             if index.isValid():
    #                 self.selectionModel().select(
    #                     index,
    #                     self.selectionModel().SelectionFlag.Select
    #                 )
    #                 self.selectionModel().setCurrentIndex(
    #                     index,
    #                     self.selectionModel().SelectionFlag.Select
    #                 )
    #                 self.setFocus(True)
    #                 self.grabKeyboard()

    def begin_reset(self):
        """Begin reset."""
        self._current_item = self._get_current_item()
        self.model().beginResetModel()

    def end_reset(self):
        """End reset."""
        self.model().endResetModel()
        self.expandAll()
        if self._current_item is None:
            return
        row = self._current_item.index()
        if row is None:
            return
        index = self.model().createIndex(row, 0, self._current_item)
        if not index.isValid():
            return
        with utils.suppress_signals(self.selectionModel()):
            self.selectionModel().setCurrentIndex(
                index,
                self.selectionModel().SelectionFlag.SelectCurrent,
            )

    def reset_model(self):
        """Full reset of model."""
        self.begin_reset()
        self.end_reset()

    def sizeHint(self):
        """Get item size hint.

        Returns:
            (QtCore.QSize): size hint.
        """
        size = super(TaskViewWidget, self).sizeHint()
        return QtCore.QSize(size.width(), size.height() + self.HEIGHT_BUFFER)


class TaskDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for task widget tree."""
    HEIGHT = 20

    def __init__(self, model, parent=None):
        """Initialise task delegate item."""
        self._model = model
        super(TaskDelegate, self).__init__(parent=parent)

    def sizeHint(self, option, index):
        """Get size hint for this item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item.

        Returns:
            (QtCore.QSize): size hint.
        """
        return QtCore.QSize(0, self.HEIGHT)

    def createEditor(self, parent, option, index):
        """Create editor widget for edit role.

        Overridding the default purely because this makes the line-edit
        cover the whole row, which I like better.

        Args:
            parent (QtWidgets.QWidget): parent widget.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.

        Returns:
            (QtWidgets.QWidget): editor widget.
        """
        if self._model.get_column_name(index) == self._model.NAME_COLUMN:
            item = index.internalPointer()
            if item:
                editor = QtWidgets.QLineEdit(parent)
                # TODO: is this needed since model sets text anyway?
                editor.setText(item.name)
                return editor
        return super().createEditor(parent, option, index)
