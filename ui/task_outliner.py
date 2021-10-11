"""TaskOutliner Panel."""

import os

from PyQt5 import QtCore, QtGui, QtWidgets

from .models.task_category_model import TaskCategoryModel


class TaskOutliner(QtWidgets.QTreeView):
    """TaskOutliner panel."""

    #MODEL_UPDATED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, task_data, *args, **kwargs):
        """Initialise task view."""
        super(TaskOutliner, self).__init__(*args, **kwargs)

        self.task_data = task_data
        self.set_model()

        self.setHeaderHidden(True)

        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.MultiSelection
        )
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems
        )

    def update(self):
        self.set_model(keep_selection=True)

    def set_model(self, keep_selection=False):
        selected_items = []
        current_item = None
        if keep_selection:
            selected_items = [
                index.internalPointer()
                for index in self.selectedIndexes()
                if index.isValid()
            ]
            current_item = self.currentIndex().internalPointer()
        self.model = TaskCategoryModel(self.task_data.get_root_data(), self)
        self.setModel(self.model)
        self.expandAll()
        self.model.dataChanged.connect(
            self.parent().reset
        )
        print (selected_items)
        for item in selected_items:
            print (item.name)
            if item.pruned:
                continue
            print (1)
            index = self.model.createIndex(
                item.index(),
                0,
                current_item
            )
            print (index)
            if not index.isValid():
                continue
            print (3)
            self.selectionModel().select(
                index,
                self.selection_model().SelectionFlag.SelectCurrent
            )
            print (4)
        if current_item and not current_item.pruned:
            index = self.model.createIndex(
                current_item.index(),
                0,
                current_item
            )
            print (index)
            self.setCurrentIndex(index)


        # def current_changed(new_index, old_index):
        #     new_data = new_index.internalPointer()
        #     old_data = old_index.internalPointer()
        #     print (
        #         "SIGNAL CALLED: new data is (",
        #         new_data.name if new_data else None,
        #         "), old data is (",
        #         old_data.name if old_data else None,
        #         ")"
        #     )
        # selection_model.currentChanged.connect(current_changed)

        # def selection_changed(*args):
        #     print ("BBBBBBBBBBBBBBBBBBBBBBB")
        # selection_model.selectionChanged.connect(selection_changed)

        # def clicked(index):
        #     selection_model.setCurrentIndex(
        #         index,
        #         selection_model.SelectionFlag.SelectCurrent
        #     )
        #     self.itemDelegate(index).setProperty("background-color", "yellow")
        # self.clicked.connect(clicked)

        # index = self.model().index(0, 0, QtCore.QModelIndex())
        # # self.setCurrentIndex(index)
        # # print (index.internalPointer().name, self.currentIndex().internalPointer())

        # # selection_model.select(index, selection_model.SelectionFlag.Current)
        # selection_model.setCurrentIndex(index, selection_model.SelectionFlag.SelectCurrent)
        # print (index.internalPointer(), self.currentIndex().internalPointer())
        # print (index.internalPointer(), selection_model.currentIndex().internalPointer())
