"""Task Category widget for Task Tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui import utils
from scheduler.ui.widgets.widget_list_view import WidgetListView
from .task_view_widget import TaskViewWidget
from .task_widget_layout import TaskWidgetLayout


class TaskHeaderWidget(QtWidgets.QFrame):
    """Task header widget, for categories and top-level tasks.

    This widget holds a line edit with the name of the current category/
    task, as well as TaskHeaderWidgets for all of its subcategories and
    top-level tasks and TaskViewWidgets for all subtasks.
    """
    FONT_SIZE_MAX = 12
    FONT_SIZE_MIN = 9
    FONT_SIZE_STEP = 1
    LINE_EDIT_BUFFER = 10
    HEIGHT_BUFFER = 30

    def __init__(
            self,
            tree_manager,
            task_item,
            tab,
            recursive_depth=0,
            item_spacing=None,
            parent=None):
        """Initialise task category widget.

        Args:
            tree_manager (TreeManager): tree manager item.
            task_item (Task or TaskCategory): task or task category tree item.
            tab (TaskTab): task tab this widget is a descendant of.
            recursive_depth (int): how far down the tree this item is.
            item_spacing (int): override of spacing for child items.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskHeaderWidget, self).__init__(parent)
        self.tree_manager = tree_manager
        self.task_item = task_item
        self.tab = tab
        tab.task_widget_tree.add_or_update_item(
            task_item,
            task_header_widget=self
        )
        if recursive_depth == 0:
            # only need to set style on top-most widget.
            utils.set_style(self, "task_header_widget.qss")

        # outer layout holds line edit layout and task widget layout
        self.outer_layout = QtWidgets.QVBoxLayout()
        self.line_edit_layout = QtWidgets.QHBoxLayout()
        # self.widget_layout = TaskWidgetLayout(self.task_widget_tree)
        self.setLayout(self.outer_layout)
        self.outer_layout.addLayout(self.line_edit_layout)
        # self.outer_layout.addLayout(self.widget_layout)

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

        self.task_view_widget = None
        self.header_list_view = None
        if self.tree_manager.is_task_category(task_item):
            self.header_list_view = TaskHeaderListView(
                tree_manager,
                task_item,
                tab=tab,
                recursive_depth=recursive_depth+1,
                item_spacing=item_spacing,
            )
            self.outer_layout.addWidget(self.header_list_view)
            self.child_widget = self.header_list_view

        elif self.tree_manager.is_task(task_item):
            self.task_view_widget = TaskViewWidget(
                self.tree_manager,
                task_item,
                tab=tab,
            )
            self.outer_layout.addWidget(self.task_view_widget)
            self.child_widget = self.task_view_widget

        # self.setMinimumHeight(self._height)
        # self.setSizePolicy(
        #     QtWidgets.QSizePolicy.Policy.Expanding,
        #     QtWidgets.QSizePolicy.Policy.Preferred,
        # )
        self.line_edit.editingFinished.connect(
            self.on_editing_finished
        )
        # self.setMinimumSize(self.child_widget.minimumSize())

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

    def eventFilter(self, obj, event):
        """Event filter for when object is clicked.

        Args:
            obj (QtCore.QObject): QObject that event is happening on.
            event (QtCore.QEvent): event that is happening.
        """
        if obj == self.line_edit and event.type() == QtCore.QEvent.FocusIn:
            if self.tree_manager.is_task(self.task_item):
                # self.tab.selected_subtask_item = None
                self.tab.selected_task_item = self.task_item
        if obj == self.line_edit and event.type() == QtCore.QEvent.FocusOut:
            self.tab.selected_task_item = None
        return False

    def sizeHint(self):
        """Get item size hint.

        Returns:
            (QtCore.QSize): size hint.
        """
        width = super(TaskHeaderWidget, self).sizeHint().width()
        height = (
            self.line_edit.height() +
            self.child_widget.sizeHint().height() +
            self.HEIGHT_BUFFER
        )
        return QtCore.QSize(width, height)


class TaskHeaderListView(WidgetListView):
    """List of task header widgets for subcategories/tasks."""
    # BORDER_BUFFER = 3

    def __init__(
            self,
            tree_manager,
            task_item,
            tab,
            recursive_depth=0,
            item_spacing=None,
            parent=None):
        """Initialize.

        Args:
            tree_manager (TreeManager): tree manager item.
            task_item (Task or TaskCategory): task or task category tree item.
            tab (TaskTab): task tab this widget is a descendant of.
            recursive_depth (int): how far down the tree this item is.
            item_spacing (int or None): override of spacing for child items.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        tab.task_widget_tree.add_or_update_item(
            task_item,
            task_header_view=self,
        )
        widget_list = []
        for child in tree_manager.get_filtered_children(task_item):
            widget = TaskHeaderWidget(
                tree_manager,
                child,
                tab=tab,
                recursive_depth=recursive_depth,
            )
            widget_list.append(widget)
        self.recursive_depth = recursive_depth
        super(TaskHeaderListView, self).__init__(
            widget_list,
            item_spacing=item_spacing,
            parent=parent,
        )
        self.tree_manager = tree_manager
        self.task_item = task_item
        self.tab = tab
        self.recursive_depth = recursive_depth

    def insert_header_widget(self, row, task_header_item):
        """Create a new header widget for task item and add to list.

        Args:
            row (int): row to insert at.
            task_header_item (Task or TaskCategory): new item to add.
        """
        widget = TaskHeaderWidget(
            self.tree_manager,
            task_header_item,
            self.tab,
            recursive_depth=self.recursive_depth,
        )
        self.insert_widget(row, widget)

    def remove_header_widget(self, row, task_header_item):
        """Remove header widget at given row.

        Args:
            row (int): row to remove.
            task_header_item (Task or TaskCategory): item to remove.
        """
        self.remove_widget(row)
        self.tab.task_widget_tree.remove_item(task_header_item)
