"""TaskTab tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.base_tree_item import DuplicateChildNameError
from scheduler.api.tree.task import Task
from scheduler.api.task_data import TaskData
from scheduler.api.tree.task_category import TaskCategory

from ..models.task_model import TaskModel
from ..widgets.outliner import Outliner

from .base_tab import BaseTab


class TaskTab(BaseTab):
    """Task Tab main view."""

    def __init__(self, tree_root, parent=None):
        """Setup task main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskTab, self).__init__(tree_root, parent)
        self._fill_main_view()
        self._fill_scroll_area()

    def update(self):
        """Update view to sync with model.

        This is done by deleting and then recreating the scroll area and
        main view.
        """
        self.scroll_area.deleteLater()
        self._fill_main_view()
        self._fill_scroll_area()

    def _fill_main_view(self):
        """Fill main task view from tree root.

        This also sets the size on the view so that the scroll area can use
        it properly.
        """
        self.main_view = QtWidgets.QWidget()
        self.main_view_layout = QtWidgets.QVBoxLayout()
        self.main_view.setLayout(self.main_view_layout)

        minimum_height = 0
        for category in self.tree_root.get_all_children():
            widget = TaskCategoryWidget(
                category,
                parent=self,
            )
            self.main_view_layout.addWidget(widget)
            minimum_height += widget.minimumHeight() + 10
        self.main_view.setMinimumSize(
            QtCore.QSize(1000, minimum_height)
        )

    def _fill_scroll_area(self):
        """Create scroll area and set its widget as main view."""
        self.scroll_area = QtWidgets.QScrollArea(self) 
        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self.scroll_area.setWidget(self.main_view)


class TaskCategoryWidget(QtWidgets.QWidget):
    """Task category widget.

    This widget holds a line edit with the name of the current category,
    as well as TaskCategoryWidgets for all of its subcategories and
    TaskTreeWidgets for all its tasks.
    """

    def __init__(self, task_item, recursive_depth=0, parent=None):
        """Initialise task category widget.

        Args:
            task_item (Task or TaskCategory): task or task category tree item.
            recursive_depth (int): how far down the tree this item is.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskCategoryWidget, self).__init__(parent)
        self.task_item = task_item

        # inner layout holds line edit (and potential additions)
        # outer layout holds inner layout and subwidgets
        self.outer_layout = QtWidgets.QVBoxLayout()
        self.inner_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.outer_layout)
        self.outer_layout.addLayout(self.inner_layout)
        self.line_edit = QtWidgets.QLineEdit(self.task_item.name)
        self.line_edit.setFrame(False)
        self.inner_layout.addWidget(self.line_edit)

        # set font and size properties
        font = self.line_edit.font()
        if recursive_depth == 0:
            font.setBold(True)
        font.setPointSize(12 - recursive_depth)
        self.line_edit.setFont(font)
        self.line_edit.setMinimumHeight(14 - recursive_depth)
        self._height = 60

        self.line_edit.editingFinished.connect(
            self.on_editing_finished
        )

        if type(task_item) == TaskCategory:
            for child in task_item.get_all_children():
                widget = TaskCategoryWidget(child, recursive_depth+1, parent)
                self.outer_layout.addWidget(widget)
                self._height += widget._height

        elif type(task_item) == Task:
            widget = TaskWidget(self.task_item, parent)
            self.outer_layout.addWidget(widget)
            self._height += widget.height()

        self.setMinimumHeight(self._height)

    def on_editing_finished(self):
        """Update views when line edit updated."""
        try:
            self.task_item.name = self.line_edit.text()
            self.parent().MODEL_UPDATED_SIGNAL.emit()
        except:
            self.line_edit.setText(self.task_item.name)


class TaskWidget(QtWidgets.QTreeView):
    """Task Tree Widget.

    This widget holds the tree view for the various tasks.
    """

    def __init__(self, task_item, parent=None):
        """Initialise task category widget.

        Args:
            task_item (Task): task category tree item.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskWidget, self).__init__(parent)
        self.task_item = task_item

        # setup model and delegate
        self.setItemDelegate(TaskDelegate(self))
        self.setFrameStyle(self.Shape.NoFrame)
        model = TaskModel(task_item, parent)
        self.setModel(model)
        self.expandAll()
        model.dataChanged.connect(self.parent().update)

        height = task_item.num_descendants() * 25
        self.setMinimumHeight(height + 50)
        self.setMaximumHeight(height + 50)
        self.setHeaderHidden(True)
        self.setItemsExpandable(False)
        
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.MultiSelection
        )
        header = self.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )


class TaskDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(TaskDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        if index.column() != 1:
            return super(TaskDelegate, self).paint(painter, option, index)
        rect = option.rect
        
        plus_button = QtWidgets.QStyleOptionButton()
        plus_button.rect = QtCore.QRect(
            rect.left() + rect.width() - 30,
            rect.top(),
            30,
            rect.height()
        )
        plus_button.text = '+'
        if option.state:
            plus_button_state = (
                QtWidgets.QStyle.StateFlag.State_Enabled |
                QtWidgets.QStyle.StateFlag.State_MouseOver
            )
        else:
            plus_button_state = (
                QtWidgets.QStyle.StateFlag.State_Enabled |
                QtWidgets.QStyle.StateFlag.State_None
            )
        plus_button.state = plus_button_state
        QtWidgets.QApplication.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_PushButton,
            plus_button,
            painter
        )

        minus_button = QtWidgets.QStyleOptionButton()
        minus_button.rect = QtCore.QRect(
            rect.left() + rect.width() - 70,
            rect.top(),
            30,
            rect.height()
        )
        minus_button.text = '-'
        if option.state:
            minus_button_state = (
                QtWidgets.QStyle.StateFlag.State_Enabled |
                QtWidgets.QStyle.StateFlag.State_MouseOver
            )
        else:
            minus_button_state = (
                QtWidgets.QStyle.StateFlag.State_Enabled |
                QtWidgets.QStyle.StateFlag.State_None
            )
        minus_button.state = minus_button_state
        QtWidgets.QApplication.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_PushButton,
            minus_button,
            painter
        )

    def editorEvent(self, event, model, option, index):
        if not index.isValid():
            return
        task_item = index.internalPointer()
        if task_item and index.column() == 1:
            rect = option.rect
            plus_button_rect = QtCore.QRect(
                rect.left() + rect.width() - 30,
                rect.top(),
                30,
                rect.height()
            )
            minus_button_rect = QtCore.QRect(
                rect.left() + rect.width() - 70,
                rect.top(),
                30,
                rect.height()
            )
            try:
                pos = event.pos()
            except AttributeError:
                pos = None
            if pos and plus_button_rect.contains(pos):
                try:
                    task_item.create_new_subtask()
                    model.dataChanged.emit(index, index)
                    return True
                except DuplicateChildNameError:
                    pass
            elif minus_button_rect.contains(event.pos()):
                task_item.parent.remove_child(task_item.name)
                model.dataChanged.emit(index, index)
                return True
        return super().editorEvent(event, model, option, index)
