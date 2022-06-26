"""Classes defining the drawing of items in scheduler tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import DateTime
from scheduler.api.utils import fallback_value
from scheduler.ui import constants


class ScheduledItemWidget(object):
    """Class representing a scheduled item widget."""
    def __init__(
            self,
            timetable_view,
            schedule_manager,
            scheduled_item):
            #orig_mouse_pos):
        """Initialize widget.

        Args:
            timetable_view (SchedulerTimetableView): timetable view this is
                part of.
            schedule_manager (ScheduleManager): the scheduler manager.
            scheduled_item (ScheduledItem): the scheduled item.
            orig_mouse_pos (QtCore.QPoint): mouse position that the selected
                item started at.
        """
        self._timetable_view = timetable_view
        self._schedule_manager = schedule_manager
        self._scheduled_item = scheduled_item
        #self.orig_mouse_pos = orig_mouse_pos
        self.is_being_moved = False
        self.mouse_pos_start_time = None
        self._edited_date = None
        self._edited_start_time = None
        self._edited_end_time = None
        self.update_orig_datetime_attrs()

    def update_orig_datetime_attrs(self):
        """Update orig start and end times."""
        self.orig_start_time = self._scheduled_item.start_time
        self.orig_end_time = self._scheduled_item.end_time
        self.orig_date = self._scheduled_item.date

    @property
    def scheduled_item(self):
        """Get scheduled item this object represents.

        Returns:
            (BaseScheduledItem): the scheduled item.
        """
        return self._scheduled_item

    @property
    def start_time(self):
        """Get current start time of item.

        Returns:
            (Time): current start time.
        """
        return fallback_value(
            self._edited_start_time,
            self._scheduled_item.start_time,
        )

    @property
    def end_time(self):
        """Get current end time of item.

        Returns:
            (Time): current end time.
        """
        return fallback_value(
            self._edited_end_time,
            self._scheduled_item.end_time,
        )

    @property
    def date(self):
        """Get current end time of item.

        Returns:
            (Time): current end time.
        """
        return fallback_value(
            self._edited_date,
            self._scheduled_item.date,
        )

    @property
    def rect(self):
        """Get rectangle that represents item in timetable view.

        Returns:
            (QtCore.QRectF): the rectangle representing this item.
        """
        return self._timetable_view.rect_from_date_time_range(
            self.date,
            self.start_time,
            self.end_time,
        )

    def contains(self, pos):
        """Check if widget contains position.

        Args:
            pos (QtCore.QPos): position to check.

        Returns:
            (bool): whether or not widget contains pos.
        """
        return self.rect.contains(pos)

    def set_mouse_pos_start_time(self, start_time):
        """When moving the item, set the start time based on the mouse pos.

        Args:
            start_time (DateTime): the time represented by the mouse position.
        """
        self.mouse_pos_start_time = start_time

    def change_time(self, new_start_datetime, new_end_datetime):
        """Change the time of the scheduled item.

        Args:
            new_start_time (DateTime): new start time for item.
            new_end_date_time (DateTime): new end time for item.
        """
        # if not self.is_being_moved:
        #     self._schedule_manager.begin_move_item(self._scheduled_item)
        #     self.is_being_moved = True
        # self._schedule_manager.update_move_item(
        #     self._scheduled_item,
        #     new_start_datetime.date(),
        #     new_start_datetime.time(),
        #     new_end_datetime.time(),
        # )
        if not self.is_being_moved:
            self.is_being_moved = True
        self._edited_date = new_start_datetime.date()
        self._edited_start_time = new_start_datetime.time()
        self._edited_end_time = new_end_datetime.time()

    def deselect(self):
        """Call when we've finished using this item."""
        # self._schedule_manager.end_move_item(self._scheduled_item)
        # self.update_orig_datetime_attrs()
        self._schedule_manager.move_scheduled_item(
            self._scheduled_item,
            self._edited_date,
            self._edited_start_time,
            self._edited_end_time,
        )
        self._edited_date = None
        self._edited_start_time = None
        self._edited_end_time = None
        self.mouse_pos_start_time = None
        self.is_being_moved = False
        self.update_orig_datetime_attrs()

    def get_item_to_modify(self):
        """Get the scheduled item to open with the scheduled item dialog.

        Returns:
            (BaseScheduledItem): either the scheduled item, or the repeat item
                that it's an instance of, in the case of repeat scheduled item
                instances.
        """
        return self._schedule_manager.get_item_to_modify(self._scheduled_item)

    def paint(self, painter):
        """Paint the item to the table view.

        Args:
            painter (QtGui.QPainter): qt painter object.
        """
        rect = self.rect
        border_size = 1
        rounding = 1
        alpha = 100 if self._scheduled_item.is_background else 200

        if self._schedule_manager.has_task_type(self._scheduled_item):
            tree_item = self._scheduled_item.tree_item
            if tree_item and tree_item.color:
                brush_color = QtGui.QColor(*tree_item.color)
            else:
                brush_color = constants.BASE_SCHEDULED_TASK_COLOR
        else:
            brush_color = constants.BASE_SCHEDULED_EVENT_COLOR
        brush_color.setAlpha(alpha)
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

        # if self._scheduled_item.is_background:
        #     return
        text_padding = 3
        text_margin = min(rect.width() / 2, 7)
        text_height = 20
        text_alignment = (
            QtCore.Qt.AlignmentFlag.AlignLeft |
            QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        category_text = str(self._scheduled_item.category)
        name_text = str(self._scheduled_item.name)
        time_text = "{0} - {1}".format(
            self._scheduled_item.start_time.string(),
            self._scheduled_item.end_time.string()
        )

        text_range = rect.height() - 2 * text_margin
        total_text_height = text_height
        num_text_rects = 0
        for i in range(1, 4 if category_text else 3):
            if total_text_height >= text_range:
                break
            num_text_rects = i
            total_text_height += text_height + text_padding
        for i in range(num_text_rects):
            text_rect = QtCore.QRect(
                rect.left() + text_margin,
                rect.top() + text_margin + text_height * i + text_padding * i,
                rect.width() - text_margin * 2,
                text_height,
            )
            if num_text_rects == 3:
                text = [category_text, name_text, time_text][i]
            else:
                text = [name_text, time_text][i]
            painter.drawText(text_rect, text_alignment, text)
        if not num_text_rects:
            text_rect = QtCore.QRect(
                rect.left() + text_padding,
                rect.top(),
                rect.width() - text_padding * 2,
                rect.height(),
            )
            painter.drawText(text_rect, text_alignment, name_text)


class SelectionRect(object):
    """Widget representing a selection in the day/week timetable."""
    def __init__(self, timetable_view, date, time):
        """Initialize widget.

        Args:
            +timetable_view (SchedulerTimetableView): timetable view this is
                part of.
            date (Date): the date of the selection rect.
            time (Time): the time at the the start of the selection creation.
        """
        self._timetable_view = timetable_view
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

    @property
    def rect(self):
        """Get rectangle that represents item in timetable view.

        Returns:
            (QtCore.QRectF): the rectangle representing this item.
        """
        return self._timetable_view.rect_from_date_time_range(
            self.date,
            self.start_time,
            self.end_time,
        )

    def paint(self, painter):
        """Paint the selection rect to the table view.

        Args:
            painter (QtGui.QPainter): qt painter object.
        """
        brush = QtGui.QBrush(constants.SCHEDULER_SELECTION_RECT_COLOR)
        painter.setBrush(brush)
        path = QtGui.QPainterPath()
        path.addRoundedRect(self.rect, 5, 5)
        painter.setClipPath(path)
        painter.fillPath(path, painter.brush())
