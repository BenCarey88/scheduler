"""Task widget for Task Tab."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.models.task_model import TaskModel


class TaskWidget(QtWidgets.QTreeView):
    """Task Tree Widget.

    This widget holds the tree view for the various tasks.
    """

    def __init__(self, task_item, tab, parent=None):
        """Initialise task category widget.

        Args:
            task_item (Task): task category tree item.
            tab (TaskTab): task tab this widget is a descendant of.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskWidget, self).__init__(parent)
        self.task_item = task_item
        self.tab = tab

        # setup model and delegate
        self.setItemDelegate(TaskDelegate(self))
        self.setFrameStyle(self.Shape.NoFrame)
        model = TaskModel(task_item, parent)
        self.setModel(model)
        self.expandAll()
        model.dataChanged.connect(self.tab.update)

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
        self.selectionModel().currentChanged.connect(
            partial(self.tab.switch_active_task_widget, self.task_item.path)
        )

        self.select_subtask_item()

    def select_subtask_item(self):
        """Select the subtask item marked as active in the task tab."""
        if (self.tab.selected_subtask_item and
                self.task_item.path in self.tab.selected_subtask_item.path):
            item_index = self.tab.selected_subtask_item.index()
            if item_index is not None:
                index = self.model().createIndex(
                    item_index,
                    0,
                    self.tab.selected_subtask_item
                )
                if index.isValid():
                    self.selectionModel().select(
                        index,
                        self.selectionModel().SelectionFlag.Select
                    )
                    self.selectionModel().setCurrentIndex(
                        index,
                        self.selectionModel().SelectionFlag.Select
                    )
                    self.setFocus()


class TaskDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for task widget tree."""

    def __init__(self, parent=None):
        """Initialise task delegate item."""
        super(TaskDelegate, self).__init__(parent)

    @staticmethod
    def _get_plus_button_rect(option):
        """Get QRect for area where plus button should be.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object
                for current item being painted.

        Returns:
            (QtCore.QRect): QRect for the plus button.
        """
        return QtCore.QRect(
            option.rect.left() + option.rect.width() - 30,
            option.rect.top(),
            30,
            option.rect.height()
        )

    @staticmethod
    def _get_minus_button_rect(option):
        """Get QRect for area where minus button should be.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object
                for current item being painted.

        Returns:
            (QtCore.QRect): QRect for the minus button.
        """
        return QtCore.QRect(
            option.rect.left() + option.rect.width() - 70,
            option.rect.top(),
            30,
            option.rect.height()
        )

    @staticmethod
    def _get_button_flags(option):
        """Get Qt state flags for painted buttons.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object
                for current item being painted.

        Returns:
            (QtWidgets.QStyle.StateFlag): Qt state flag.
        """
        if option.state:
            state = (
                QtWidgets.QStyle.StateFlag.State_Enabled |
                QtWidgets.QStyle.StateFlag.State_MouseOver
            )
        else:
            state = (
                QtWidgets.QStyle.StateFlag.State_Enabled |
                QtWidgets.QStyle.StateFlag.State_None
            )
        return state

    def paint(self, painter, option, index):
        """Override paint method for custom rendering.

        Args:
            painter (QtGui.QPainter): painter object.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item we're painting.
        """
        if index.column() != 1:
            return super(TaskDelegate, self).paint(painter, option, index)

        plus_button = QtWidgets.QStyleOptionButton()
        plus_button.rect = self._get_plus_button_rect(option)
        plus_button.text = '+'
        plus_button.state = self._get_button_flags(option)
        QtWidgets.QApplication.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_PushButton,
            plus_button,
            painter
        )

        minus_button = QtWidgets.QStyleOptionButton()
        minus_button.rect = self._get_minus_button_rect(option)
        minus_button.text = '-'
        minus_button.state = self._get_button_flags(option)
        QtWidgets.QApplication.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_PushButton,
            minus_button,
            painter
        )

    def editorEvent(self, event, model, option, index):
        """Edit model based on user input.

        Args:
            event (QtCore.QEvent): the qt event.
            model (QtCore.QAbstractItemModel) the model to be updated.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.
        """
        if not index.isValid():
            return
        task_item = index.internalPointer()
        if task_item and index.column() == 1:
            plus_button_rect = self._get_plus_button_rect(option)
            minus_button_rect = self._get_minus_button_rect(option)
            try:
                pos = event.pos()
            except AttributeError:
                pos = None
            if pos and plus_button_rect.contains(pos):
                task_item.create_new_subtask()
                model.dataChanged.emit(index, index)
                return True
            elif pos and minus_button_rect.contains(pos):
                task_item.parent.remove_child(task_item.name)
                model.dataChanged.emit(index, index)
                return True
        return super().editorEvent(event, model, option, index)
