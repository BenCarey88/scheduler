"""Tacker tab."""

from functools import partial
from types import new_class

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, DateTime, Time
from scheduler.api.edit.task_edit import UpdateTaskHistoryEdit
from scheduler.api.tree.task import (
    Task,
    TaskHistory,
    TaskStatus,
    TaskValueType
)
from scheduler.ui.tabs.base_tab import BaseTab
from scheduler.ui import constants, utils

from .tracker_model import TrackerModel


# TODO: base class here is pretty much identical to calendar, as is model,
# should do some sharing
class TrackerTab(BaseTab):
    """Tracker tab."""

    WEEK_START_DAY = Date.SAT

    def __init__(
            self,
            tree_root,
            tree_manager,
            outliner,
            calendar,
            tracker,
            parent=None):
        """Setup timetable main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner widget.
            calendar (Calendar): calendar object.
            tracker (Tracker): tracker object.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TrackerTab, self).__init__(
            tree_root,
            tree_manager,
            outliner,
            parent=parent
        )
        utils.set_style(self, "tracker.qss")
        self.tracker = tracker
        date = Date.now()
        self.calendar_week = calendar.get_week_containing_date(
            date,
            starting_day=self.WEEK_START_DAY
        )

        navigator_panel = QtWidgets.QWidget()
        navigator_panel.setFixedHeight(30)
        navigator_layout = QtWidgets.QHBoxLayout()
        navigator_layout.setContentsMargins(0, 0, 0, 0)
        navigator_panel.setLayout(navigator_layout)
        self.outer_layout.addWidget(navigator_panel)

        self.date_label = QtWidgets.QLabel(self.get_date_label())
        prev_week_button = QtWidgets.QPushButton("<")
        next_week_button = QtWidgets.QPushButton(">")
        view_type_dropdown = QtWidgets.QComboBox()
        view_type_dropdown.addItems(["week"])

        navigator_layout.addWidget(self.date_label)
        navigator_layout.addStretch()
        navigator_layout.addWidget(prev_week_button)
        navigator_layout.addWidget(next_week_button)
        navigator_layout.addStretch()
        navigator_layout.addWidget(view_type_dropdown)

        self.table = TrackerView(
            tree_root,
            tree_manager,
            tracker,
            self.calendar_week
        )
        self.outer_layout.addWidget(self.table)

        prev_week_button.clicked.connect(self.change_to_prev_week)
        next_week_button.clicked.connect(self.change_to_next_week)

    def update(self):
        """Update widget."""
        self.table.update()

    def get_date_label(self):
        """Get date label for current week.

        Returns:
            (str): label to use for date.
        """
        start_date = self.calendar_week.start_date
        end_date = self.calendar_week.end_date
        if start_date.month == end_date.month:
            return " {0} {1}".format(
                Date.month_string_from_int(start_date.month, short=False),
                start_date.year
            )
        elif start_date.year == end_date.year:
            return " {0} - {1} {2}".format(
                Date.month_string_from_int(start_date.month),
                Date.month_string_from_int(end_date.month),
                start_date.year
            )
        else:
            return " {0} {1} - {2} {3}".format(
                Date.month_string_from_int(start_date.month),
                start_date.year,
                Date.month_string_from_int(end_date.month),
                end_date.year
            )

    def change_to_prev_week(self):
        """Set calendar view to use previous week."""
        self.calendar_week = self.calendar_week.prev_week()
        self.table.set_to_week(self.calendar_week)
        self.date_label.setText(self.get_date_label())

    def change_to_next_week(self):
        """Set calendar view to use next week."""
        self.calendar_week = self.calendar_week.next_week()
        self.table.set_to_week(self.calendar_week)
        self.date_label.setText(self.get_date_label())


class TrackerView(QtWidgets.QTableView):

    def __init__(
            self,
            tree_root,
            tree_manager,
            tracker,
            calendar_week,
            parent=None):
        """Initialise tracker delegate item.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager object.
            tracker (Tracker): tracker object.
            calendar_week (CalendarWeek): the week we're tracking.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TrackerView, self).__init__(parent)
        utils.set_style(self, "tracker_view.qss")
        self.calendar_week = calendar_week
        model = TrackerModel(calendar_week, self)
        self.setModel(model)
        self.setItemDelegate(TrackerDelegate(self, tracker))
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.open_editors()

    def update(self):
        """Update widget and viewport."""
        self.open_editors()
        self.viewport().update()

    def set_to_week(self, week):
        """Set view to use given week.

        Args:
            week (CalendarWeek): the calendar week to use.
        """
        self.calendar_week = week
        model = TrackerModel(week, self)
        self.setModel(model)
        self.open_editors()

    # TODO this page shares a lot of functionality with TimetableView - maybe
    # make a bunch of base classes to inherit from (same for the model)
    def resize_table(self):
        """Resize table view."""
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def resizeEvent(self, event):
        """Resize event.

        Args:
            event (QtCore.QEvent): the event.
        """
        super(TrackerView, self).resizeEvent(event)
        self.open_editors()
        self.resize_table()

    def open_editors(self):
        """Open persistent editors on each column."""
        model = self.model()
        for i in range(model.num_rows):
            for j in range(model.num_cols):
                index = model.index(i, j, QtCore.QModelIndex())
                if index.isValid():
                    if self.isPersistentEditorOpen(index):
                        self.closePersistentEditor(index)
                    self.openPersistentEditor(index)
        self.viewport().update()

    def row_count(self):
        """Get number of rows of table.

        Returns:
            (int): number of rows.
        """
        return self.model().rowCount(QtCore.QModelIndex())

    def column_count(self):
        """Get number of columns of table.

        Returns:
            (int): number of columns.
        """
        return self.model().columnCount(QtCore.QModelIndex())


class TrackerDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for tracker."""
    def __init__(self, table, tracker, parent=None):
        """Initialise task delegate item.
        
        Args:
            table (QtWidgets.QTableView): table widget this is delegate of.
            tracker (Tracker): tracker object.
        """
        super(TrackerDelegate, self).__init__(parent)
        self.table = table
        self.tracker = tracker

    @property
    def calendar_week(self):
        """Get calendar week.

        Implemented as a property to stay up to date  with parent class.

        Returns:
            (CalendarWeek): calendar week
        """
        return self.table.calendar_week

    def sizeHint(self, option, index):
        """Get size hint for this item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item.

        Returns:
            (QtCore.QSize): size hint.
        """
        return self.get_fixed_size()

    def get_fixed_size(self):
        """Get fixed size for widgets.

        Returns:
            (QtCore.QSize): size hint.
        """
        table_size = self.table.viewport().size()
        line_width = 1
        rows = self.table.row_count() or 1
        cols = self.table.column_count() or 1
        width = (table_size.width() - (line_width * (cols - 1))) / cols
        height = (table_size.height() -  (line_width * (rows - 1))) / rows
        return QtCore.QSize(width, height)

    def get_layout_from_task(self, task, date):
        """Get qt layout of widgets corresponding to given tracked task.

        Args:
            task (Task): task we're tracking.
            date (Date): date we're getting widget for.

        Returns:
            (QtWidgets.QLayout): layout of widgets for given task value.
        """
        task_value_type = task.value_type
        # TODO: task history should be keyed by date not date string
        task_history_at_date = task.history.dict.get(str(date), {})
        status = task_history_at_date.get(
            TaskHistory.STATUS_KEY,
            TaskStatus.UNSTARTED
        )

        value = task_history_at_date.get(
            TaskHistory.VALUE_KEY,
            None
        )

        if task_value_type == TaskValueType.MULTI:
            layout = QtWidgets.QVBoxLayout()
            label = QtWidgets.QLabel(task.name)
            label.setStyleSheet("font-weight: bold")
            layout.addWidget(label)
            for subtask in task.get_all_children():
                layout.addLayout(
                    self.get_layout_from_task(subtask, date)
                )
            layout.setContentsMargins(1, 1, 1, 10)
            return layout

        if task_value_type == TaskValueType.NONE:
            value_widget = QtWidgets.QCheckBox()
            value_widget.setCheckState(
                constants.TASK_STATUS_CHECK_STATES.get(status)
            )
            value_widget.stateChanged.connect(
                partial(self.update_task_value, task, date, value_widget)
            )

        elif task_value_type == TaskValueType.STRING:
            value_widget = QtWidgets.QLineEdit(value or "")
            value_widget.editingFinished.connect(
                partial(self.update_task_value, task, date, value_widget)
            )

        elif task_value_type == TaskValueType.INT:
            value_widget = QtWidgets.QSpinBox()
            value_widget.setValue(value or 0)
            value_widget.editingFinished.connect(
                partial(self.update_task_value, task, date, value_widget)
            )

        elif task_value_type == TaskValueType.FLOAT:
            value_widget = QtWidgets.QDoubleSpinBox()
            value_widget.setValue(value or 0)
            value_widget.editingFinished.connect(
                partial(self.update_task_value, task, date, value_widget)
            )

        elif task_value_type == TaskValueType.TIME:
            value_widget = QtWidgets.QStackedWidget()
            push_button = QtWidgets.QPushButton("    ")
            time_widget = QtWidgets.QTimeEdit(QtCore.QTime(0, 0, 0))
            value_widget.addWidget(push_button)
            value_widget.addWidget(time_widget)
            push_button.clicked.connect(
                partial(value_widget.setCurrentIndex, 1)
            )
            if value:
                # TODO: task history should do this string conversion for us
                time = Time.from_string(value)
                time_widget.setTime(
                    QtCore.QTime(time.hour, time.minute, time.second)
                )
                value_widget.setCurrentIndex(1)
            time_widget.editingFinished.connect(
                partial(self.update_task_value, task, date, time_widget)
            )

        value_widget.setFixedHeight(30)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel(task.name))
        layout.addStretch()
        layout.addWidget(value_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        return layout

    def update_task_value(self, task, date, value_widget):
        """Run edit to update task value.

        Args:
            task (Task): task to update.
            date (Date): date to update.
            value_widget (QtWidgets.QWidget): widget to get new value from.
        """
        date_time = DateTime.from_date_and_time(date, Time())
        value = None
        status = None

        if task.value_type == TaskValueType.NONE:
            # if value type is None we set status instead of value
            # TODO: this is a really gross way to do things really
            for status_, state in constants.TASK_STATUS_CHECK_STATES.items():
                if value_widget.checkState() == state:
                    status = status_
                    break
            if not status:
                return
        elif task.value_type == TaskValueType.STRING:
            value = value_widget.text()
        elif task.value_type in (TaskValueType.INT, TaskValueType.FLOAT):
            value = value_widget.value()
        elif task.value_type == TaskValueType.TIME:
            # TODO: this should be fixed so it doesn't need to be a string
            qtime = value_widget.time()
            value=str(Time(qtime.hour(), qtime.minute(), qtime.second()))

        UpdateTaskHistoryEdit.create_and_run(
            task,
            date_time,
            new_value=value,
            new_status=status
        )

    def createEditor(self, parent, option, index):
        """Create editor widget for edit role.

        Args:
            parent (QtWidgets.QWidget): parent widget.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.

        Returns:
            (QtWidgets.QWidget): editor widget.
        """
        editor_widget = QtWidgets.QFrame(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        editor_widget.setLayout(layout)
        editor_widget.setFixedSize(self.get_fixed_size())

        calendar_day = self.calendar_week.get_day_at_index(index.column())
        for task in self.tracker.get_tracked_tasks():
            task_layout = self.get_layout_from_task(task, calendar_day.date)
            layout.addLayout(task_layout)
            layout.addStretch()
        layout.addStretch()

        return editor_widget
