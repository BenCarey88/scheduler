"""Task Category widget for Task Tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui import utils
from .task_view_widget import TaskViewWidget
from .task_widget_layout import TaskWidgetLayout


class TaskHeaderWidget(QtWidgets.QFrame):
    """Task header widget, for categories and top-level tasks.

    This widget holds a line edit with the name of the current category/
    task, as well as TaskHeaderWidgets for all of its subcategories and
    top-level tasks and TaskViewWidgets for all subtasks.
    """
    HEIGHT_MIN = 0
    FONT_SIZE_MAX = 12
    FONT_SIZE_MIN = 9
    FONT_SIZE_STEP = 1
    LINE_EDIT_BUFFER = 10

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
        super(TaskHeaderWidget, self).__init__(parent)
        self.tree_manager = tree_manager
        self.task_item = task_item
        self.tab = tab
        self.task_widget_tree = tab.task_widget_tree
        utils.set_style(self, "task_header_widget.qss")

        # outer layout holds line edit layout and task widget layout
        self.outer_layout = QtWidgets.QVBoxLayout()
        self.line_edit_layout = QtWidgets.QHBoxLayout()
        self.widget_layout = TaskWidgetLayout(self.task_widget_tree)
        self.setLayout(self.outer_layout)
        self.outer_layout.addLayout(self.line_edit_layout)
        self.outer_layout.addLayout(self.widget_layout)

        # line edit layout holds line edit (and potential additions)
        self.line_edit = QtWidgets.QLineEdit(self.task_item.name)
        self.line_edit.setFrame(False)
        self.line_edit.installEventFilter(self)
        self.line_edit_layout.addWidget(self.line_edit)

        # set font and size properties
        font = self.line_edit.font()
        if self.tree_manager.is_task_category(task_item):
            font.setBold(True)
        font_size = max(
            self.FONT_SIZE_MAX - recursive_depth * self.FONT_SIZE_STEP,
            self.FONT_SIZE_MIN,
        )
        font.setPointSize(font_size)
        self.line_edit.setFont(font)
        self.line_edit.setMinimumHeight(font_size + self.LINE_EDIT_BUFFER)
        self._height = self.HEIGHT_MIN

        if self.tree_manager.is_task_category(task_item):
            for child in self.tree_manager.get_filtered_children(task_item):
                widget = TaskHeaderWidget(
                    self.tree_manager,
                    child,
                    tab=tab,
                    recursive_depth=recursive_depth+1,
                )
                # self.tab.category_widget_tree[child] = widget
                self.widget_layout.add_task_header(child, widget)
                self._height += widget._height

        elif self.tree_manager.is_task(task_item):
            widget = TaskViewWidget(
                self.tree_manager,
                task_item,
                tab=tab,
            )
            # self.tab.task_widget_tree[task_item] = widget
            self.widget_layout.add_task_view(task_item, widget)
            self._height += widget.height()

        # self.setMinimumHeight(self._height)
        # self.setSizePolicy(
        #     QtWidgets.QSizePolicy.Policy.Expanding,
        #     QtWidgets.QSizePolicy.Policy.Preferred,
        # )
        self.line_edit.editingFinished.connect(
            self.on_editing_finished
        )

    def update_task_item(self, task_item):
        """Update task item that this represents.

        In most cases, the task_item will be the same as the old one, and this
        method is just used to ensure the name stays up to date after any name
        changes and etc.

        Args:
            task_item (BaseTreeItem): new task item that this represents.
        """
        if task_item != self.task_item:
            self.task_widget_tree.update_widget_item(self.task_item, task_item)
            self.task_item = task_item
        with utils.suppress_signals(self.line_edit):
            self.line_edit.setText(task_item.name)

    def on_editing_finished(self):
        """Update views when line edit updated."""
        success = self.tree_manager.set_item_name(
            self.task_item,
            self.line_edit.text(),
        )
        if not success:
            self.line_edit.setText(self.task_item.name)

    def eventFilter(self, object, event):
        """Event filter for when object is clicked.

        Args:
            object (QtCore.QObject): QObject that event is happening on.
            event (QtCore.QEvent): event that is happening.
        """
        if object == self.line_edit and event.type() == QtCore.QEvent.FocusIn:
            if self.tree_manager.is_task(self.task_item):
                # self.tab.selected_subtask_item = None
                self.tab.selected_task_item = self.task_item
        if object == self.line_edit and event.type() == QtCore.QEvent.FocusOut:
            self.tab.selected_task_item = None
        return False
