"""Base dialog for creating and editing items."""


from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui import utils
from scheduler.ui.models.tree import FullTaskTreeModel


class ItemDialog(QtWidgets.QDialog):
    """Base dialog for creating and editing items."""

    def __init__(
            self,
            tree_manager,
            schedule_manager,
            item=None,
            tree_item=None,
            parent=None):
        """Initialise dialog.

        Args:
            tree_manager (TreeManager): the task tree manager object.
            calendar (calendar): the calendar object.
            item (BaseScheduledItem, PlannedItem or None): item we're
                editing, if in edit mode. If None, we're in create mode.
            tree_item (Task or None): tree item to initialize with, if we're
                not passing a scheduled item. If None, user has to choose.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(ItemDialog, self).__init__(parent=parent)
        self._calendar = schedule_manager.calendar
        self._schedule_manager = schedule_manager
        self._item = item
        self.is_editor = (item is not None)

    @property
    def tree_item(self):
        """Get tree item this is associated to.

        Returns:
            (Task or None): selected task tree item, if one exists.
        """
        return self.task_combo_box.selected_task_item

    def accept_and_close(self):
        """Run add or modify scheduled item edit.

        Called when user clicks accept.
        """
        raise NotImplementedError(
            "accept_and_close implemented in ItemDialog subclasses."
        )

    def delete_item_and_close(self):
        """Run remove scheduled item edit.

        Called when user clicks delete.
        """
        raise NotImplementedError(
            "delete_item_and_close implemented in ItemDialog subclasses."
        )




class TreeComboBox(QtWidgets.QComboBox):
    # Thanks to http://qt.shoutwiki.com/wiki/Implementing_QTreeView_in_QComboBox_using_Qt-_Part_2

    def __init__(self, label, tree_item=None, parent=None):
        super(TreeComboBox, self).__init__(parent=parent)
        self.label = label
        self.skip_next_hide = False
        self.selected_task_item = None
        self.setEnabled(False)
        self.tree_item = tree_item

    def setup(self, model, tree_view, root):
        self.setEnabled(True)
        self.setModel(model)
        self.setView(tree_view)
        self.view().viewport().installEventFilter(self)
        self.root = root
        if self.tree_item:
            item_row = self.tree_item.index()
            if item_row is not None:
                index = model.createIndex(
                    item_row,
                    0,
                    self.tree_item
                )
                self.view().setCurrentIndex(index)
                self.setRootModelIndex(index.parent())
                self.setCurrentIndex(index.row())
                try:
                    full_text = self.tree_item.path[len(self.root.path):]
                    self.label.setText(full_text)
                except IndexError:
                    pass

    def eventFilter(self, object, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress
                and object == self.view().viewport()):
            index = self.view().indexAt(event.pos())
            if not self.view().visualRect(index).contains(event.pos()):
                self.skip_next_hide = True
        return False

    def showPopup(self):
        self.setRootModelIndex(QtCore.QModelIndex())
        super(TreeComboBox, self).showPopup()

    def hidePopup(self):
        # self.setRootModelIndex(self.view().currentIndex().parent())
        self.setCurrentIndex(self.view().currentIndex().row())
        if self.skip_next_hide:
            self.skip_next_hide = False
        else:
            super(TreeComboBox, self).hidePopup()
            index = self.view().currentIndex()
            if index:
                item = self.view().currentIndex().internalPointer()
                if item:
                    self.selected_task_item = item
                    try:
                        full_text = item.path[len(self.root.path):]
                    except IndexError:
                        return
                    self.label.setText(full_text)


class TaskTreeComboBox(TreeComboBox):
    def __init__(
            self,
            tree_manager,
            label,
            tree_item=None,
            parent=None):
        model = FullTaskTreeModel(tree_manager)
        tree_view = QtWidgets.QTreeView()
        tree_view.setModel(model)
        super(TaskTreeComboBox, self).__init__(
            label,
            tree_item,
            parent=parent
        )
        self.setup(model, tree_view, tree_manager.tree_root)
