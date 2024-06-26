"""Tracker timetable view."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, DateTime, Time
from scheduler.api.edit.edit_callbacks import (
    CallbackEditType as CET,
    CallbackItemType as CIT,
)
from scheduler.api.enums import TrackedValueType

from scheduler.ui.models.table import TrackerWeekModel
from scheduler.ui.tabs.base_calendar_view import BaseWeekTableView

from scheduler.ui import constants, utils


class TrackerTimetableView(BaseWeekTableView):
    """Tracker table view."""
    def __init__(self, name, project, num_days=7, parent=None):
        """Initialise tracker table view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            num_days (int): num days to use.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TrackerTimetableView, self).__init__(
            name,
            project,
            TrackerWeekModel(project.calendar, num_days=num_days),
            parent=parent,
        )
        self.tracker_manager = project.get_tracker_manager()
        utils.set_style(self, "tracker_view.qss")
        self.setItemDelegate(
            TrackerDelegate(
                self,
                self.tracker_manager,
                self.tree_manager,
                self.filter_manager,
            )
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

    def on_view_changed(self):
        """Callback for when this view is loaded."""
        super(TrackerTimetableView, self).on_view_changed()
        self.model().beginResetModel()
        self.model().endResetModel()
        self.update()

    def on_outliner_filter_changed(self, *args):
        """Callback for what to do when filter is changed in outliner."""
        super(TrackerTimetableView, self).on_outliner_filter_changed(*args)
        self.model().beginResetModel()
        self.model().endResetModel()
        self.update()

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(TrackerTimetableView, self).pre_edit_callback(
            callback_type,
            *args,
        )
        if (self._is_active
                and callback_type[0] == CIT.TREE
                and callback_type[1] in [CET.MODIFY, CET.ADD, CET.REMOVE]):
            self.model().beginResetModel()

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(TrackerTimetableView, self).post_edit_callback(
            callback_type,
            *args,
        )
        if (self._is_active
                and callback_type[0] == CIT.TREE
                and callback_type[1] in [CET.MODIFY, CET.ADD, CET.REMOVE]):
            self.model().endResetModel()
            self.update()

    def update(self):
        """Update widget and viewport."""
        self.open_editors()
        super(TrackerTimetableView, self).update()

    def resize_table(self):
        """Resize table view."""
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def resizeEvent(self, event):
        """Resize event.

        Args:
            event (QtCore.QEvent): the event.
        """
        super(TrackerTimetableView, self).resizeEvent(event)
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
    def __init__(
            self,
            table,
            tracker_manager,
            tree_manager,
            filter_manager,
            parent=None):
        """Initialise task delegate item.
        
        Args:
            table (QtWidgets.QTableView): table widget this is delegate of.
            tracker_manager (TrackerManager): tracker manager object.
            tree_manager (TreeManager): tree manager object.
            filter_manager (FilterManager): filter manager object.
            parent (QtWidgets.QWidget or None): Qt parent of delegate.
        """
        super(TrackerDelegate, self).__init__(parent)
        self.table = table
        self.tracker_manager = tracker_manager
        self.tracker = tracker_manager.tracker
        self.tree_manager = tree_manager
        self.filter_manager = filter_manager

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

    # TODO: need to handle case where task is updated to a new value type
    # and old values at the date now have incompatible types (eg. if we have
    # an old Time value and are now have a value type of INT then we'll end
    # up trying to set a spin box to a Time, which will crash). The most
    # important thing is to handle this here, but would also be good to give
    # a warning to the user when switching tasks to a new value type if there
    # are incompatible values already saved in the task's history
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

        if task_value_type == TrackedValueType.MULTI:
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

        if task_value_type in (
                TrackedValueType.STATUS, TrackedValueType.COMPLETIONS):
            value_widget = QtWidgets.QCheckBox()
            value_widget.setCheckState(
                constants.TASK_STATUS_CHECK_STATES.get(status)
            )
            value_widget.stateChanged.connect(
                partial(self.update_task_value, task, date, value_widget)
            )

        elif task_value_type == TrackedValueType.STRING:
            value_widget = QtWidgets.QLineEdit(value or "")
            value_widget.editingFinished.connect(
                partial(self.update_task_value, task, date, value_widget)
            )

        elif task_value_type == TrackedValueType.INT:
            value_widget = QtWidgets.QSpinBox()
            value_widget.setValue(value or 0)
            value_widget.editingFinished.connect(
                partial(self.update_task_value, task, date, value_widget)
            )

        elif task_value_type == TrackedValueType.FLOAT:
            value_widget = QtWidgets.QDoubleSpinBox()
            value_widget.setValue(value or 0)
            value_widget.editingFinished.connect(
                partial(self.update_task_value, task, date, value_widget)
            )

        elif task_value_type == TrackedValueType.TIME:
            value_widget = QtWidgets.QStackedWidget()
            push_button = QtWidgets.QPushButton("    ")
            time_widget = QtWidgets.QTimeEdit(QtCore.QTime(0, 0, 0))
            value_widget.addWidget(push_button)
            value_widget.addWidget(time_widget)
            push_button.clicked.connect(
                partial(value_widget.setCurrentIndex, 1)
            )
            if value:
                # TODO: check this doesn't break now we've got Time not str
                time = value # Time.from_string(value)
                time_widget.setTime(
                    QtCore.QTime(time.hour, time.minute, time.second)
                )
                value_widget.setCurrentIndex(1)
            time_widget.editingFinished.connect(
                partial(self.update_task_value, task, date, time_widget)
            )

        # Check if target is met
        target = task.get_target_at_date(date)
        if (target is not None
                and value is not None
                and target.is_met_by_value(value)):
            value_widget.setStyleSheet("background-color: #1AE72E")
        else:
            value_widget.setStyleSheet("")

        # palette = value_widget.palette()
        # palette.setColor(palette.ColorRole.Base, QtGui.QColor(0, 255, 0))
        # value_widget.setBackgroundRole(palette.ColorRole.Base)

        value_widget.setFixedHeight(30)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel(task.name))
        layout.addStretch()
        layout.addWidget(value_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        return layout

    # TODO: keep an eye on this and remove the commented out bits if it seems
    # fine - I've just changed it to use the date only, which I believe should
    # be fine but should confirm to be sure
    def update_task_value(self, task, date, value_widget):
        """Run edit to update task value.

        Args:
            task (Task): task to update.
            date (Date): date to update.
            value_widget (QtWidgets.QWidget): widget to get new value from.
        """
        # date_time = DateTime.from_date_and_time(date, Time())
        value = None
        status = None

        if task.value_type in (
                TrackedValueType.STATUS, TrackedValueType.COMPLETIONS):
            # if value type is Status we set status instead of value
            # TODO: is this a bit of a gross way to do things really?
            # should it set the value as well, to be equal to the status?
            for status_, state in constants.TASK_STATUS_CHECK_STATES.items():
                if value_widget.checkState() == state:
                    status = status_
                    break
            if not status:
                return
        elif task.value_type == TrackedValueType.STRING:
            value = value_widget.text()
        elif task.value_type in (TrackedValueType.INT, TrackedValueType.FLOAT):
            value = value_widget.value()
        elif task.value_type == TrackedValueType.TIME:
            qtime = value_widget.time()
            # TODO: I just changed this to Time from a string, keep an
            # eye out to make sure it doesn't crash
            value=Time(qtime.hour(), qtime.minute(), qtime.second())

        self.tree_manager.update_task(
            task,
            date, #date_time,
            status,
            value,
        )

        # Check if target is met
        # TODO: this is duplicate of above code - combine to one func
        target = task.get_target_at_date(date)
        if (target is not None
                and value is not None
                and target.is_met_by_value(value)):
            value_widget.setStyleSheet("background-color: #1AE72E")
        else:
            value_widget.setStyleSheet("")

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
        iter_ = self.tracker_manager.iter_filtered_items(self.filter_manager)
        for task in iter_:
            task_layout = self.get_layout_from_task(task, calendar_day.date)
            layout.addLayout(task_layout)
            layout.addStretch()
        layout.addStretch()

        return editor_widget
