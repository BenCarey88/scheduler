"""Scheduler week view."""

from calendar import calendar
import math

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import DateTime, Time, TimeDelta
from scheduler.api.calendar.scheduled_item import BaseScheduledItem
from scheduler.api.edit.edit_callbacks import (
    CallbackType as CT,
    CallbackItemType,
)
from scheduler.ui import constants, utils
from scheduler.ui.models.table import SchedulerWeekModel
from scheduler.ui.tabs.base_calendar_view import BaseWeekTableView
from scheduler.ui.dialogs import ScheduledItemDialog
from .scheduler_widgets import SelectionRect, ScheduledItemWidget


class SchedulerTimetableView(BaseWeekTableView):
    """Scheduler view widget for some number of days."""
    HOVERED_ITEM_SIGNAL = QtCore.pyqtSignal(BaseScheduledItem)
    HOVERED_ITEM_REMOVED_SIGNAL = QtCore.pyqtSignal()

    DAY_START = Time(hour=0)
    DAY_END = Time(hour=23, minute=59, second=59)
    TIME_INTERVAL = TimeDelta(hours=1)
    SELECTION_TIME_STEP = TimeDelta(minutes=15)
    SELECTION_TIME_STEP_SECS = SELECTION_TIME_STEP.total_seconds()
    ITEM_BORDER_SIZE = 1

    def __init__(
            self,
            name,
            project,
            num_days=7,
            parent=None):
        """Initialise calendar view.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            num_days (int): num_days.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        self.scheduled_item_widgets = []
        self.selection_rect = None
        self.selected_scheduled_item = None
        self.hovered_item = None
        super(SchedulerTimetableView, self).__init__(
            name,
            project,
            SchedulerWeekModel(project.calendar, num_days=num_days),
            parent=parent,
        )
        self.schedule_manager = project.get_schedule_manager()
        # TODO: allow to change this and set as user pref
        self.open_dialog_on_drop_event = True
        self.display_widget_buttons = True
        self.refresh_scheduled_items_list()

        self.setItemDelegate(SchedulerDelegate(self))
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.resize_table()

        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)        
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.setMouseTracking(True)

        self.timer_id = self.startTimer(constants.LONG_TIMER_INTERVAL)
        self.installEventFilter(self)

    def refresh_scheduled_items_list(self, *args):
        """Refresh list of scheduled items.

        Unused args are passed so this can be connected to callbacks.
        """
        self.scheduled_item_widgets = [
            ScheduledItemWidget(self, self.schedule_manager, item)
            for calendar_day in self.calendar_week.iter_days()
            for item in self.schedule_manager.iter_filtered_items(
                self.filter_manager,
                calendar_day,
            )
        ]
        # Put background items below foreground ones
        self.scheduled_item_widgets.sort(
            key=(lambda w : 1 - int(w.scheduled_item.is_background))
        )
        self.viewport().update()

    # def on_view_changed(self):
    #     """Callback for when this view is loaded."""
    #     super(BaseWeekTableView, self).on_view_changed()
    #     date_time = DateTime.now()
    #     time = Time(10,0,0)
    #     y_val = self.y_pos_from_time(time)
    #     y_val -= (self.height() / 2)
    #     y_val = max(y_val, self.rect().top())
    #     self.verticalScrollBar().setValue(y_val)

    def on_outliner_filter_changed(self, *args):
        """Callback for what to do when filter is changed in outliner."""
        super(BaseWeekTableView, self).on_outliner_filter_changed(*args)
        self.refresh_scheduled_items_list()

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        if (self._is_active and
                (callback_type in [CT.TREE_REMOVE, CT.TREE_ADD]
                or callback_type[0] == CallbackItemType.SCHEDULER)):
            self.refresh_scheduled_items_list()
        super(SchedulerTimetableView, self).post_edit_callback(
            callback_type,
            *args
        )

    def update(self):
        """Update widget."""
        self.refresh_scheduled_items_list()
        super(SchedulerTimetableView, self).update()

    def set_to_calendar_period(self, calendar_week):
        """Set view to given calendar_week.

        Args:
            calendar_week (CalendarWeek): calendar week to set to.
        """
        super(SchedulerTimetableView, self).set_to_calendar_period(
            calendar_week
        )
        self.refresh_scheduled_items_list()

    @property
    def table_top(self):
        """Get topmost y pos of table:

        Returns:
            (int): table top y pos.
        """
        return self.rowViewportPosition(0)

    @property
    def table_bottom(self):
        """Get bottommost y pos of table:

        Returns:
            (int): table bottom y pos.
        """
        return (
            self.rowViewportPosition(self.row_count - 1) +
            self.rowHeight(self.row_count - 1)
        )

    @property
    def table_left(self):
        """Get leftmost x pos of table:

        Returns:
            (int): table left x pos.
        """
        return self.columnViewportPosition(0)

    @property
    def table_right(self):
        """Get rightmost x pos of table:

        Returns:
            (int): table right x pos.
        """
        return (
            self.columnViewportPosition(self.column_count - 1) +
            self.columnWidth(self.column_count - 1)
        )

    @property
    def table_height(self):
        """Get height of table:

        Returns:
            (int): table height.
        """
        return self.table_bottom - self.table_top

    @property
    def time_range(self):
        """Get full time range of column.

        Returns:
            (TimeDelta): time range.
        """
        return self.DAY_END - self.DAY_START

    @property
    def row_count(self):
        """Get number of rows.

        Returns:
            (int): number of rows.
        """
        return self.model().rowCount(QtCore.QModelIndex())

    @property
    def column_count(self):
        """Get number of columns.

        Returns:
            (int): number of columns.
        """
        return self.model().columnCount(QtCore.QModelIndex())

    def height_from_time_range(self, time_range):
        """Get a height representing the given time range.

        Args:
            time_range (TimeDelta): time range to represent.

        Returns:
            (int): pixel height of screen representation of that time range.
        """
        conversion_factor = self.table_height / self.time_range.total_seconds()
        return time_range.total_seconds() * conversion_factor

    def y_pos_from_time(self, time):
        """Get the y position in the table representing a given time.

        Args:
            time (Time): time to represent.

        Returns:
            (int): pixel height of y position representing that time.
        """
        time_from_start = time - self.DAY_START
        return self.table_top + self.height_from_time_range(time_from_start)

    def time_range_from_height(self, height):
        """Get the time range represented by the given height.

        Args:
            height (int): pixel height of screen representation a time range.

        Returns:
            (TimeDelta): time range represented by that height.
        """
        return height * self.time_range / self.table_height

    def time_from_y_pos(self, y_pos):
        """Get the time represented by a given pixel height.

        Args:
            y_pos (int): pixel height on screen.

        Returns:
            (Time): time represented by that height.
        """
        if y_pos < self.table_top:
            return self.DAY_START
        if y_pos > self.table_bottom:
            return self.DAY_END
        y_pos_from_top = y_pos - self.table_top
        return self.DAY_START + self.time_range_from_height(y_pos_from_top)

    def round_y_pos_to_time_step(self, y_pos):
        """Round y_pos based on self.SELECTION_TIME_STEP.

        Specifically, round it so that the time that is represented by y_pos
        is rounded to the nearest SELECTION_TIME_STEP.

        Args:
            y_pos (int): height in pixels of point on the table view.

        Returns:
            (int): rounded y_pos.
        """
        time = self.time_from_y_pos(y_pos)
        scaled_time_secs = (
            (time - self.DAY_START) / self.SELECTION_TIME_STEP_SECS
        ).total_seconds()
        rounded_time_secs = min(
            round(scaled_time_secs) * self.SELECTION_TIME_STEP_SECS,
            (self.DAY_END - self.DAY_START).total_seconds()
        )
        rounded_time = self.DAY_START + TimeDelta(seconds=rounded_time_secs)
        return self.y_pos_from_time(rounded_time)

    def round_height_to_time_step(self, height):
        """Round height based on self.SELECTION_TIME_STEP.

        Specifically, round it so that the time_range that is represented by
        height is rounded to the nearest SELECTION_TIME_STEP.

        Args:
            height (int): a height in pixels.

        Returns:
            (int): rounded height.
        """
        time_range = self.time_range_from_height(height)
        scaled_time_range_secs = (
            time_range / self.SELECTION_TIME_STEP_SECS
        ).total_seconds()
        rounded_time_range_secs = (
            round(scaled_time_range_secs) * self.SELECTION_TIME_STEP_SECS
        )
        rounded_time_range = TimeDelta(seconds=rounded_time_range_secs)
        return self.height_from_time_range(rounded_time_range)

    def column_from_mouse_pos(self, pos):
        """Get column that the given mouse position is in.

        Args:
            pos (QtCore.QPoint): mouse position.

        Returns:
            (int or None): column the mouse pos is in, if it's in one.
        """
        if (self.table_left < pos.x() < self.table_right
                and self.table_top < pos.y() < self.table_bottom):
            column = 0
            for i, _ in enumerate(self.calendar_week.iter_days()):
                if pos.x() < self.columnViewportPosition(i):
                    break
                column = i
            return column
        return None

    def column_from_date(self, date):
        """Get column from date.

        Args:
            date (Date): date to query.

        Returns:
            (int): the column number corresponding to that date.
        """
        return (date - self.calendar_week.start_date).days

    def date_from_column(self, col):
        """Get date for given column.

        Args:
            col (int): the column number.

        Returns:
            (Date): the date corresponding to the given column.
        """
        return self.calendar_week.start_date + TimeDelta(days=col)

    def datetime_from_pos(self, pos):
        """Get the datetime represented by a given position.

        Args:
            pos (QtCore.QPoint): the qpoint.

        Returns:
            (DateTime or None): datetime represented by given (x, y) position,
                if there is one.
        """
        column = self.column_from_mouse_pos(pos)
        if column is None:
            return
        time = self.time_from_y_pos(pos.y())
        date = self.date_from_column(column)
        return DateTime.from_date_and_time(date, time)

    def rect_from_date_time_range(self, date, time_start, time_end):
        """Get a qrect from a date and time range.

        Args:
            date (Date): the date.
            time_start (Time): start time.
            time_end (Time): end time.

        Returns:
            (QtCore.QRectF): rectangle representing this range in the view.
        """
        column = self.column_from_date(date)
        x_start = self.columnViewportPosition(column)
        width = self.columnWidth(column)
        y_start = self.y_pos_from_time(time_start)
        height = self.height_from_time_range(time_end - time_start)
        return QtCore.QRectF(x_start, y_start, width, height)

    def resize_table(self):
        """Resize table rows and columns to contents."""
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def resizeEvent(self, event):
        """Resize event, called when view is resized.

        Args:
            event (QtCore.QEvent): the resize event.
        """
        super(SchedulerTimetableView, self).resizeEvent(event)
        self.resize_table()

    def timerEvent(self, event):
        """Called every timer_interval.

        This is used to repaint so that current time marker stays up to date.

        Args:
            event (QtCore.QEvent): the timer event.
        """
        if event.timerId() == self.timer_id:
            self.viewport().update()
        super(SchedulerTimetableView, self).timerEvent(event)

    def paintEvent(self, event):
        """Override paint event to draw item rects and selection rect.

        Args:
            event (QtCore.QEvent): the paint event.
        """
        super(SchedulerTimetableView, self).paintEvent(event)

        # Create painter
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen = QtGui.QPen(constants.BLACK, self.ITEM_BORDER_SIZE)
        painter.setPen(pen)

        # Scheduled item rects
        for item_widget in self.scheduled_item_widgets:
            item_widget.paint(painter)

        # Selection Rect
        if self.selection_rect is not None:
            self.selection_rect.paint(painter)

        # Current Time Line
        date_time = DateTime.now()
        for i, calendar_day in enumerate(self.calendar_week.iter_days()):
            if calendar_day.date == date_time.date():
                line_thickness = 3
                x_start = self.columnViewportPosition(i)
                line_width = self.columnWidth(i)
                y_start = self.y_pos_from_time(date_time.time())
                path = QtGui.QPainterPath()
                rect = QtCore.QRectF(
                    x_start,
                    y_start - line_thickness/2,
                    line_width,
                    line_thickness
                )
                path.addRoundedRect(rect, 3, 3)
                painter.setBrush(
                    QtGui.QBrush(constants.SCHEDULER_TIME_LINE_COLOR)
                )
                painter.setClipPath(path)
                painter.fillPath(path, painter.brush())
                break

    def mousePressEvent(self, event):
        """Override mouse press event for interaction with scheduled items.

        Args:
            event (QtCore.QEvent): the mouse press event.
        """
        if self.hovered_item is not None:
            self.hovered_item = None
            self.HOVERED_ITEM_REMOVED_SIGNAL.emit()

        pos = event.pos()
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        # shift modifier used to create new selection rect
        if modifiers != QtCore.Qt.KeyboardModifier.ShiftModifier:
            # item rects drawn last are the ones we should click first
            for item_widget in reversed(self.scheduled_item_widgets):
                if item_widget.contains(pos):
                    self.selected_scheduled_item = item_widget
                    if self.display_widget_buttons:
                        # if widget buttons are displayed, check them first
                        if item_widget.over_delete_button(pos):
                            item_widget.delete_pressed = True
                            return
                        if item_widget.over_checkbox(pos):
                            item_widget.checkbox_pressed = True
                            return
                    time = self.time_from_y_pos(pos.y())
                    item_widget.set_mouse_pos_start_time(time)
                    if item_widget.at_top(event.pos()):
                        item_widget.is_being_resized_top = True
                    elif item_widget.at_bottom(event.pos()):
                        item_widget.is_being_resized_bottom = True
                    return

        mouse_col = self.column_from_mouse_pos(pos)
        if mouse_col is not None:
            date = self.date_from_column(mouse_col)
            y_pos = self.round_y_pos_to_time_step(event.pos().y())
            time_start = self.time_from_y_pos(y_pos)
            self.selection_rect = SelectionRect(self, date, time_start)
        return super(SchedulerTimetableView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Override mouse move event for interaction with scheduled items.

        Args:
            event (QtCore.QEvent): the mouse move event.
        """
        if self.selection_rect:
            # TODO: create new method to round time directly, as otherwise
            # here we convert, round, convert back and then convert again.
            y_pos = self.round_y_pos_to_time_step(event.pos().y())
            self.selection_rect.set_time_at_selection_end(
                self.time_from_y_pos(y_pos)
            )
            self.viewport().update()

        elif self.selected_scheduled_item:
            if (not self.selected_scheduled_item.delete_pressed
                    and not self.selected_scheduled_item.checkbox_pressed):
                mouse_col = self.column_from_mouse_pos(event.pos())
                if mouse_col is not None:
                    date = self.date_from_column(mouse_col)
                else:
                    date = self.selected_scheduled_item.date
                y_pos = self.round_height_to_time_step(event.pos().y())
                orig_y_pos = self.y_pos_from_time(
                    self.selected_scheduled_item.mouse_pos_start_time
                )
                y_pos_change = self.round_height_to_time_step(
                    y_pos - orig_y_pos
                )
                timedelta = self.time_range_from_height(y_pos_change)
                success = self.selected_scheduled_item.apply_time_change(
                    timedelta,
                    date,
                )
                if success:
                    self.viewport().update()

        else:
            for scheduled_item_widget in reversed(self.scheduled_item_widgets):
                if (scheduled_item_widget.at_top(event.pos())
                        or scheduled_item_widget.at_bottom(event.pos())):
                    QtGui.QGuiApplication.setOverrideCursor(
                        QtCore.Qt.CursorShape.SizeVerCursor
                    )
                else:
                    QtGui.QGuiApplication.restoreOverrideCursor()
                if scheduled_item_widget.contains(event.pos()):
                    self.hovered_item = scheduled_item_widget.scheduled_item
                    self.HOVERED_ITEM_SIGNAL.emit(self.hovered_item)
                    break
            else:
                if self.hovered_item is not None:
                    self.hovered_item = None
                    self.HOVERED_ITEM_REMOVED_SIGNAL.emit()

        return super(SchedulerTimetableView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Override mouse release event for interaction with scheduled items.

        Args:
            event (QtCore.QEvent): the mouse release event.
        """
        if self.selection_rect:
            if self.selection_rect.time_range.total_seconds() != 0:
                item_editor = ScheduledItemDialog(
                    self.tree_manager,
                    self.schedule_manager,
                    start_datetime=self.selection_rect.start_datetime,
                    end_datetime=self.selection_rect.end_datetime,
                    tree_item=self.filter_manager.get_current_tree_item(),
                )
                item_editor.exec()
            self.selection_rect = None

        elif self.selected_scheduled_item:
            item_widget = self.selected_scheduled_item
            # if delete pressed and still over button, delete item
            if item_widget.delete_pressed:
                if item_widget.over_delete_button(event.pos()):
                    modifiers = QtWidgets.QApplication.keyboardModifiers()
                    force = (
                        modifiers == QtCore.Qt.KeyboardModifier.ControlModifier
                    )
                    item_widget.delete(force=force)
                item_widget.delete_pressed = False
            # if checkbox pressed and still over button, check item
            elif item_widget.checkbox_pressed:
                if item_widget.over_checkbox(event.pos()):
                    item_widget.toggle_checkbox()
                item_widget.checkbox_pressed = False
            # if being moved or resized, deselect the item to trigger edit
            elif (item_widget.is_being_moved
                    or item_widget.is_being_resized_top
                    or item_widget.is_being_resized_bottom):
                item_widget.deselect()
            # otherwise, we want to open the editor
            else:
                item = item_widget.get_item_to_modify()
                item_editor = ScheduledItemDialog(
                    self.tree_manager,
                    self.schedule_manager,
                    scheduled_item=item,
                )
                item_editor.exec()
            self.selected_scheduled_item = None

        return super(SchedulerTimetableView, self).mouseReleaseEvent(event)

    def eventFilter(self, obj, event):
        """Event filter for when object is clicked.

        Args:
            obj (QtCore.QObject): QObject that event is happening on.
            event (QtCore.QEvent): event that is happening.
        """
        if obj == self and event.type() == QtCore.QEvent.Leave:
            QtGui.QGuiApplication.restoreOverrideCursor()
            if self.hovered_item is not None:
                self.hovered_item = None
                self.HOVERED_ITEM_REMOVED_SIGNAL.emit()
        return False

    def dropEvent(self, event):
        """Override drop event for dropping task items.

        Note that this drop event is enabled through the model by setting
        ItemIsDropEnabled flag on all indexes.

        Args:
            event (QtCore.QEvent): the drop event.
        """
        data = event.mimeData()
        tree_item = None
        planned_item = None
        if data.hasFormat(constants.OUTLINER_TREE_MIME_DATA_FORMAT):
            tree_item = utils.decode_mime_data(
                data,
                constants.OUTLINER_TREE_MIME_DATA_FORMAT,
                drop=True,
            )
        elif data.hasFormat(constants.PLANNED_ITEM_MIME_DATA_FORMAT):
            planned_item = utils.decode_mime_data(
                data,
                constants.PLANNED_ITEM_MIME_DATA_FORMAT,
                drop=True,
            )
            tree_item = planned_item.tree_item
        if tree_item is None:
            return

        date_time = self.datetime_from_pos(event.pos())
        date = date_time.date()
        time = date_time.time()
        start_time = Time(time.hour, 0, 0)
        end_time = Time(
            time.hour + 1 if time.hour < 23 else 23,
            0 if time.hour < 23 else 59,
            0 if time.hour <23 else 59,
        )
        start_date_time = DateTime.from_date_and_time(date, start_time)
        end_date_time = DateTime.from_date_and_time(date, end_time)
        item_editor = ScheduledItemDialog(
            self.tree_manager,
            self.schedule_manager,
            start_datetime=start_date_time,
            end_datetime=end_date_time,
            tree_item=tree_item,
            planned_item=planned_item,
        )
        if self.open_dialog_on_drop_event:
            item_editor.exec()
        else:
            item_editor.accept_and_close()


class SchedulerDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for calendar."""
    NUM_ROWS_ON_SCREEN = 12

    def __init__(self, table, parent=None):
        """Initialise task delegate item."""
        super(SchedulerDelegate, self).__init__(parent)
        self.table = table

    def sizeHint(self, option, index):
        """Get size hint for this item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item.

        Returns:
            (QtCore.QSize): size hint.
        """
        table_size = self.table.viewport().size()
        line_width = 1
        rows = self.NUM_ROWS_ON_SCREEN
        cols = self.table.column_count or 1
        width = (table_size.width() - (line_width * (cols - 1))) / cols
        height = (table_size.height() -  (line_width * (rows - 1))) / rows
        return QtCore.QSize(width, height)
