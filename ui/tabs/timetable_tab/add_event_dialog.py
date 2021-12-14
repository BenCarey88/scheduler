
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
            start_time,
            end_time,
            date,
            tree_root,
            tree_manager,
            parent=None):
        super(AddEventDialog, self).__init__(parent)

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
        self.task_combo_box = TaskViewComboBox(task_label)
        category_label = QtWidgets.QLabel("")
        self.outliner_combo_box = OutlinerComboBox(
            tree_root,
            tree_manager,
            category_label,
            self.task_combo_box,
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
        event_name_label = QtWidgets.QLabel("Name")
        self.event_name_line_edit = QtWidgets.QLineEdit()
        event_layout.addStretch()
        event_layout.addWidget(event_category_label)
        event_layout.addWidget(self.event_category_line_edit)
        event_layout.addStretch()
        event_layout.addWidget(event_name_label)
        event_layout.addWidget(self.event_name_line_edit)
        event_layout.addStretch()

        main_layout.addSpacing(10)

        self.add_event_button = QtWidgets.QPushButton("Add Event")
        main_layout.addWidget(self.add_event_button)
        main_layout.addStretch()
        self.add_event_button.clicked.connect(self.accept_and_close)
        self.add_event_button.setFocusPolicy(
            QtCore.Qt.FocusPolicy.NoFocus
        )

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
            return self.event_category_line_edit.currentText()

    @property
    def name(self):
        if self.tab_widget.currentIndex() == 0:
            if self.task_combo_box.selected_task_item:
                return self.task_combo_box.selected_task_item.name
            return ""
        else:
            return self.event_name_line_edit.currentText()

    def accept_and_close(self):
        self.accept()
        self.close()


class TreeComboBox(QtWidgets.QComboBox):
    # Thanks to http://qt.shoutwiki.com/wiki/Implementing_QTreeView_in_QComboBox_using_Qt-_Part_2

    def __init__(self, label, parent=None):
        super(TreeComboBox, self).__init__(parent=parent)
        self.label = label
        self.skip_next_hide = False
        self.selected_task_item = None
        self.setEnabled(False)

    def setup(self, model, tree_view, root):
        self.setEnabled(True)
        self.setModel(model)
        self.setView(tree_view)
        self.view().viewport().installEventFilter(self)
        self.root = root

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
    def __init__(
            self,
            tree_root,
            tree_manager,
            label,
            task_combobox,
            parent=None):
        self.tree_manager = tree_manager
        outliner = Outliner(tree_root, tree_manager)
        model = TaskCategoryModel(tree_root, tree_manager)
        super(OutlinerComboBox, self).__init__(
            label,
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
    def __init__(self, label, parent=None):
        super(TaskViewComboBox, self).__init__(
            label,
            parent=parent
        )
        self.setEnabled(False)
