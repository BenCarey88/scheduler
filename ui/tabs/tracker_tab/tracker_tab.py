"""Tacker tab."""

from collections import OrderedDict
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import DateTime, Time
from scheduler.api.tree.task import TaskValueType

from scheduler.ui.models.table import TrackerWeekModel
from scheduler.ui.tabs.base_calendar_tab import (
    BaseCalendarTab,
    BaseWeekTableView
)
from scheduler.ui.widgets.navigation_panel import DateType, ViewType
from scheduler.ui import constants, utils


class TrackerTab(BaseCalendarTab):
    """Tracker tab."""
    def __init__(self, project, parent=None):
        """Setup tracker tab.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        name = "tracker"
        main_views_dict = OrderedDict([
            (
                (DateType.WEEK, ViewType.TIMETABLE),
                TrackerView(name, project)
            ),
        ])
        super(TrackerTab, self).__init__(
            name,
            project,
            main_views_dict,
            DateType.WEEK,
            ViewType.TIMETABLE,
            parent=parent,
        )
        utils.set_style(self, "tracker.qss")


class TrackerView(BaseWeekTableView):
    """Tracker table view."""
    def __init__(self, name, project, parent=None):
        """Initialise tracker table view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TrackerView, self).__init__(
            name,
            project,
            TrackerWeekModel(project.calendar),
            parent=parent,
        )
        utils.set_style(self, "tracker_view.qss")
        self.setItemDelegate(
            TrackerDelegate(self, project.tracker, self.tree_manager)
        )
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
        super(TrackerView, self).update()

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
    def __init__(self, table, tracker, tree_manager, parent=None):
        """Initialise task delegate item.
        
        Args:
            table (QtWidgets.QTableView): table widget this is delegate of.
            tracker (Tracker): tracker object.
            tree_manager (TreeManager): tree manager object.
            parent (QtWidgets.QWidget or None): Qt parent of delegate.
        """
        super(TrackerDelegate, self).__init__(parent)
        self.table = table
        self.tracker = tracker
        self.tree_manager = tree_manager

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
        status = task.history.get_status_at_date(date)
        value = task.history.get_value_at_date(date)

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

        self.tree_manager.update_task(
            task,
            date_time,
            status,
            value,
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
