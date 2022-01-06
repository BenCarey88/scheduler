"""Calendar Tab."""

# general TODO (should hopefully cover several of the to-dos below):
#   - switch times here to all use datetime (or my util class wrapper around datetime)
#   - create all the conversion functions between that and the screen position values
#   - maybe even make separate Converter class to do this? or break into separate file?

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, DateTime, Time, TimeDelta
from scheduler.api.edit.calendar_edit import ModifyCalendarItem
from scheduler.api.timetable.calendar_item import (
    CalendarItem,
    CalendarItemType
)
from scheduler.api.timetable.calendar_period import CalendarWeek
from scheduler.api.tree.task import Task

from scheduler.ui.tabs.base_tab import BaseTab
from scheduler.ui import constants, utils

from .calendar_item_dialog import CalendarItemDialog
from .calendar_model import CalendarModel


class CalendarTab(BaseTab):
    """Calendar tab."""

    # repeat of attrs from the view (find way to share this info)
    WEEK_START_DAY = Date.SAT

    def __init__(
            self,
            tree_root,
            tree_manager,
            outliner,
            calendar,
            parent=None):
        """Setup calendar main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner widget.
            calendar (Calendar): calendar item.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(CalendarTab, self).__init__(
            tree_root,
            tree_manager,
            outliner,
            parent=parent
        )
        utils.set_style(self, "calendar.qss")
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

        self.table = CalendarView(
            tree_root,
            tree_manager,
            calendar,
            self.calendar_week
        )
        self.outer_layout.addWidget(self.table)

        prev_week_button.clicked.connect(self.change_to_prev_week)
        next_week_button.clicked.connect(self.change_to_next_week)

    def update(self):
        """Update widget."""
        self.table.viewport().update()

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
    """Wrapper class around the selected calendar item in the table view."""
    def __init__(
            self,
            calendar,
            calendar_item,
            orig_mouse_pos):
        """Initialise class.

        Args:
            calendar (Calendar): the calendar.
            calendar_item (CalendarItem): the currently selected calendar item.
            orig_mouse_pos (QtCore.QPoint): mouse position that the selected
                item started at.
        """
        self.calendar_item = calendar_item
        self.orig_mouse_pos = orig_mouse_pos
        self.orig_start_time = calendar_item.start_time
        self.orig_end_time = calendar_item.end_time
        self.orig_date = calendar_item.date
        self.edit = ModifyCalendarItem(
            calendar,
            calendar_item
        )
        self.is_being_moved = False

    @property
    def start_time(self):
        """Get current start time of item.

        Returns:
            (Time): current start time.
        """
        return self.calendar_item.start_time

    @property
    def end_time(self):
        """Get current end time of item.

        Returns:
            (Time): current end time.
        """
        return self.calendar_item.end_time

    @property
    def date(self):
        """Get current end time of item.

        Returns:
            (Time): current end time.
        """
        return self.calendar_item.date

    def change_time(self, new_start_datetime, new_end_datetime):
        """Change the time of the calendar item.

        Args:
            new_start_time (DateTime): new start time for item.
            new_end_date_time (DateTime): new end time for item.
        """
        if not self.is_being_moved:
            self.edit.begin_continuous_run()
            self.is_being_moved = True
        self.edit.update_continuous_run(new_start_datetime, new_end_datetime)

    def deselect(self):
        """Call when we've finished using this item."""
        self.edit.end_continuous_run()


class CalendarView(QtWidgets.QTableView):
    """Calendar view widget."""

    # repeat of attrs from model (find way to share this info)
    WEEK_START_DAY = Date.SAT
    DAY_START = Time(hour=6)
    DAY_END = Time(hour=23, minute=59, second=59)
    TIME_INTERVAL = TimeDelta(hours=1)
    SELECTION_TIME_STEP = TimeDelta(minutes=15)
    SELECTION_TIME_STEP_SECS = SELECTION_TIME_STEP.total_seconds()

    def __init__(
            self,
            tree_root,
            tree_manager,
            calendar,
            calendar_week,
            parent=None):
        """Initialise calendar view."""
        super(CalendarView, self).__init__(parent)

        self.tree_root = tree_root
        self.tree_manager = tree_manager
        self.calendar = calendar
        self.calendar_week = calendar_week

        self.selection_rect = None
        self.selected_calendar_item = None

        model = CalendarModel(self.calendar_week, self)
        self.setModel(model)
        self.setItemDelegate(CalendarDelegate(self))
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.resize_table()
        self.startTimer(constants.LONG_TIMER_INTERVAL)

    def set_to_week(self, week):
        """Set view to use given week.

        Args:
            week (CalendarWeek): the calendar week to use.
        """
        self.calendar_week = week
        model = CalendarModel(week, self)
        self.setModel(model)
        self.viewport().update()

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

    def get_item_rects(self):
        """Get all qt rectangles to display for calendar items.

        Yields:
            (QtCore.QRectF): rectangle for a given calendar item.
            (CalendarItem): the corresponding calendar item.
        """
        for i, calendar_day in enumerate(self.calendar_week.iter_days()):
            rect_x = self.columnViewportPosition(i)
            rect_width = self.columnWidth(i)
            for calendar_item in calendar_day.iter_calendar_items():
                time_start = calendar_item.start_time
                time_end = calendar_item.end_time
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
                yield rect, calendar_item

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

        # Calendar Item Rects
        for rect, item in self.get_item_rects():
            if item.type == CalendarItemType.TASK:
                brush_color = QtGui.QColor(245, 245, 190)
            else:
                brush_color = QtGui.QColor(173, 216, 230)
            brush = QtGui.QBrush(brush_color)
            painter.setBrush(brush)

            path = QtGui.QPainterPath()
            rect.adjust(
                border_size/2, border_size/2, -border_size/2, -border_size/2
            )
            path.addRoundedRect(rect, 5, 5)
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
        """Override mouse press event for interaction with calendar items.

        Args:
            event (QtCore.QEvent): the mouse press event.
        """
        pos = event.pos()
        # item rects since drawn last are the ones we should click first
        for rect, calendar_item in reversed(list(self.get_item_rects())):
            if rect.contains(pos):
                self.selected_calendar_item = SelectedCalenderItem(
                    self.calendar,
                    calendar_item,
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
        """Override mouse move event for interaction with calendar items.

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

        elif self.selected_calendar_item:
            mouse_col = self.column_from_mouse_pos(event.pos())
            if mouse_col is not None:
                date = self.date_from_column(mouse_col)
            else:
                date = self.selected_calendar_item.date
            y_pos = self.round_height_to_time_step(event.pos().y())
            y_pos_change = self.round_height_to_time_step(
                y_pos - self.selected_calendar_item.orig_mouse_pos.y()
            )
            time_change = self.time_range_from_height(y_pos_change)
            orig_start = self.selected_calendar_item.orig_start_time
            orig_end = self.selected_calendar_item.orig_end_time
            if (self.DAY_END - orig_end < time_change):
                time_change = self.DAY_END - orig_end
            # TODO this bit isn't working:
            elif (orig_start - self.DAY_START < time_change):
                time_change = orig_start - self.DAY_START
            new_start_time = orig_start + time_change
            new_end_time = orig_end + time_change
            if (new_start_time != self.selected_calendar_item.start_time
                    or date != self.selected_calendar_item.date):
                self.selected_calendar_item.is_moving = True
                self.selected_calendar_item.change_time(
                    DateTime.from_date_and_time(date, new_start_time),
                    DateTime.from_date_and_time(date, new_end_time),
                )
                self.viewport().update()

        return super(CalendarView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Override mouse release event for interaction with calendar items.

        Args:
            event (QtCore.QEvent): the mouse release event.
        """
        if self.selection_rect:
            if self.selection_rect.time_range.total_seconds() != 0:
                new_calendar_item = CalendarItem(
                    self.calendar,
                    self.selection_rect.start_datetime,
                    self.selection_rect.end_datetime,
                )
                item_editor = CalendarItemDialog(
                    self.tree_root,
                    self.tree_manager,
                    self.calendar,
                    new_calendar_item,
                )
                item_editor.exec()
            self.selection_rect = None
            self.viewport().update()

        elif self.selected_calendar_item:
            if self.selected_calendar_item.is_being_moved:
                # if being moved, deselect the item to finish continuous edit
                self.selected_calendar_item.deselect()
            else:
                # otherwise, we want to open the editor
                item_editor = CalendarItemDialog(
                    self.tree_root,
                    self.tree_manager,
                    self.calendar,
                    self.selected_calendar_item.calendar_item,
                    as_editor=True,
                )
                item_editor.exec()
            self.selected_calendar_item = None
            self.viewport().update()

        return super(CalendarView, self).mouseReleaseEvent(event)


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
