"""Task Category widget for Task Tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory

from .task_widget import TaskWidget


class TaskCategoryWidget(QtWidgets.QFrame):
    """Task category widget.

    This widget holds a line edit with the name of the current category,
    as well as TaskCategoryWidgets for all of its subcategories and
    TaskTreeWidgets for all its tasks.

    Signals:
        MODEL_UPDATED_SIGNAL: emitted whenever the tree model is updated by
            the outliner.
    """
    MODEL_UPDATED_SIGNAL = QtCore.pyqtSignal()

    def __init__(
            self,
            tree_manager,
            task_item,
            tab,
            recursive_depth=0,
            parent=None):
        """Initialise task category widget.

        Args:
            tree_manager (TreeManager): tree manager item.
            task_item (Task or TaskCategory): task or task category tree item.
            tab (TaskTab): task tab this widget is a descendant of.
            recursive_depth (int): how far down the tree this item is.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskCategoryWidget, self).__init__(parent)
        self.tree_manager = tree_manager
        self.task_item = task_item
        self.tab = tab

        # inner layout holds line edit (and potential additions)
        # outer layout holds inner layout and subwidgets
        self.outer_layout = QtWidgets.QVBoxLayout()
        self.inner_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.outer_layout)
        self.outer_layout.addLayout(self.inner_layout)
        self.line_edit = QtWidgets.QLineEdit(self.task_item.name)
        self.line_edit.setFrame(False)
        self.line_edit.installEventFilter(self)
        self.inner_layout.addWidget(self.line_edit)

        # set font and size properties
        # TODO: make some constants for these guys 
        # (maybe in separate file in this directory)
        font = self.line_edit.font()
        if isinstance(task_item, TaskCategory):
            font.setBold(True)
        font.setPointSize(12 - recursive_depth)
        self.line_edit.setFont(font)
        self.line_edit.setMinimumHeight(14 - recursive_depth)
        self._height = 50

        # Set border properties
        # TODO: set this and above via task tab stylesheet
        self.setStyleSheet("border: 1px dotted grey")
        self.line_edit.setStyleSheet("border: none")

        self.line_edit.editingFinished.connect(
            self.on_editing_finished
        )

        if type(task_item) == TaskCategory:
            child_filter = self.tree_manager.child_filter
            child_filters = [child_filter] if child_filter else []
            # TODO: this should probably be done by tree manager
            with task_item.filter_children(child_filters):
                for child in task_item.get_all_children():
                    # TODO: naming is dodgy: the top level tasks are actually
                    # TaskCategoryWidgets here rather than TaskWidgets
                    widget = TaskCategoryWidget(
                        self.tree_manager,
                        child,
                        tab=tab,
                        recursive_depth=recursive_depth+1,
                        parent=self
                    )
                    self.tab.category_widget_tree[child] = widget
                    self.outer_layout.addWidget(widget)
                    self._height += widget._height

        elif type(task_item) == Task:
            widget = TaskWidget(
                self.tree_manager,
                task_item,
                tab=tab,
                parent=self
            )
            self.tab.task_widget_tree[task_item] = widget
            self.outer_layout.addWidget(widget)
            self._height += widget.height()

        self.setMinimumHeight(self._height)

    def on_editing_finished(self):
        """Update views when line edit updated."""
        # TODO: arguably this type of thing should be handled through the
        # model - ie. would probably be better if all updates to the tree
        # items are done through the model? so this functions would call
        # the model's update_name method or something like that.
        # ^ open question tbh, not sure about that anymore
        success = self.tree_manager.set_item_name(
            self.task_item,
            self.line_edit.text(),
        )
        if success:
            self.tab.MODEL_UPDATED_SIGNAL.emit()
        else:
            self.line_edit.setText(self.task_item.name)

    def eventFilter(self, object, event):
        """Event filter for when object is clicked.

        Args:
            object (QtCore.QObject): QObject that event is happening on.
            event (QtCore.QEvent): event that is happening.
        """
        if object == self.line_edit and event.type() == QtCore.QEvent.FocusIn:
            if isinstance(self.task_item, Task):
                self.tab.selected_subtask_item = None
                self.tab.selected_task_item = self.task_item
        if object == self.line_edit and event.type() == QtCore.QEvent.FocusOut:
            self.tab.selected_task_item = None
        return False
