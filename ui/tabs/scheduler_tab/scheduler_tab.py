"""Scheduler Tab."""


from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import DateTime, Time, TimeDelta
from scheduler.api.calendar.scheduled_item import ScheduledItemType

from scheduler.ui.models.timetable import SchedulerDayModel, SchedulerWeekModel
from scheduler.ui.tabs.base_calendar_tab import (
    BaseCalendarTab,
    BaseDayTableView,
    BaseWeekTableView
)
from scheduler.ui.widgets.navigation_panel import DateType, ViewType
from scheduler.ui import constants, utils

from .scheduled_item_dialog import ScheduledItemDialog


class SchedulerTab(BaseCalendarTab):
    """Calendar tab."""

    def __init__(self, project, parent=None):
        """Setup calendar main view.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        name = "scheduler"
        main_views_dict = OrderedDict([
            (
                (DateType.WEEK, ViewType.TIMETABLE),
                CalendarView(name, project)
            ),
            # FOR TESTING
            (
                (DateType.DAY, ViewType.TIMETABLE),
                BaseDayTableView(
                    name, project, SchedulerDayModel(project.calendar)
                )
            ),
        ])
        super(SchedulerTab, self).__init__(
            name,
            project,
            main_views_dict,
            DateType.WEEK,
            ViewType.TIMETABLE,
            parent=parent,
        )
        utils.set_style(self, "scheduler.qss")


class SelectionRect(object):
    """Class representing a selection rectangle in the table view."""
    def __init__(self, column, date, time):
        """Initialise class.

        Args:
            column (int): column of the selection, passed for convenience.
            date (Date): the date of that column.
            time (Time): the time at the the start of the selection creation.
        """
        self.column = column
        self.date = date
        self._time_at_selection_start = time
        self._time_at_selection_end = time

    def set_time_at_selection_end(self, time):
        """Set time at other end of selection.

        Args:
            time (Time): time to set.
        """
        self._time_at_selection_end = time

    @property
    def start_time(self):
        """Get starting time of selection.

        Returns:
            (Time): start time.
        """
        return min(self._time_at_selection_start, self._time_at_selection_end)

    @property
    def end_time(self):
        """Get ending time of selection.

        Returns:
            (Time): end time.
        """
        return max(self._time_at_selection_start, self._time_at_selection_end)

    @property
    def time_range(self):
        """Get time range of selection.

        Returns:
            (TimeDelta): time range.
        """
        return self.end_time - self.start_time

    @property
    def start_datetime(self):
        """Get starting datetime of selection.

        Returns:
            (DateTime): start datetime.
        """
        return DateTime.from_date_and_time(self.date, self.start_time)

    @property
    def end_datetime(self):
        """Get ending datetime of selection.

        Returns:
            (DateTime): end datetime.
        """
        return DateTime.from_date_and_time(self.date, self.end_time)


class SelectedCalenderItem(object):
    """Wrapper class around the selected scheduled item in the table view."""
    def __init__(
            self,
            schedule_manager,
            scheduled_item,
            orig_mouse_pos):
        """Initialise class.

        Args:
            schedule_manager (ScheduleManager): the calendar manager.
            scheduled_item (ScheduledItem): the currently selected scheduled item.
            orig_mouse_pos (QtCore.QPoint): mouse position that the selected
                item started at.
        """
        self._schedule_manager = schedule_manager
        self._scheduled_item = scheduled_item
        self.orig_mouse_pos = orig_mouse_pos
        self.orig_start_time = scheduled_item.start_time
        self.orig_end_time = scheduled_item.end_time
        self.orig_date = scheduled_item.date
        self.is_being_moved = False

    @property
    def start_time(self):
        """Get current start time of item.

        Returns:
            (Time): current start time.
        """
        return self._scheduled_item.start_time

    @property
    def end_time(self):
        """Get current end time of item.

        Returns:
            (Time): current end time.
        """
        return self._scheduled_item.end_time

    @property
    def date(self):
        """Get current end time of item.

        Returns:
            (Time): current end time.
        """
        return self._scheduled_item.date

    def change_time(self, new_start_datetime, new_end_datetime):
        """Change the time of the scheduled item.

        Args:
            new_start_time (DateTime): new start time for item.
            new_end_date_time (DateTime): new end time for item.
        """
        if not self.is_being_moved:
            self._schedule_manager.begin_move_item(self._scheduled_item)
            self.is_being_moved = True
        self._schedule_manager.update_move_item(
            self._scheduled_item,
            new_start_datetime.date(),
            new_start_datetime.time(),
            new_end_datetime.time(),
        )

    def deselect(self):
        """Call when we've finished using this item."""
        self._schedule_manager.end_move_item(self._scheduled_item)

    def get_item_to_modify(self):
        """Get the scheduled item to open with the scheduled item dialog.

        Returns:
            (BaseScheduledItem): either the scheduled item, or the repeat item
                that it's an instance of, in the case of repeat scheduled item
                instances.
        """
        return self._schedule_manager.get_item_to_modify(self._scheduled_item)


class CalendarView(BaseWeekTableView):
    """Calendar view widget."""
    DAY_START = Time(hour=0)
    DAY_END = Time(hour=23, minute=59, second=59)
    TIME_INTERVAL = TimeDelta(hours=1)
    SELECTION_TIME_STEP = TimeDelta(minutes=15)
    SELECTION_TIME_STEP_SECS = SELECTION_TIME_STEP.total_seconds()

    def __init__(
            self,
            name,
            project,
            parent=None):
        """Initialise calendar view.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(CalendarView, self).__init__(
            name,
            project,
            SchedulerWeekModel(project.calendar),
            parent=parent,
        )
        self.schedule_manager = project.get_schedule_manager()
        self.selection_rect = None

        self.setItemDelegate(CalendarDelegate(self))
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
        self.setDefaultDropAction(QtCore.Qt.DropAction.CopyAction)

        self.startTimer(constants.LONG_TIMER_INTERVAL)

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
    def column_width(self):
        """Get width of columns.

        Returns:
            (int): pixel width of columns.
        """
        return self.columnWidth(0)

    @property
    def row_height(self):
        """Get height of rows.

        Returns:
            (int): pixel height of rows.
        """
        return self.row_height(0)

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

    # TODO: make proper exception class for this func. Also maybe find more
    # efficient way to do this (eg. separate item attrs in CalendarDay?)
    def get_item_rects(self, background_only=False, foreground_only=False):
        """Get all qt rectangles to display for scheduled items.

        Args:
            background_only (bool): if True, only return background items.
            foreground_only (bool): if True, only return foreground items.

        Raises:
            (Exception): if both background_only and foreground_only are True.

        Yields:
            (QtCore.QRectF): rectangle for a given scheduled item.
            (ScheduledItem): the corresponding scheduled item.
        """
        if background_only and foreground_only:
            raise Exception(
                "Cannot call get_item_rects with both background_only "
                "and foreground_only flags set to True."
            )
        for i, calendar_day in enumerate(self.calendar_week.iter_days()):
            rect_x = self.columnViewportPosition(i)
            rect_width = self.columnWidth(i)
            for scheduled_item in calendar_day.iter_scheduled_items():
                if foreground_only and scheduled_item.is_background:
                    continue
                elif background_only and not scheduled_item.is_background:
                    continue
                time_start = scheduled_item.start_time
                time_end = scheduled_item.end_time
                rect_y = self.y_pos_from_time(time_start)
                rect_height = self.height_from_time_range(
                    time_end - time_start
                )
                rect = QtCore.QRectF(
                    rect_x,
                    rect_y,
                    rect_width,
                    rect_height
                )
                yield rect, scheduled_item

    def resize_table(self):
        """Resize table rows and columns to contents."""
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def resizeEvent(self, event):
        """Resize event, called when view is resized.

        Args:
            event (QtCore.QEvent): the resize event.
        """
        super(CalendarView, self).resizeEvent(event)
        self.resize_table()

    def timerEvent(self, event):
        """Called every timer_interval.

        This is used to repaint so that current time marker stays up to date.

        Args:
            event (QtCore.QEvent): the timer event.
        """
        self.viewport().update()

    def _paint_item(self, painter, rect, item, border_size, alpha, rounding):
        """Paint scheduled item.

        Args:
            painter (QtGui.QPainter): qt painter object.
            rect (QtCore.QRectF): rectangle to paint.
            item (ScheduledItem): scheduled item we're painting.
            border_size (int): size of border of items.
            alpha (int): alpha value for colours.
            rounding (int): amount of rounding for rects.
        """
        if item.type == ScheduledItemType.TASK:
            tree_item = item.tree_item
            if tree_item and tree_item.colour:
                brush_color = QtGui.QColor(*tree_item.colour, alpha)
            else:
                brush_color = QtGui.QColor(245, 245, 190, alpha)
        else:
            brush_color = QtGui.QColor(173, 216, 230, alpha)
        brush = QtGui.QBrush(brush_color)
        painter.setBrush(brush)

        path = QtGui.QPainterPath()
        rect.adjust(
            border_size/2, border_size/2, -border_size/2, -border_size/2
        )
        path.addRoundedRect(rect, rounding, rounding)
        painter.setClipPath(path)
        painter.fillPath(path, painter.brush())
        painter.strokePath(path, painter.pen())

        padding = 10
        text_height = 20
        category_text_rect = None
        time_text_rect = None
        # TODO: neaten this whole bit
        if rect.height() <= 2 * text_height + 3 * padding:
            name_text_rect = rect.adjusted(
                padding, 0, -padding, 0
            )
        elif (2 * text_height + 3 * padding <= rect.height() 
                and rect.height() < 3 * text_height + 5 * padding):
            name_text_rect = rect.adjusted(
                padding,
                padding,
                -padding,
                padding + text_height - rect.height(),
            )
            time_text_rect = rect.adjusted(
                padding,
                2 * padding + text_height,
                -padding, 
                2 * padding + 2 * text_height - rect.height()
            )
        else:
            category_text_rect = rect.adjusted(
                padding,
                padding,
                -padding,
                padding + text_height - rect.height()
            )
            name_text_rect = rect.adjusted(
                padding,
                2 * padding + text_height,
                -padding, 
                2 * padding + 2 * text_height - rect.height()
            )
            time_text_rect = rect.adjusted(
                padding,
                3 * padding + 2 * text_height,
                -padding,
                3 * padding + 3 * text_height - rect.height()
            )

        if category_text_rect:
            painter.drawText(
                category_text_rect,
                (
                    QtCore.Qt.AlignmentFlag.AlignLeft|
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                ),
                str(item.category)
            )
        painter.drawText(
            name_text_rect,
            (
                QtCore.Qt.AlignmentFlag.AlignLeft |
                QtCore.Qt.AlignmentFlag.AlignVCenter
            ),
            str(item.name)
        )
        if time_text_rect:
            painter.drawText(
                time_text_rect,
                (
                    QtCore.Qt.AlignmentFlag.AlignLeft |
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                ),
                "{0} - {1}".format(
                    item.start_time.string(),
                    item.end_time.string()
                )
            )

    def paintEvent(self, event):
        """Override paint event to draw item rects and selection rect.

        Args:
            event (QtCore.QEvent): the paint event.
        """
        super(CalendarView, self).paintEvent(event)

        # Create painter
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        border_size = 1
        pen = QtGui.QPen(QtGui.QColor(0,0,0), border_size)
        painter.setPen(pen)

        # Scheduled item background rects
        for rect, item in self.get_item_rects(background_only=True):
            self._paint_item(
                painter,
                rect,
                item,
                border_size,
                100,
                1,
            )

        # Scheduled item foreground rects
        for rect, item in self.get_item_rects(foreground_only=True):
            self._paint_item(
                painter,
                rect,
                item,
                border_size,
                255,
                5,
            )

        # Selection Rect
        if self.selection_rect:
            brush = QtGui.QBrush(QtGui.QColor(0, 255, 204))
            painter.setBrush(brush)

            path = QtGui.QPainterPath()
            x_start = self.columnViewportPosition(self.selection_rect.column)
            width = self.columnWidth(self.selection_rect.column)
            y_start = self.y_pos_from_time(self.selection_rect.start_time)
            height = self.height_from_time_range(
                self.selection_rect.time_range
            )
            rect = QtCore.QRectF(x_start, y_start, width, height)
            path.addRoundedRect(rect, 5, 5)
            painter.setClipPath(path)

            painter.fillPath(path, painter.brush())
            # painter.strokePath(path, painter.pen())

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
                painter.setBrush(QtGui.QBrush(QtGui.QColor(227, 36, 43)))
                painter.setClipPath(path)
                painter.fillPath(path, painter.brush())
                break

    def mousePressEvent(self, event):
        """Override mouse press event for interaction with scheduled items.

        Args:
            event (QtCore.QEvent): the mouse press event.
        """
        pos = event.pos()
        # item rects drawn last are the ones we should click first
        foreground_rects = list(self.get_item_rects(foreground_only=True))
        foreground_rects.reverse()
        background_rects = list(self.get_item_rects(background_only=True))
        background_rects.reverse()
        for rect, scheduled_item in foreground_rects + background_rects:
            if rect.contains(pos):
                self.selected_scheduled_item = SelectedCalenderItem(
                    self.schedule_manager,
                    scheduled_item,
                    pos
                )
                return

        mouse_col = self.column_from_mouse_pos(pos)
        if mouse_col is not None:
            date = self.date_from_column(mouse_col)
            y_pos = self.round_y_pos_to_time_step(event.pos().y())
            time_start = self.time_from_y_pos(y_pos)
            self.selection_rect = SelectionRect(
                mouse_col,
                date,
                time_start
            )
        return super(CalendarView, self).mousePressEvent(event)

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
            mouse_col = self.column_from_mouse_pos(event.pos())
            if mouse_col is not None:
                date = self.date_from_column(mouse_col)
            else:
                date = self.selected_scheduled_item.date
            y_pos = self.round_height_to_time_step(event.pos().y())
            y_pos_change = self.round_height_to_time_step(
                y_pos - self.selected_scheduled_item.orig_mouse_pos.y()
            )
            time_change = self.time_range_from_height(y_pos_change)
            orig_start = self.selected_scheduled_item.orig_start_time
            orig_end = self.selected_scheduled_item.orig_end_time
            if (self.DAY_END - orig_end <= time_change):
                time_change = self.DAY_END - orig_end
            elif (time_change <= self.DAY_START - orig_start):
                time_change = self.DAY_START - orig_start
            new_start_time = orig_start + time_change
            new_end_time = orig_end + time_change
            if (new_start_time != self.selected_scheduled_item.start_time
                    or date != self.selected_scheduled_item.date):
                self.selected_scheduled_item.is_moving = True
                self.selected_scheduled_item.change_time(
                    DateTime.from_date_and_time(date, new_start_time),
                    DateTime.from_date_and_time(date, new_end_time),
                )
                self.viewport().update()

        return super(CalendarView, self).mouseMoveEvent(event)

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
                )
                item_editor.exec()
            self.selection_rect = None
            self.viewport().update()

        elif self.selected_scheduled_item:
            if self.selected_scheduled_item.is_being_moved:
                # if being moved, deselect the item to finish continuous edit
                self.selected_scheduled_item.deselect()
            else:
                # otherwise, we want to open the editor
                item = self.selected_scheduled_item.get_item_to_modify()
                item_editor = ScheduledItemDialog(
                    self.tree_manager,
                    self.schedule_manager,
                    scheduled_item=item,
                )
                item_editor.exec()
            self.selected_scheduled_item = None
            self.viewport().update()

        return super(CalendarView, self).mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        """Override drag enter event for dragging task items.

        Args:
            event (QtCore.QEvent): the drag enter event.
        """
        if event.mimeData().hasFormat('application/vnd.treeviewdragdrop.list'):
            event.acceptProposedAction()
        super(CalendarView, self).dragMoveEvent(event)

    def dragMoveEvent(self, event):
        """Override drag move event for dragging task items.

        Args:
            event (QtCore.QEvent): the drag move event.
        """
        if event.mimeData().hasFormat('application/vnd.treeviewdragdrop.list'):
            event.acceptProposedAction()
        super(CalendarView, self).dragMoveEvent(event)

    def dropEvent(self, event):
        """Override drop event for dropping task items.

        Args:
            event (QtCore.QEvent): the drop event.
        """
        # TODO: if we use this same setup here as from tree model to decode mime data
        # should add as utils function or similar.
        encoded_data = event.mimeData().data('application/vnd.treeviewdragdrop.list')
        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.ReadOnly)

        if stream.atEnd():
            print ("early return")
            return

        while not stream.atEnd():
            byte_array = QtCore.QByteArray()
            stream >> byte_array
            encoded_path = bytes(byte_array).decode('utf-8')

        print (encoded_path)

        super(CalendarView, self).dropEvent(event)
        print ("DROPPED", event.mimeData().text())
        event.acceptProposedAction()


class CalendarDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for calendar."""

    def __init__(self, table, parent=None):
        """Initialise task delegate item."""
        super(CalendarDelegate, self).__init__(parent)
        self.table = table

    def sizeHint(self, option, index):
        """Get size hint for this item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item.

        Returns:
            (QtCore.QSize): size hint.
        """
        # TODO set num_rows as constant? and call it something more
        # explicit, like num_visible_rows or num_rows_on_screen
        num_rows = 12
        table_size = self.table.viewport().size()
        line_width = 1
        rows = self.table.row_count or 1
        cols = self.table.column_count or 1
        width = (table_size.width() - (line_width * (cols - 1))) / cols
        # TODO: why does the expression below use rows AND num_rows?
        height = (table_size.height() -  (line_width * (rows - 1))) / num_rows
        return QtCore.QSize(width, height)
