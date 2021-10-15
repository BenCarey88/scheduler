"""Task Outliner Panel."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.models.task_category_model import TaskCategoryModel


class Outliner(QtWidgets.QTreeView):
    """Task Outliner panel."""

    MODEL_UPDATED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, tree_root, parent=None):
        """Initialise task view.
        
        Args:
            tree_root (BaseTreeItem): tree root item for outliner model.
            parent (QtGui.QWidget or None): QWidget parent of widget. 
        """
        super(Outliner, self).__init__(parent)

        self.root = tree_root
        self.reset_model()
        self.setHeaderHidden(True)

        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.MultiSelection
        )
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems
        )

    def update(self):
        """Update view to pick up changes in model."""
        self.reset_model(keep_selection=True)

    def reset_model(self, keep_selection=False):
        """Reset model.

        Args:
            keep_selection (bool): if True, save current selection before
                resetting and reselect any items that still exist.
        """
        selected_items = []
        current_item = None
        if keep_selection:
            selected_items = [
                index.internalPointer()
                for index in self.selectedIndexes()
                if index.isValid()
            ]
            current_item = self.currentIndex().internalPointer()

        self.model = TaskCategoryModel(self.root, self)
        self.setModel(self.model)
        self.expandAll()
        self.model.dataChanged.connect(
            self.MODEL_UPDATED_SIGNAL.emit
        )

        for item in selected_items:
            index = self.model.createIndex(
                item.index(),
                0,
                item
            )
            if not index.isValid():
                continue
            self.selectionModel().select(
                index,
                self.selectionModel().SelectionFlag.Select
            )
        if current_item:
            index = self.model.createIndex(
                current_item.index(),
                0,
                current_item
            )
            self.setCurrentIndex(index)
