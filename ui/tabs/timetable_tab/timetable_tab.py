"""Timetable Tab."""

# general TODO (should hopefully cover several of the to-dos below):
#   - switch times here to all use datetime (or my util class wrapper around datetime)
#   - create all the conversion functions between that and the screen position values
#   - maybe even make separate Converter class to do this? or break into separate file?

import datetime
import math

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task

from scheduler.ui.tabs.base_tab import BaseTab
from scheduler.ui import utils

from .add_event_dialog import AddEventDialog
from .timetable_model import TimetableModel


# this and the below should be part of the API
class TimetableEvent(object):
    def __init__(self, date, start_time, end_time):
        self.date = date
        self.start_time = min(start_time, end_time)
        self.end_time = max(start_time, end_time)
        self.category = None
        self.name = None
        self.tree_item = None
        self.category_item = None

    # TODO: this shit is getting super hacky, all needs to be fixed up
    # when we make proper API classes. The +2 here is because our timetable
    # starts from sunday but datetime.datetime.weekday() starts from mon
    @property
    def column(self):
        return (self.date.weekday() + 2) % 7

    def set_date(self, date):
        self.date = date

    def move_column(self, new_column):
        day_change = new_column - self.column
        self.date += datetime.timedelta(days=day_change)

    def set_tree_item(self, tree_item):
        self.tree_item = tree_item
        if self.tree_item:
            self.name = tree_item.name
            parent = tree_item.parent
            self.category = parent.name
            while isinstance(parent, Task):
                self.category_item = parent
                self.category = parent.name
                parent = parent.parent
            # so 'category' is actually the top level task - this is due
            # to my dodgy namings and should change in a refactor

    def set_category(self, category):
        self.category = category

    def set_name(self, name):
        self.name = name

    def set_time(self, start, end):
        self.start_time = start
        self.end_time = end

    def change_time(self, new_start, new_end):
        self.start_time = new_start
        self.end_time = new_end


class TimetableDayData(object):
    def __init__(self, date):
        self.date = date
        self.events = []

    def add_event(self, event):
        self.events.append(event)


class TimetableTab(BaseTab):
    """Timetable tab."""

    def __init__(self, tree_root, tree_manager, outliner, parent=None):
        """Setup timetable main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner widget.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TimetableTab, self).__init__(
            tree_root,
            tree_manager,
            outliner,
            parent=parent
        )
        self.table = TimetableView(tree_root, tree_manager)
        self.outer_layout.addWidget(self.table)

    def update(self):
        pass


class TimetableView(QtWidgets.QTableView):
    """Timetable view widget."""

    # repeat of attrs from model (find way to share this info)
    WEEKDAYS = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
    DAY_START = 6
    DAY_END = 24
    TIME_INTERVAL = 1
    SELCECTION_TIME_STEP = 0.25

    def __init__(self, tree_root, tree_manager, parent=None):
        """Initialise task delegate item."""
        super(TimetableView, self).__init__(parent)

        self.tree_root = tree_root
        self.tree_manager = tree_manager
        self.selected_rect = None

        # TODO: store these on TimetableEvent? may need wrapper from api class
        self.selected_timetable_event = None
        self.selected_timetable_event_is_moving = False
        self.selected_timetable_event_orig_mouse_pos = None
        self.selected_timetable_event_orig_start = None
        self.selected_timetable_event_orig_end = None

        # test_events = [
        #     [(8, 9), (10.5, 11)],
        #     [(13, 20), (19, 20.5)],
        #     [(14.25, 15.25)],
        #     [],
        #     [(8, 9), (10.5, 11)],
        #     [(13, 14.5)],
        #     [(14.25, 15.25)],
        # ]
        # TODO: time should be datetime too, rather than float
        date = datetime.datetime(2021, 12, 11)

        # bad name, should be something like self.day_data
        self.timetable_events = []
        for i, day in enumerate(self.WEEKDAYS):
            day_data = TimetableDayData(date)
            date += datetime.timedelta(days=1)
            # for event in test_events[i]:
            #     day_data.add_event(event[0], event[1], "test", "test")
            self.timetable_events.append(day_data)

        model = TimetableModel(self)
        self.setModel(model)
        self.setItemDelegate(TimetableDelegate(self))
        #self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.resize_table()
        utils.set_style(self, "timetable.qss")

        #self.setSelectionMode(self.SelectionMode.ContiguousSelection)

    @property
    def table_top(self):
        return self.rowViewportPosition(0)
        
    @property
    def table_bottom(self):
        return (
            self.rowViewportPosition(self.row_count() - 1) +
            self.rowHeight(self.row_count() - 1)
        )

    @property
    def table_left(self):
        return self.columnViewportPosition(0)

    @property
    def table_right(self):
        return (
            self.columnViewportPosition(self.column_count() - 1) +
            self.columnWidth(self.column_count() - 1)
        )

    @property
    def table_height(self):
        return self.table_bottom - self.table_top

    @property
    def time_range(self):
        return self.DAY_END - self.DAY_START

    def height_from_time_range(self, time_range):
        return time_range * self.table_height / self.time_range

    def pos_from_time(self, time):
        return (
            self.table_top + self.height_from_time_range(time - self.DAY_START)
        )

    def time_range_from_height(self, height):
        return height * self.time_range / self.table_height

    def time_from_pos(self, pos):
        return (
            self.DAY_START + self.time_range_from_height(pos - self.table_top)
        )

    def resize_table(self):
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def resizeEvent(self, event):
        super(TimetableView, self).resizeEvent(event)
        self.resize_table()

    def column_width(self):
        return self.columnWidth(0)

    def row_height(self):
        return self.row_height(0)

    def row_count(self):
        return self.model().rowCount(QtCore.QModelIndex())

    def column_count(self):
        return self.model().columnCount(QtCore.QModelIndex())

    def get_event_rects(self):
        for i, _ in enumerate(self.WEEKDAYS):
            rect_x = self.columnViewportPosition(i)
            rect_width = self.columnWidth(i)
            day_data = self.timetable_events[i]
            for timetable_event in day_data.events:
                time_start = timetable_event.start_time
                time_end = timetable_event.end_time
                rect_y = self.pos_from_time(time_start)
                rect_height = self.height_from_time_range(
                    time_end - time_start
                )
                rect = QtCore.QRectF(
                    rect_x,
                    rect_y,
                    rect_width,
                    rect_height
                )
                yield rect, timetable_event

    def paintEvent(self, event):
        super(TimetableView, self).paintEvent(event)

        # Create the painter
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        #set the pen
        border_size = 1
        pen = QtGui.QPen(QtGui.QColor(0,0,0), border_size)
        painter.setPen(pen)

        for rect, event in self.get_event_rects():
            brush = QtGui.QBrush(QtGui.QColor(173, 216, 230))
            painter.setBrush(brush)
            # Create the path
            path = QtGui.QPainterPath()
            rect.adjust(
                border_size/2, border_size/2, -border_size/2, -border_size/2
            )
            # Add the rect to path.
            path.addRoundedRect(rect, 5, 5)
            painter.setClipPath(path)

            # Fill shape, draw the border and center the text.
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
                    str(event.category)
                )
            painter.drawText(
                name_text_rect,
                (
                    QtCore.Qt.AlignmentFlag.AlignLeft |
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                ),
                str(event.name)
            )
            if time_text_rect:
                painter.drawText(
                    time_text_rect,
                    (
                        QtCore.Qt.AlignmentFlag.AlignLeft |
                        QtCore.Qt.AlignmentFlag.AlignVCenter
                    ),
                    "{0} - {1}".format(
                        self.model().convert_to_time(event.start_time),
                        self.model().convert_to_time(event.end_time)
                    )
                )

        if self.selected_rect:
            brush = QtGui.QBrush(QtGui.QColor(0, 255, 204))
            painter.setBrush(brush)
            # Create the path
            path = QtGui.QPainterPath()

            rect = QtCore.QRectF(
                self.selected_rect[0],
                self.selected_rect[1],
                self.selected_rect[2],
                self.selected_rect[3],
            )
            path.addRoundedRect(rect, 5, 5)
            painter.setClipPath(path)

            # Fill shape, draw the border and center the text.
            painter.fillPath(path, painter.brush())
            # painter.strokePath(path, painter.pen())

    # TODO: don't call pos in these functions pos as it's just a float
    def round_pos_to_time_step(self, y_pos):
        time = self.time_from_pos(y_pos)
        scaled_time = (time - self.DAY_START) / self.SELCECTION_TIME_STEP
        rounded_time = (
            round(scaled_time) * self.SELCECTION_TIME_STEP + self.DAY_START
        )
        return self.pos_from_time(rounded_time)

    def round_height_to_time_step(self, height):
        time_range = self.time_range_from_height(height)
        scaled_time_range = time_range / self.SELCECTION_TIME_STEP
        rounded_time_range = round(scaled_time_range) * self.SELCECTION_TIME_STEP
        return self.height_from_time_range(rounded_time_range)

    def get_column_from_mouse_pos(self, pos):
        if (self.table_left < pos.x() < self.table_right
                and self.table_top < pos.y() < self.table_bottom):
            day = 0
            for i, _ in enumerate(self.WEEKDAYS):
                if pos.x() < self.columnViewportPosition(i):
                    break
                day = i
            return day
        return None

    def mousePressEvent(self, event):
        pos = event.pos()
        for rect, timetable_event in self.get_event_rects():
            if rect.contains(pos):
                self.selected_timetable_event = timetable_event
                self.selected_timetable_event_orig_mouse_pos = pos
                self.selected_timetable_event_orig_start = (
                    timetable_event.start_time
                )
                self.selected_timetable_event_orig_end = (
                    timetable_event.end_time
                )
                #  QtCore.QPoint(
                #     pos.x(), self.round_pos_to_time_step(pos.y())
                # )
                return

        day = self.get_column_from_mouse_pos(pos)
        if day is not None:
            col_start = self.columnViewportPosition(day)
            col_width = self.columnWidth(day)
            # TODO make struct for selection rect
            self.selected_rect = [0, 0, 0, 0, 0, 0]
            self.selected_rect[0] = col_start
            self.selected_rect[1] = self.round_pos_to_time_step(pos.y())
            self.selected_rect[2] = col_width
            self.selected_rect[4] = day
            self.selected_rect[5] = self.timetable_events[day].date
        return super(TimetableView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):

        update_view_port = False
        if self.selected_rect:
            y_pos = self.round_pos_to_time_step(event.pos().y())
            self.selected_rect[3] = y_pos - self.selected_rect[1]
            update_view_port = True

        elif self.selected_timetable_event:
            y_pos = event.pos().y()
            y_pos_change = self.round_height_to_time_step(
                y_pos - self.selected_timetable_event_orig_mouse_pos.y()
            )
            if y_pos_change != 0:
                time_change = self.time_range_from_height(y_pos_change)
                new_start = (
                    self.selected_timetable_event_orig_start + time_change
                )
                new_end = (
                    self.selected_timetable_event_orig_end + time_change
                )
                if new_start != self.selected_timetable_event.start_time:
                    self.selected_timetable_event_is_moving = True
                    self.selected_timetable_event.change_time(
                        new_start,
                        new_end
                    )
                update_view_port = True

            x_pos = event.pos().x()
            x_pos_change = (
                x_pos - self.selected_timetable_event_orig_mouse_pos.x()
            )
            mouse_col = self.get_column_from_mouse_pos(event.pos())
            event_col = self.selected_timetable_event.column
            if mouse_col is not None and mouse_col != event_col:
                self.selected_timetable_event_is_moving = True
                self.selected_timetable_event.move_column(mouse_col)
                self.timetable_events[event_col].events.remove(
                    self.selected_timetable_event
                )
                self.timetable_events[mouse_col].events.append(
                    self.selected_timetable_event
                )
                update_view_port = True

        if update_view_port:
            self.viewport().update()
        return super(TimetableView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.selected_rect:
            y_top = self.selected_rect[1]
            height = self.selected_rect[3]
            if height != 0:
                day = self.selected_rect[4]
                new_event = TimetableEvent(
                    self.selected_rect[5],
                    self.time_from_pos(y_top),
                    self.time_from_pos(y_top + height)
                )
                event_editor = AddEventDialog(
                    self.tree_root,
                    self.tree_manager,
                    self.timetable_events[day],
                    new_event
                )
                if event_editor.exec():
                    self.timetable_events[day].add_event(
                        event_editor.timetable_event
                    )
            self.selected_rect = None
            self.viewport().update()
        elif self.selected_timetable_event:
            if not self.selected_timetable_event_is_moving:
                event_editor = AddEventDialog(
                    self.tree_root,
                    self.tree_manager,
                    self.timetable_events[
                        self.selected_timetable_event.column
                    ],
                    self.selected_timetable_event,
                    as_editor=True,
                )
                event_editor.exec()
            self.selected_timetable_event = None
            self.selected_timetable_event_is_moving = False
            self.selected_timetable_event_orig_mouse_pos = None
            self.viewport().update()
        return super(TimetableView, self).mouseReleaseEvent(event)


class TimetableDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for timetable."""

    # repeat of attrs from model (find way to share this info)
    WEEKDAYS = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
    DAY_START = 6
    DAY_END = 24
    TIME_INTERVAL = 1

    def __init__(self, table, parent=None):
        """Initialise task delegate item."""
        super(TimetableDelegate, self).__init__(parent)
        self.table = table

    def sizeHint(self, option, index):
        """Get size hint for this item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item.

        Returns:
            (QtCore.QSize): size hint.
        """
        num_rows = 12
        table_size = self.table.viewport().size()
        line_width = 1
        rows = self.table.row_count() or 1
        cols = self.table.column_count() or 1
        width = (table_size.width() - (line_width * (cols - 1))) / cols
        height = (table_size.height() -  (line_width * (rows - 1))) / num_rows
        return QtCore.QSize(width, height)

    # def createEditor(self, parent, option, index):
    #     """Create editor widget for edit role.

    #     Args:
    #         parent (QtWidgets.QWidget): parent widget.
    #         option (QtWidgets.QStyleOptionViewItem): style options object.
    #         index (QtCore.QModelIndex) index of the edited item.

    #     Returns:
    #         (QtWidgets.QWidget): editor widget.
    #     """
    #     return super().createEditor(parent, option, index)

    # TODO:
    # I think probably we don't want to override this paint method - see:
    # https://stackoverflow.com/questions/21528972/qtableview-selected-cell-messes-up-painting
    # may be better to override paintEvent in TableView class.
    # then we can still keep the model with the same number of rows for gridline formatting
    # and to be used when clicking on a cell, but the event data is actually added directly
    # to the table paintevent so it can straddle multiple cells
    # def paint(self, painter, option, index):
    #     """Paint item.

    #     Args:
    #         painter (QtGui.QPainter): painter object.
    #         option (QtGui.QStyleOptioneViewItem): options object.
    #         index (QtCore.QModelIndex): index of item we're painting.
    #     """
    #     if not index.isValid():
    #         return
    #     item = index.internalPointer()
    #     if not item:
    #         return

    #     painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    #     painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200), 1))

    #     # illustrating the concept that the best way to organise this is
    #     # probably just a table model with 7 columns of one row each,
    #     # then add in lines to separate each time
    #     # will then probably need an ItemDelegate for the row header
    #     # as well
    #     time_range = self.DAY_END - self.DAY_START
    #     num_lines = int(time_range / self.TIME_INTERVAL)
    #     column_range = option.rect.bottom() - option.rect.top()
    #     for line_num in range(num_lines):
    #         fraction = line_num / num_lines
    #         y_value = option.rect.top() + fraction * column_range
    #         painter.drawLine(
    #             option.rect.left(),
    #             y_value,
    #             option.rect.right(),
    #             y_value,
    #         )

    #     for event in item.events:
    #         border_size = 1
    #         pen = QtGui.QPen(QtGui.QColor(0, 0, 0), border_size)
    #         painter.setPen(pen)
    #         brush = QtGui.QBrush(QtGui.QColor(173, 216, 230))
    #         painter.setBrush(brush)
    #         # Create the path
    #         path = QtGui.QPainterPath()

    #         event_start = event[0]
    #         event_end = event[1]
    #         rect_top = (
    #             (event_start - self.DAY_START) / time_range * column_range
    #         )
    #         rect_bottom = (
    #             (event_end - self.DAY_START) / time_range * column_range
    #         )
    #         rect = QtCore.QRectF(
    #             option.rect.left(),
    #             rect_top,
    #             option.rect.right() - option.rect.left(),
    #             rect_bottom - rect_top,
    #         )

    #         # Slighly shrink dimensions to account for bordersize.
    #         rect.adjust(
    #             border_size/2, border_size/2, -border_size/2, -border_size/2
    #         )

    #         # Add the rect to path.
    #         path.addRoundedRect(rect, 10, 10)
    #         painter.setClipPath(path)

    #         # Fill shape, draw the border and center the text.
    #         painter.fillPath(path, painter.brush())
    #         painter.strokePath(path, painter.pen())

    #     return super().paint(painter, option, index)
