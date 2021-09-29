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
        root_data = self.task_data.get_root_data()

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.outliner = TaskOutliner(self.task_data, parent=self)
        self.addWidget(self.outliner)

        self.main_view = QtWidgets.QWidget()
        self.addWidget(self.main_view)

        self.main_view_layout = QtWidgets.QVBoxLayout()
        self.main_view.setLayout(self.main_view_layout)
        #self.main_view = QtWidgets.QTreeView()
        # self.model = TaskModel(root_data, self)
        # self.main_view.setModel(self.model)
        #self.main_view.expandAll()
        #self.expand_all(root_data, QtCore.QModelIndex())
        self.display_tasks(root_data)

    def display_tasks(self, task_catgeory_list):
        for category in task_catgeory_list:
            self.main_view_layout.addWidget(TaskWidget(category, self))


class TaskWidget(QtWidgets.QWidget):

    def __init__(self, task_item, parent=None):
        super(TaskWidget, self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.name = task_item.name
        self.label = QtWidgets.QLineEdit(self.name)
        self.layout.addWidget(self.label)
        for child in task_item.get_all_children():
            self.layout.addWidget(TaskWidget(child, self))
