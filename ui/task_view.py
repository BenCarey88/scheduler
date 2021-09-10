"""TaskTab tab."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.base_tree_item import DuplicateChildNameError
from scheduler.api.tree.task import Task
from scheduler.api.task_data import TaskData
from .models.task_model import TaskModel
from .task_outliner import TaskOutliner


class TaskTab(QtWidgets.QWidget):
    """TaskTab tab."""

    def __init__(self, *args, **kwargs):
        """Initialise task view."""
        super(TaskTab, self).__init__(*args, **kwargs)

        path = "C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\tasks\\projects.json"
        self.task_data = TaskData.from_file(path)

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.outliner = TaskOutliner(self.task_data, parent=self)
        self.layout.addWidget(self.outliner)

        self.main_view = QtWidgets.QTreeView()
        self.main_view.setItemDelegate(TaskDelegate(self))
        self.layout.addWidget(self.main_view)
        root_data = self.task_data.get_root_data()
        self.model = TaskModel(root_data, self)
        self.main_view.setModel(self.model)
        #self.main_view.expandAll()
        self.expand_all(root_data, QtCore.QModelIndex())

        # for i in range(self.model.rowCount(QtCore.QModelIndex())):
        #     index = self.model.index(i, 0, QtCore.QModelIndex())
        #     self.main_view.openPersistentEditor(index)

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

    def createEditor(self, parent, option, index):
        # if not index.model():
        #     return
        editor = QtWidgets.QLineEdit(parent)
        editor.setText(index.data())
        editor.editingFinished.connect(
            partial(self.commitData.emit, editor)
        )
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
        return QtCore.QSize(50, 50)

    def setModelData(self, editor, model, index):
        item = index.internalPointer()
        if editor.text() != item.name:
            try:
                item.name = editor.text()
            except DuplicateChildNameError:
                editor.setText(item.name)

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
