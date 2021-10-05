"""TaskTab tab."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.base_tree_item import DuplicateChildNameError
from scheduler.api.tree.task import Task
from scheduler.api.task_data import TaskData
from scheduler.api.tree.task_category import TaskCategory
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

        self.outliner = TaskOutliner(self.task_data, parent=self)
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
        self.display_tasks(root_data)
        self.refresh_scroll_area()

    def display_tasks(self, task_catgeory_list):
        minimum_height = 0
        for category in task_catgeory_list:
            widget = TaskCategoryWidget(category, parent=self)
            self.main_view_layout.addWidget(widget)
            minimum_height += widget.minimumHeight() + 10
        self.main_view.setMinimumSize(
            QtCore.QSize(1000, minimum_height)
        )
    
    def refresh_scroll_area(self):
        self.scroll_area.setWidget(self.main_view)


class TaskCategoryWidget(QtWidgets.QWidget):

    def __init__(self, task_item, recursive_depth=0, parent=None):
        super(TaskCategoryWidget, self).__init__(parent)
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

        self.inner_layout.addWidget(self.line_edit)

        self._height = 60

        if type(task_item) == TaskCategory:
            for child in task_item.get_all_children():
                widget = TaskCategoryWidget(child, recursive_depth+1, self)
                self.outer_layout.addWidget(widget)
                self._height += widget._height

        elif type(task_item) == Task:
            tree = QtWidgets.QTreeView(self)
            tree.setFrameStyle(tree.Shape.NoFrame)
            model = TaskModel(task_item.get_all_subtasks(), self)
            tree.setModel(model)
            tree.expandAll()
            tree_height = task_item.num_descendants() * 25
            tree.setMinimumHeight(tree_height)
            tree.setMaximumHeight(tree_height)
            tree.setHeaderHidden(True)
            tree.setItemsExpandable(False)
            self.outer_layout.addWidget(tree)
            self._height += tree_height

            tree.setStyleSheet(
                """
                QTreeView::branch:open:has-children:!has-siblings{image:url(/c/Users/benca/OneDrive/Documents/Coding/python/scheduler/ui/icons/search.png)}
                QTreeView::branch:closed:has-children:!has-siblings{image:url(/c/Users/benca/OneDrive/Documents/Coding/python/scheduler/ui/icons/search.png)}
                QTreeView::branch:open:has-children{image:url(/c/Users/benca/OneDrive/Documents/Coding/python/scheduler/ui/icons/search.png)}
                QTreeView::branch:closed:has-children{image:url(/c/Users/benca/OneDrive/Documents/Coding/python/scheduler/ui/icons/search.png)}
                QTreeView::branch:open:{image:url(/c/Users/benca/OneDrive/Documents/Coding/python/scheduler/ui/icons/search.png)}
                QTreeView::branch:closed:{image:url(/c/Users/benca/OneDrive/Documents/Coding/python/scheduler/ui/icons/search.png)};
                """
            )

        self.setMinimumHeight(self._height)
