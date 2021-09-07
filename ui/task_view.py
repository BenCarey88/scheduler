"""TaskView tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from scheduler.api.task_data import TaskData
from .models.task_model import TaskModel
from .task_outliner import TaskOutliner


class TaskView(QtWidgets.QWidget):
    """TaskView tab."""

    def __init__(self, *args, **kwargs):
        """Initialise task view."""
        super(TaskView, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.outliner = TaskOutliner(self)
        self.layout.addWidget(self.outliner)

        self.main_view = QtWidgets.QTreeView()
        self.layout.addWidget(self.main_view)
        path = "C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\tasks\\projects.json"
        self.task_data = TaskData.from_file(path)
        root_data = self.task_data.get_root_data()
        self.model = TaskModel(root_data, self)
        self.main_view.setModel(self.model)
        self.expand_all(root_data, QtCore.QModelIndex())

    def expand_all(self, data_list, index):
        # maybe some of this can be put in the model?
        for i, data in enumerate(data_list):
            child_index = self.model.index(i, 0, index)
            self.main_view.setExpanded(index, True)
            child_data_list = data.get_all_children()
            self.expand_all(child_data_list, child_index)
