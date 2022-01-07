#TODO: rename as just EventDialog


from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import DateTime, Time
from scheduler.api.edit.calendar_edit import (
    AddCalendarItem,
    ModifyCalendarItem,
    RemoveCalendarItem,
)
from scheduler.api.timetable.calendar_item import CalendarItemType
from scheduler.api.tree.task import Task

from scheduler.ui import utils
from scheduler.ui.models.full_task_tree_model import FullTaskTreeModel
from scheduler.ui.models.task_category_model import TaskCategoryModel
from scheduler.ui.models.task_model import TaskModel
from scheduler.ui.widgets.outliner import Outliner


# TODO: current idea seems to be to make this class just be called and executed
# - we don't need access to anything from it as it handles the edits itself, so
# we should be able to make all methods private.
class CalendarItemDialog(QtWidgets.QDialog):
    """Dialog for creating or editing calendar items."""
    END_TIME_KEY = "End"
    START_TIME_KEY = "Start"

    def __init__(
            self,
            tree_root,
            tree_manager,
            calendar,
            calendar_item,
            as_editor=False,
            parent=None):
        """Initialise dialog.

        Args:
            tree_root (TreeRoot): the task tree root object.
            tree_manager (TreeManager): the task tree manager object.
            calendar (calendar): the calendar object.
            calendar_item (CalendarItem): calendar item we're editing or
                creating.
            as_editor (bool): whether or not we're editing an existing item,
                or adding a new one.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(CalendarItemDialog, self).__init__(parent=parent)
        self._calendar = calendar
        self._calendar_item = calendar_item
        date = calendar_item.date
        start_time = calendar_item.start_time
        end_time = calendar_item.end_time
        self.is_editor = as_editor

        flags = QtCore.Qt.WindowFlags(
            QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setMinimumSize(900, 700)
        self.setWindowTitle("Calendar Item Editor")
        utils.set_style(self, "calendar_item_dialog.qss")

        outer_layout = QtWidgets.QHBoxLayout()
        main_layout = QtWidgets.QVBoxLayout()
        tree_layout = QtWidgets.QVBoxLayout()
        outer_layout.addLayout(main_layout)
        outer_layout.addLayout(tree_layout)
        self.setLayout(outer_layout)

        self.cb_date = QtWidgets.QDateEdit()
        main_layout.addWidget(self.cb_date)
        self.cb_date.setDate(
            QtCore.QDate(date.year, date.month, date.day)
        )

        self.time_editors = {
            self.START_TIME_KEY: QtWidgets.QTimeEdit(),
            self.END_TIME_KEY: QtWidgets.QTimeEdit()
        }
        for name, time_editor in self.time_editors.items():
            layout = QtWidgets.QHBoxLayout()
            time_editor.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed
            )
            time_editor.setMinimumSize(100, 30)
            label = QtWidgets.QLabel(name)
            label.setMinimumSize(100, 30)
            layout.addWidget(label)
            layout.addWidget(time_editor)
            main_layout.addLayout(layout)

        # TODO: can we find a way to avoid this? feels unneat
        if start_time >= Time(23, 59):
            start_time = Time(23, 59)
        if end_time >= Time(23, 59):
            end_time = Time(23, 59)
        self.time_editors[self.START_TIME_KEY].setTime(
            QtCore.QTime(start_time.hour, start_time.minute)
        )
        self.time_editors[self.END_TIME_KEY].setTime(
            QtCore.QTime(end_time.hour, end_time.minute)
        )
        main_layout.addSpacing(10)

        self.tab_widget = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tab_widget)
        task_selection_tab = QtWidgets.QWidget()
        task_selection_layout = QtWidgets.QVBoxLayout()
        task_selection_tab.setLayout(task_selection_layout)
        self.tab_widget.addTab(task_selection_tab, "Task")

        task_label = QtWidgets.QLabel("")
        self.task_combo_box = TaskTreeComboBox(
            tree_root,
            tree_manager,
            task_label,
            calendar_item.tree_item,
        )
        task_selection_layout.addStretch()
        task_selection_layout.addWidget(task_label)
        task_selection_layout.addWidget(self.task_combo_box)
        task_selection_layout.addStretch()

        event_tab = QtWidgets.QWidget()
        event_layout = QtWidgets.QVBoxLayout()
        event_tab.setLayout(event_layout)
        self.tab_widget.addTab(event_tab, "Event")

        event_category_label = QtWidgets.QLabel("Category")
        self.event_category_line_edit = QtWidgets.QLineEdit()
        if calendar_item.category:
            self.event_category_line_edit.setText(calendar_item.category)
        event_name_label = QtWidgets.QLabel("Name")
        self.event_name_line_edit = QtWidgets.QLineEdit()
        if calendar_item.name:
            self.event_name_line_edit.setText(calendar_item.name)
        event_layout.addStretch()
        event_layout.addWidget(event_category_label)
        event_layout.addWidget(self.event_category_line_edit)
        event_layout.addStretch()
        event_layout.addWidget(event_name_label)
        event_layout.addWidget(self.event_name_line_edit)
        event_layout.addStretch()
        if self._calendar_item.type == CalendarItemType.EVENT:
            self.tab_widget.setCurrentIndex(1)

        self.background_checkbox = QtWidgets.QCheckBox("Set as background")
        if calendar_item.is_background:
            self.background_checkbox.setCheckState(2)
        main_layout.addWidget(self.background_checkbox)

        main_layout.addSpacing(10)

        buttons_layout = QtWidgets.QHBoxLayout()
        if as_editor:
            self.delete_button = QtWidgets.QPushButton("Delete Calendar Item")
            buttons_layout.addWidget(self.delete_button)
            self.delete_button.clicked.connect(self.delete_item_and_close)
        accept_button_text = (
            "Edit Calendar Item" if self.is_editor else "Add Calendar Item"
        )
        self.accept_button = QtWidgets.QPushButton(accept_button_text)
        buttons_layout.addWidget(self.accept_button)
        self.accept_button.clicked.connect(self.accept_and_close)

        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()

        self.accept_button.setFocus(True)

        # TODO: will be nicer to have one (or maybe both) of the two
        # treeviews as a widget on the RHS
        # task_tree_scroll_area = QtWidgets.QScrollArea()
        # # tree_layout.addWidget(outliner_scroll_area)
        # tree_layout.addWidget(task_tree_scroll_area)

    @property
    def start_datetime(self):
        """Get starting datetime for item, based on values set in editor.

        Returns:
            (DateTime): starting datetime.
        """
        date = self.cb_date.date()
        time = self.time_editors[self.START_TIME_KEY].time()
        return DateTime(
            date.year(), date.month(), date.day(), time.hour(), time.minute()
        )

    @property
    def end_datetime(self):
        """Get ending datetime for item, based on values set in editor.

        Returns:
            (DateTime): ending datetime.
        """
        date = self.cb_date.date()
        time = self.time_editors[self.END_TIME_KEY].time()
        return DateTime(
            date.year(), date.month(), date.day(), time.hour(), time.minute()
        )

    @property
    def type(self):
        """Get type of calendar item.

        Returns:
            (CalendarItemType): type of item, based on current selected tab.
        """
        if self.tab_widget.currentIndex() == 1:
            return CalendarItemType.EVENT
        return CalendarItemType.TASK

    @property
    def tree_item(self):
        """Get tree item, if this is in task mode.

        Returns:
            (Task or None): selected task tree item, if one exists.
        """
        return self.task_combo_box.selected_task_item

    @property
    def category(self):
        """Get name of event category.

        Returns:
            (str): name of category.
        """
        if self.tab_widget.currentIndex() == 0:
            if self.task_combo_box.selected_task_item:
                task = self.task_combo_box.selected_task_item
                return task.top_level_task().name
            return ""
        else:
            return self.event_category_line_edit.text()

    @property
    def name(self):
        """Get name of calendar item.

        Returns:
            (str): name of calendar item.
        """
        if self.tab_widget.currentIndex() == 0:
            if self.task_combo_box.selected_task_item:
                return self.task_combo_box.selected_task_item.name
            return ""
        else:
            return self.event_name_line_edit.text()

    @property
    def is_background(self):
        """Return whether or not this item is a background item.

        Returns:
            (bool): whether or not this item is a background item.
        """
        return bool(self.background_checkbox.checkState())

    def accept_and_close(self):
        """Run add or modify calendar item edit.

        Called when user clicks accept.
        """
        if self.is_editor:
            ModifyCalendarItem.create_and_run(
                self._calendar,
                self._calendar_item,
                self.start_datetime,
                self.end_datetime,
                self.type,
                self.tree_item,
                self.category,
                self.name,
                self.is_background,
            )
        else:
            # TODO: feels odd that this just discards the item we're editing
            # should maybe make the item an optional field of this class and
            # pass in the item params as arguments when creating instead?
            AddCalendarItem.create_and_run(
                self._calendar,
                self.start_datetime,
                self.end_datetime,
                self.type,
                self.tree_item,
                self.category,
                self.name,
                self.is_background
            )
        self.accept()
        self.close()

    def delete_item_and_close(self):
        """Run remove calendar item edit.

        Called when user clicks delete.
        """
        RemoveCalendarItem.create_and_run(
            self._calendar,
            self._calendar_item
        )
        self.reject()
        self.close()


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
            tree_root,
            tree_manager,
            label,
            tree_item=None,
            parent=None):
        model = FullTaskTreeModel(tree_root, tree_manager)
        tree_view = QtWidgets.QTreeView()
        tree_view.setModel(model)
        super(TaskTreeComboBox, self).__init__(
            label,
            tree_item,
            parent=parent
        )
        self.setup(model, tree_view, tree_root)
