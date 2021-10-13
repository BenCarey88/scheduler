"""TaskTab tab."""

import datetime
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.base_tree_item import BaseTreeItem, DuplicateChildNameError
from scheduler.api.tree.task import Task
from scheduler.api.task_data import TaskData
from scheduler.api.tree.task_category import TaskCategory
from ui.utils import suppress_signals
from .models.task_model import TaskModel
from .task_outliner import TaskOutliner

from .utils import suppress_signals


class TaskTab(QtWidgets.QSplitter):
    """TaskTab tab."""

    def __init__(self, *args, **kwargs):
        """Initialise task view."""
        super(TaskTab, self).__init__(*args, **kwargs)

        self.setChildrenCollapsible(False)

        path = "C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\tasks\\projects.json"
        self.task_data = TaskData.from_file(path)
        self.tree_root = self.task_data.get_tree_root()

        # TESTING NEW ROOT
        # root = BaseTreeItem("Root")
        # for category in root_data:
        #     root.add_child(category)

        # self.main_layout = QtWidgets.QVBoxLayout()
        # self.setLayout(self.main_layout)

        # TESTING NEW ROOT
        # self.outliner = TaskOutliner(self.task_data, parent=self)
        self.outliner = TaskOutliner(self.tree_root, parent=self)

        self.addWidget(self.outliner)

        self.scroll_area = QtWidgets.QScrollArea(self) 
        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self.main_view = QtWidgets.QWidget()
        self.addWidget(self.scroll_area)
        #self.addWidget(self.main_view)

        self.main_view_layout = QtWidgets.QVBoxLayout()
        self.main_view.setLayout(self.main_view_layout)
        #self.main_view = QtWidgets.QTreeView()
        # self.model = TaskModel(root_data, self)
        # self.main_view.setModel(self.model)
        #self.main_view.expandAll()
        #self.expand_all(root_data, QtCore.QModelIndex())

        # self.kids = []
        # self.outliner.model.dataChanged.connect(
        #     self.reset
        # )

        self.display_tasks(self.tree_root)
        self.refresh_scroll_area()

    def display_tasks(self, tree_root):
        minimum_height = 0
        for category in tree_root.get_all_children():
            widget = TaskCategoryWidget(
                category,
                parent=self,
            )
            self.main_view_layout.addWidget(widget)
            # self.kids.append(widget)
            minimum_height += widget.minimumHeight() + 10
        self.main_view.setMinimumSize(
            QtCore.QSize(1000, minimum_height)
        )

    # TO TEST SWITCHING THIS FROM SPLITTER TO QWIDGET
    # Can probably be deleted
    # def addWidget(self, widget):
    #     self.main_layout.addWidget(widget)

    def refresh_scroll_area(self):
        self.scroll_area.deleteLater()
        self.scroll_area = QtWidgets.QScrollArea(self) 
        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self.scroll_area.setWidget(self.main_view)

    def reset(self):
        # for widget in self.kids:
        #     self.main_view_layout.removeWidget(widget)
        #     widget.safe_delete()
        # self.main_view.deleteLater()
        print ("RESET")
        self.main_view = QtWidgets.QWidget()
        self.main_view_layout = QtWidgets.QVBoxLayout()
        self.main_view.setLayout(self.main_view_layout)
        # tree_root = self.task_data.get_tree_root()
        self.display_tasks(self.tree_root)
        self.refresh_scroll_area()
        # self.outliner.model.dataChanged.connect(
        #     self.reset
        # )

    def refresh_outliner(self):
        self.outliner.update()


class TaskCategoryWidget(QtWidgets.QWidget):

    def __init__(self, task_item, recursive_depth=0, parent=None):
        super(TaskCategoryWidget, self).__init__(parent)
        self.main_view = parent
        self.task_item = task_item
        self.name = task_item.name

        self.outer_layout = QtWidgets.QVBoxLayout()
        self.inner_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.outer_layout)
        self.outer_layout.addLayout(self.inner_layout)

        self.line_edit = QtWidgets.QLineEdit(self.name)
        self.line_edit.setFrame(False)

        font = self.line_edit.font()
        if recursive_depth == 0:
            font.setBold(True)
        font.setPointSize(12 - recursive_depth)
        self.line_edit.setFont(font)
        self.line_edit.setMinimumHeight(14 - recursive_depth)
        
        def on_editing_finished():
            try:
                self.task_item.name = self.line_edit.text()
                self.main_view.refresh_outliner()
            except:
                pass

        self.line_edit.editingFinished.connect(
            on_editing_finished
        )

        self.inner_layout.addWidget(self.line_edit)

        self._height = 60

        if type(task_item) == TaskCategory:
            for child in task_item.get_all_children():
                widget = TaskCategoryWidget(child, recursive_depth+1, parent)
                self.outer_layout.addWidget(widget)
                self._height += widget._height

        elif type(task_item) == Task:
            tree = QtWidgets.QTreeView()
            tree.setItemDelegate(TaskDelegate(tree))
            tree.setFrameStyle(tree.Shape.NoFrame)
             
            # TESTING NEW ROOT
            # model = TaskModel(task_item.get_all_subtasks(), parent)
            model = TaskModel(task_item, parent)

            tree.setModel(model)
            tree.expandAll()

            def open_editor(data_list, index):
                # maybe some of this can be put in the model?
                for i, data in enumerate(data_list):
                    for column in range(2):
                        child_index = model.index(i, column, index)
                        child_data_list = data.get_all_children()
                        tree.openPersistentEditor(child_index)
                        open_editor(child_data_list, child_index)
            #open_editor(task_item.get_all_subtasks(), QtCore.QModelIndex())

            tree_height = task_item.num_descendants() * 25
            tree.setMinimumHeight(tree_height + 50)
            tree.setMaximumHeight(tree_height + 50)
            tree.setHeaderHidden(True)
            tree.setItemsExpandable(False)
            self.outer_layout.addWidget(tree)
            self._height += tree_height

            tree.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.MultiSelection
            )
            header = tree.header()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            header.setSectionsMovable(True)
            header.setSectionsClickable(True)
            tree.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
            )

            model.dataChanged.connect(self.parent().reset)
            # header.setSizeAdjustPolicy()

            # def open_and_close_editors(new_index, old_index):
            #     tree.closePersistentEditor(old_index)
            #     tree.openPersistentEditor(new_index)
            # tree.selectionModel().currentChanged.connect(open_and_close_editors)

        self.setMinimumHeight(self._height)

    # def safe_delete(self):
    #     for kid in self.kids:
    #         self.outer_layout.removeWidget(kid)
    #         kid.deleteLater()
    #     self.deleteLater()


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

        # painter.fillRect(
        #     option.rect,
        #     option.palette.highlight(),
        #     # QtWidgets.QStyleOption.palette.
        # )

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
                    task_item.create_subtask("[NEW SUBTASK (RENAME REQUIRED)]")
                    model.dataChanged.emit(index, index)
                    return True
                except DuplicateChildNameError:
                    pass
            elif minus_button_rect.contains(event.pos()):
                task_item.parent.remove_child(task_item.name)
                model.dataChanged.emit(index, index)
                return True
        return super().editorEvent(event, model, option, index)

    # def createEditor(self, parent, option, index):
    #     if not index.model():
    #         return
    #     column = index.column()
    #     if True: #if column == 0:
    #         editor = QtWidgets.QLineEdit(index.data(), parent)
    #         editor.editingFinished.connect(
    #             partial(self.commitData.emit, editor)
    #         )
    #         editor.setFrame(False)
    #     # elif column == 1:
    #     #     editor = QtWidgets.QPushButton("index.data()", parent)
    #     # else:
    #     #     editor = QtWidgets.QWidget(parent)
    #     return editor

    # def setEditorData(self, editor, index):
    #     if index.model():
    #         index.model().setData(index, editor, QtCore.Qt.UserRole)
    #     return

    # # def sizeHint(self, option, index):
    # #     return QtCore.QSize(500, 30)

    # def setModelData(self, editor, model, index):
    #     item = index.internalPointer()
    #     if editor.text() != item.name:
    #         try:
    #             item.name = editor.text()
    #         except DuplicateChildNameError:
    #             editor.setText(item.name)

    # hash this function out to get stuff working again
    # def paint(self, painter, option, index):
    #     string = index.data()
    #     style = QtWidgets.QApplication.style()
    #     style.drawPrimitive(
    #         style.PrimitiveElement.PE_IndicatorArrowUp,
    #         QtWidgets.QStyleOption(),
    #         painter,
    #         QtWidgets.QPushButton()
    #     )


class TaskWidget(QtWidgets.QWidget):

    def __init__(self, parent, index):
        super(TaskWidget, self).__init__(parent)
