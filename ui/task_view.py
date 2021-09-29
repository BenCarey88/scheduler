"""TaskTab tab."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.base_tree_item import DuplicateChildNameError
from scheduler.api.tree.task import Task
from scheduler.api.task_data import TaskData
from .models.task_model import TaskModel
from .task_outliner import TaskOutliner


class TaskTab(QtWidgets.QSplitter):
    """TaskTab tab."""

    def __init__(self, *args, **kwargs):
        """Initialise task view."""
        super(TaskTab, self).__init__(*args, **kwargs)

        self.setChildrenCollapsible(False)

        path = "C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\tasks\\projects.json"
        self.task_data = TaskData.from_file(path)

        self.outliner = TaskOutliner(self.task_data, parent=self)
        self.outliner.setMinimumWidth(100)
        self.addWidget(self.outliner)

        self.main_view = QtWidgets.QListView()
        self.main_view.setVerticalScrollMode(self.main_view.ScrollPerPixel)
        self.main_view.setResizeMode(self.main_view.Adjust)
        self.main_view.setItemDelegate(TaskDelegate(self))
        self.addWidget(self.main_view)
        root_data = self.task_data.get_root_data()
        for data in root_data:
            print (type(data), data.name)
        self.model = TaskModel(root_data, self)
        self.main_view.setModel(self.model)
        #self.main_view.expandAll()
        # self.expand_all(root_data, QtCore.QModelIndex())

        for i in range(self.model.rowCount(QtCore.QModelIndex())):
            index = self.model.index(i, 0, QtCore.QModelIndex())
            self.main_view.openPersistentEditor(index)

    def expand_all(self, data_list, index):
        # maybe some of this can be put in the model?
        for i, data in enumerate(data_list):
            child_index = self.model.index(i, 0, index)
            self.main_view.setExpanded(index, True)
            child_data_list = data.get_all_children()
            self.main_view.openPersistentEditor(child_index)
            self.expand_all(child_data_list, child_index)


class TaskView(QtWidgets.QAbstractItemView):

    def __init__(self, parent):
        super(TaskView, self).__init__(parent)
        self.setItemDelegate(TaskDelegate(self))


class TaskDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent):
        super(TaskDelegate, self).__init__(parent)
        #self.setItemEditorFactory(TaskItemEditorFactory())
        self._size_hints = {}

    def createEditor(self, parent, option, index):
        # if not index.model():
        #     return
        editor = TaskWidget(parent, index)
        editor.line_edit.setText(index.data())
        editor.line_edit.editingFinished.connect(
            partial(self.commitData.emit, editor)
        )
        self._size_hints[index] = editor.size()
        # editor.setIndex(index)
        # editor.update_cheat.connect(self.commitData)
        # editor.update_timeline.connect(self.commitData)
        # editor.update_notes.connect(self.commitData)
        if index.model():
            index.model().setData(index, editor, QtCore.Qt.UserRole)
        return editor

    def setEditorData(self, editor, index):
        return

    def sizeHint(self, option, index):
        return self._size_hints.get(index, QtCore.QSize(500, 500))

    def setModelData(self, editor, model, index):
        item = index.internalPointer()
        if editor.line_edit.text() != item.name:
            try:
                item.name = editor.text()
            except DuplicateChildNameError:
                editor.line_edit.setText(item.name)

    # def setEditorData(self, editor, index):


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

    # def sizeHint():


class TaskItemEditorFactory(QtWidgets.QItemEditorFactory):

    def __init__(self):
        super(TaskItemEditorFactory, self).__init__()


class TaskWidget(QtWidgets.QWidget):

    def __init__(self, parent, index):
        super(TaskWidget, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.line_edit = QtWidgets.QLineEdit(parent)
        self.line_edit.setText(index.data())
        layout.addWidget(self.line_edit)

        list_view = QtWidgets.QListView()
        list_view.setVerticalScrollMode(list_view.ScrollPerPixel)
        layout.addWidget(list_view)
        root_data = index.internalPointer().get_all_children()
        for data in root_data:
            print (type(data), data.name)
        
        path = "C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\tasks\\projects.json"
        task_data = TaskData.from_file(path)

        #model = TaskModel(task_data.get_root_data(), self)
        model = TaskModel(root_data, self)

        list_view.setModel(model)
        # list_view.setModel(QtCore.QStringListModel(["12","2","3","4"]))

        list_view.setItemDelegate(TaskDelegate(self))
        for i in range(model.rowCount(QtCore.QModelIndex())):
            index = model.index(i, 0, QtCore.QModelIndex())
            list_view.openPersistentEditor(index)

        self.setMinimumSize(500, 500)
