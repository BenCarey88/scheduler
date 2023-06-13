"""Task widget for Task Tab."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.enums import ItemImportance, ItemSize

from scheduler.ui.widgets.base_tree_view import BaseTreeView
from scheduler.ui.models.tree import TaskTreeModel
from scheduler.ui import utils


class TaskViewWidget(BaseTreeView):
    """Task Tree Widget.

    This widget holds the tree view for the various tasks.
    """
    HEIGHT_BUFFER = 10

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

    def _build_right_click_menu(self, item=None):
        """Build right click menu for given item.

        This is used to add task history printing to right click menu.
        TODO: should this be available in outliner too? If so just add
        to base treevieew, but need to make sure that it checks if it's
        a category or not first.

        Args:
            item (BaseTaskItem or None): item to build menu for.

        Returns:
            (QtWidgets.QMenu): the right click menu.
        """
        right_click_menu = super(TaskViewWidget, self)._build_right_click_menu(
            item=item
        )
        right_click_menu.addSeparator()
        action = right_click_menu.addAction("Print History")
        self._connect_action_to_func(
            action,
            partial(self.print_task_history, item=item),
        )

        return right_click_menu
    
    def print_task_history(self, item, *args):
        """Print task history of given item.
        
        Args:
            item (BaseTreeItem or None): item to add sibling to.

        Returns:
            (bool): whether or not action was successful.
        """
        if item is None:
            return False
        item.history.print()
        return True


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
        column_name = self._model.get_column_name(index)
        if column_name == self._model.NAME_COLUMN:
            item = index.internalPointer()
            if item:
                editor = QtWidgets.QLineEdit(parent)
                return editor
        elif column_name == self._model.IMPORTANCE_COLUMN:
            item = index.internalPointer()
            if item:
                editor = QtWidgets.QComboBox(parent)
                editor.addItems(ItemImportance.get_values())
                return editor
        elif column_name == self._model.SIZE_COLUMN:
            item = index.internalPointer()
            if item:
                editor = QtWidgets.QComboBox(parent)
                editor.addItems(ItemSize.get_values())
                return editor
        return super().createEditor(parent, option, index)
