
from PyQt5 import QtCore, QtGui, QtWidgets
from api.tree.task import Task
from scheduler.api import tree

from scheduler.api.tree.task import Task
from scheduler.ui import utils
from scheduler.ui.models.task_category_model import TaskCategoryModel
from scheduler.ui.models.task_model import TaskModel
from scheduler.ui.widgets.outliner import Outliner


class AddEventDialog(QtWidgets.QDialog):
    def __init__(
            self,
            tree_root,
            tree_manager,
            day_data,
            event_item,
            as_editor=False,
            parent=None):
        """
        Args:
            ...
            as_editor (bool): whether or not we're editing an existing event,
                or adding a new one.
            ...
        """
        super(AddEventDialog, self).__init__(parent)

        self._event_item = event_item
        date = event_item.date
        start_time = event_item.start_time
        end_time = event_item.end_time
        self.day_data = day_data

        accept_button_text = "Edit Event" if as_editor else "Add Event"

        utils.set_style(self, "timetable_event_widget.qss")

        flags = QtCore.Qt.WindowFlags(
            QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setMinimumSize(900, 700)

        self.setWindowTitle("Timetable Event Editor")

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
            "Start": QtWidgets.QTimeEdit(),
            "End": QtWidgets.QTimeEdit()
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

        # 23.98 =~ 59/60
        # TODO: this should be way neater
        if int(start_time) >= 23.99:
            start_time = 23.99
        if int(end_time) >= 23.99:
            end_time = 23.99
        self.time_editors["Start"].setTime(
            QtCore.QTime(
                int(start_time),
                (start_time % 1) * 60,
            )
        )
        self.time_editors["End"].setTime(
            QtCore.QTime(
                int(end_time),
                (end_time % 1) * 60,
            )
        )

        main_layout.addSpacing(10)

        # outliner_scroll_area = QtWidgets.QScrollArea()
        # outliner = Outliner(tree_root, tree_manager)
        # outliner_scroll_area.setWidget(outliner)
        # main_layout.addWidget(outliner_scroll_area)
        self.tab_widget = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tab_widget)
        task_selection_tab = QtWidgets.QWidget()
        task_selection_layout = QtWidgets.QVBoxLayout()
        task_selection_tab.setLayout(task_selection_layout)
        self.tab_widget.addTab(task_selection_tab, "Add Task")

        task_label = QtWidgets.QLabel("")
        self.task_combo_box = TaskViewComboBox(
            tree_root,
            tree_manager,
            task_label,
            event_item.tree_item,
            event_item.category_item
        )
        category_label = QtWidgets.QLabel("")
        self.outliner_combo_box = OutlinerComboBox(
            tree_root,
            tree_manager,
            category_label,
            self.task_combo_box,
            event_item.category_item
        )
        task_selection_layout.addStretch()
        task_selection_layout.addWidget(category_label)
        task_selection_layout.addWidget(self.outliner_combo_box)
        task_selection_layout.addStretch()
        task_selection_layout.addWidget(task_label)
        task_selection_layout.addWidget(self.task_combo_box)
        task_selection_layout.addStretch()

        event_tab = QtWidgets.QWidget()
        event_layout = QtWidgets.QVBoxLayout()
        event_tab.setLayout(event_layout)
        self.tab_widget.addTab(event_tab, "Add Event")

        event_category_label = QtWidgets.QLabel("Category")
        self.event_category_line_edit = QtWidgets.QLineEdit()
        if event_item.category:
            self.event_category_line_edit.setText(event_item.category)
        event_name_label = QtWidgets.QLabel("Name")
        self.event_name_line_edit = QtWidgets.QLineEdit()
        if event_item.name:
            self.event_name_line_edit.setText(event_item.name)
        event_layout.addStretch()
        event_layout.addWidget(event_category_label)
        event_layout.addWidget(self.event_category_line_edit)
        event_layout.addStretch()
        event_layout.addWidget(event_name_label)
        event_layout.addWidget(self.event_name_line_edit)
        event_layout.addStretch()

        main_layout.addSpacing(10)

        buttons_layout = QtWidgets.QHBoxLayout()
        if as_editor:
            self.delete_button = QtWidgets.QPushButton("Delete Event")
            buttons_layout.addWidget(self.delete_button)
            self.delete_button.clicked.connect(self.delete_event)
        self.accept_button = QtWidgets.QPushButton(accept_button_text)
        buttons_layout.addWidget(self.accept_button)
        self.accept_button.clicked.connect(self.accept_and_close)

        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()

        # TODO: will be nicer to have one (or maybe both) of the two
        # treeviews as a widget on the RHS
        # task_tree_scroll_area = QtWidgets.QScrollArea()
        # # tree_layout.addWidget(outliner_scroll_area)
        # tree_layout.addWidget(task_tree_scroll_area)

    @staticmethod
    def qtime_to_float(qtime):
        return qtime.hour() + qtime.minute() / 60

    @property
    def start_time(self):
        return self.qtime_to_float(self.time_editors["Start"].time())

    @property
    def end_time(self):
        return self.qtime_to_float(self.time_editors["End"].time())

    @property
    def category(self):
        if self.tab_widget.currentIndex() == 0:
            if self.outliner_combo_box.selected_task_item:
                return self.outliner_combo_box.selected_task_item.name
            return ""
        else:
            return self.event_category_line_edit.text()

    @property
    def name(self):
        if self.tab_widget.currentIndex() == 0:
            if self.task_combo_box.selected_task_item:
                return self.task_combo_box.selected_task_item.name
            return ""
        else:
            return self.event_name_line_edit.text()

    @property
    def timetable_event(self):
        return self._event_item

    def accept_and_close(self):
        self._event_item.set_time(self.start_time, self.end_time)
        if (self.tab_widget.currentIndex() == 0 
                and self.task_combo_box.selected_task_item):
            self._event_item.set_tree_item(
                self.task_combo_box.selected_task_item
            )
        else:
            self._event_item.set_category(self.category)
            self._event_item.set_name(self.name)
        self.accept()
        self.close()

    def delete_event(self):
        self.day_data.events.remove(self._event_item)
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


class OutlinerComboBox(TreeComboBox):
    # TODO: disable drag drop in this case of outliner
    def __init__(
            self,
            tree_root,
            tree_manager,
            label,
            task_combobox,
            tree_item=None,
            parent=None):
        self.tree_manager = tree_manager
        outliner = Outliner(tree_root, tree_manager)
        model = TaskCategoryModel(tree_root, tree_manager)
        super(OutlinerComboBox, self).__init__(
            label,
            tree_item,
            parent=parent
        )
        self.setup(model, outliner, tree_root)
        self.task_combobox = task_combobox
        self.currentIndexChanged.connect(self.setup_task_combobox)

    def setup_task_combobox(self, index):
        if isinstance(self.selected_task_item, Task):
            model = TaskModel(
                self.selected_task_item,
                self.tree_manager,
                num_cols=1,
            )
            tree_view = QtWidgets.QTreeView()
            tree_view.setModel(model)
            self.task_combobox.setup(model, tree_view, self.selected_task_item)


class TaskViewComboBox(TreeComboBox):
    def __init__(
            self,
            tree_root,
            tree_manager,
            label,
            task_item=None,
            task_category_item=None,
            parent=None):
        super(TaskViewComboBox, self).__init__(
            label,
            task_item,
            parent=parent
        )
        if task_item and task_category_item:
            self.setEnabled(True)
            model = TaskModel(
                task_category_item,
                tree_manager,
                num_cols=1,
            )
            tree_view = QtWidgets.QTreeView()
            tree_view.setModel(model)
            self.setup(model, tree_view, task_category_item)
