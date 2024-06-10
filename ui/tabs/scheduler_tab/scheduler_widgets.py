"""Classes defining the drawing of items in scheduler tab."""

from tabnanny import check
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import DateTime
from scheduler.api.enums import ItemStatus
from scheduler.api.utils import fallback_value
from scheduler.ui import constants, utils


class ScheduledItemWidget(object):
    """Class representing a scheduled item widget."""
    BOUNDARY_BUFFER = 5

    def __init__(
            self,
            timetable_view,
            schedule_manager,
            scheduled_item):
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
        self.is_being_moved = False
        self.is_being_resized_top = False
        self.is_being_resized_bottom = False
        self.delete_pressed = False
        self.checkbox_pressed = False
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

    @property
    def checkbox_rect(self):
        """Get checkbox rectangle.

        Returns:
            (QtCore.QRectF or None): the rectangle for this item's checkbox,
                if exists.
        """
        is_task = self._schedule_manager.has_task_type(
            self._scheduled_item,
            strict=True,
        )
        if not is_task: # or self._scheduled_item.is_background:
            return None
        max_buffer = 3
        min_buffer = 1
        buffer = max_buffer
        max_size = 15
        rect = self.rect
        size = min(rect.height() - 2*buffer, max_size)
        if size < max_size:
            buffer = min_buffer
            size = min(rect.height() - 2*buffer, max_size)
        if size > 0:
            return QtCore.QRectF(
                rect.right() - size - buffer,
                rect.bottom() - size - buffer,
                size,
                size,
            )
        return None

    @property
    def delete_button_rect(self):
        """Get delete button rectangle.

        Returns:
            (QtCore.QRectF): the rectangle for this item's delete button.
        """
        max_buffer = 3
        min_buffer = 1
        buffer = max_buffer
        max_size = 15
        rect = self.rect
        size = min(rect.height() - 2*buffer, max_size)
        if size < max_size:
            buffer = min_buffer
            size = min(rect.height() - 2*buffer, max_size)
        if size > 0:
            # if can't fit over top of checkbox, put to the left
            if 2 * size + 2 * buffer > rect.height():
                return QtCore.QRectF(
                    rect.right() - 2*size - 2*buffer,
                    rect.bottom() - size - buffer,
                    size,
                    size,
                )
            else:
                return QtCore.QRectF(
                    rect.right() - size - buffer,
                    rect.top() + buffer,
                    size,
                    size,
                )
        return None

    @property
    def checkbox_status(self):
        """Get checkbox status of scheduled item.

        Returns:
            (QtWidgets.QStyle or None): checkbox status, if exists.
        """
        is_task = self._schedule_manager.has_task_type(
            self._scheduled_item,
            strict=True,
        )
        if not is_task: # or self._scheduled_item.is_background:
            return None
        return {
            ItemStatus.UNSTARTED: QtWidgets.QStyle.State_Off,
            ItemStatus.IN_PROGRESS: QtWidgets.QStyle.State_NoChange,
            ItemStatus.COMPLETE: QtWidgets.QStyle.State_On,
        }.get(self._scheduled_item.status, None)

    @property
    def display_buttons(self):
        """Property determining whether or not we should display buttons.

        Returns:
            (bool): whether or not we should display buttons.
        """
        return self._timetable_view.display_widget_buttons

    def contains(self, pos):
        """Check if widget contains position.

        Args:
            pos (QtCore.QPos): position to check.

        Returns:
            (bool): whether or not widget contains pos.
        """
        return self.rect.contains(pos)

    def over_checkbox(self, pos):
        """Check if position is over checkbox rect.

        Args:
            pos (QtCore.QPos): position to check.

        Returns:
            (bool): whether or not checkbox rect contains pos.
        """
        checkbox_rect = self.checkbox_rect
        if checkbox_rect:
            return checkbox_rect.contains(pos)
        return False

    def over_delete_button(self, pos):
        """Check if position is over delete button rect.

        Args:
            pos (QtCore.QPos): position to check.

        Returns:
            (bool): whether or not delete button rect contains pos.
        """
        delete_button_rect = self.delete_button_rect
        if delete_button_rect:
            return delete_button_rect.contains(pos)
        return False

    def at_top(self, pos):
        """Check if mouse pos is at top of widget.

        Args:
            pos (QtCore.QPos): position to check.

        Returns:
            (bool): whether or not mouse pos is at top of widget.
        """
        rect = self.rect
        return (
            abs(rect.top() - pos.y()) < self.BOUNDARY_BUFFER
            and rect.left() <= pos.x() <= rect.right()
        )

    def at_bottom(self, pos):
        """Check if mouse pos is at bottom of widget.

        Args:
            pos (QtCore.QPos): position to check.

        Returns:
            (bool): whether or not mouse pos is at bottom of widget.
        """
        rect = self.rect
        return (
            abs(rect.bottom() - pos.y()) < self.BOUNDARY_BUFFER
            and rect.left() <= pos.x() <= rect.right()
        )

    def set_mouse_pos_start_time(self, start_time):
        """When moving the item, set the start time based on the mouse pos.

        Args:
            start_time (DateTime): the time represented by the mouse position.
        """
        self.mouse_pos_start_time = start_time

    def apply_time_change(self, time_change, date=None):
        """Apply time change from user to widget.

        Args:
            time_change (TimeDelta): time change to apply, calculated from
                mouse movement in the view.
            date (Date): date to change to, if needed.

        Returns:
            (bool): true if any change was actually applied.
        """
        self.is_being_moved = (
            not self.is_being_resized_bottom
            and not self.is_being_resized_top
        )
        orig_start = self.orig_start_time
        orig_end = self.orig_end_time

        if self.is_being_moved:
            if (time_change <= self._timetable_view.DAY_START - orig_start):
                time_change = self._timetable_view.DAY_START - orig_start
            if (self._timetable_view.DAY_END - orig_end <= time_change):
                time_change = self._timetable_view.DAY_END - orig_end
            new_start_time = orig_start + time_change
            new_end_time = orig_end + time_change
            new_date = date or self.orig_date

        elif self.is_being_resized_top:
            if (time_change <= self._timetable_view.DAY_START - orig_start):
                time_change = self._timetable_view.DAY_START - orig_start
            if (self._timetable_view.DAY_END - orig_start <= time_change):
                time_change = self._timetable_view.DAY_END - orig_start
            new_start_time = min(orig_start + time_change, orig_end)
            new_end_time = max(orig_start + time_change, orig_end)
            new_date = self.orig_date

        elif self.is_being_resized_bottom:
            if (self._timetable_view.DAY_END - orig_end <= time_change):
                time_change = self._timetable_view.DAY_END - orig_end
            if (time_change <= self._timetable_view.DAY_START - orig_end):
                time_change = self._timetable_view.DAY_START - orig_end
            new_start_time = min(orig_end + time_change, orig_start)
            new_end_time = max(orig_end + time_change, orig_start)
            new_date = self.orig_date

        if (new_start_time != self.start_time
                or new_end_time != self.end_time
                or date != self.date):
            self._edited_start_time = new_start_time
            self._edited_end_time = new_end_time
            self._edited_date = new_date
            return True
        return False

    def deselect(self):
        """Call when we've finished editing this item."""
        self._schedule_manager.move_scheduled_item(
            self._scheduled_item,
            date=self._edited_date,
            start_time=self._edited_start_time,
            end_time=self._edited_end_time,
        )
        self._edited_date = None
        self._edited_start_time = None
        self._edited_end_time = None
        self.mouse_pos_start_time = None
        self.is_being_moved = False
        self.is_being_resized_top = False
        self.is_being_resized_bottom = False
        self.update_orig_datetime_attrs()

    def delete(self, force=False):
        """Delete scheduled item.

        Args:
            force (bool): if True, don't prompt user confirmation.
        """
        # TODO: for repeat scheduled items, this should give option
        # to delete either instance or repeat item.
        continue_deletion = force or utils.simple_message_dialog(
            "Delete Scheduled Item?",
            parent=self._timetable_view,
        )
        if continue_deletion:
            # TODO: make this apply to _scheduled_item rather than item
            # to modify, as this deletion should apply to item instance?
            # BUT: the edit doesn't currently work for them
            self._schedule_manager.remove_scheduled_item(
                self.get_item_to_modify(),
            )

    def toggle_checkbox(self):
        """Toggle checkbox."""
        self._schedule_manager.update_check_status(self._scheduled_item)

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
        border_size = 1
        rounding = 1
        alpha = 100 if self._scheduled_item.is_background else 200

        # setup brush
        if self._schedule_manager.has_task_type(self._scheduled_item):
            tree_item = self._scheduled_item.tree_item
            if tree_item and tree_item.color:
                brush_color = QtGui.QColor(*tree_item.color)
            else:
                brush_color = QtGui.QColor(constants.BASE_SCHEDULED_TASK_COLOR)
        else:
            brush_color = QtGui.QColor(constants.BASE_SCHEDULED_EVENT_COLOR)
        brush_color.setAlpha(alpha)
        brush = QtGui.QBrush(brush_color)
        painter.setBrush(brush)

        # setup path and fill rects
        path = QtGui.QPainterPath()
        rect = self.rect.adjusted(
            border_size/2, border_size/2, -border_size/2, -border_size/2
        )
        path.addRoundedRect(rect, rounding, rounding)
        painter.setClipPath(path)
        painter.fillPath(path, painter.brush())
        painter.strokePath(path, painter.pen())

        # setup text
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
            self.start_time.string(),
            self.end_time.string(),
        )

        # draw text rects
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

        if not self.display_buttons:
            return

        # draw delete button
        dbr = self.delete_button_rect
        if dbr:
            buffer = 3
            dbr.adjust(buffer, buffer, -buffer, -buffer)
            painter.drawLine(
                QtCore.QPointF(dbr.left(), dbr.top()),
                QtCore.QPointF(dbr.right(), dbr.bottom()),
            )
            painter.drawLine(
                QtCore.QPointF(dbr.right(), dbr.top()),
                QtCore.QPointF(dbr.left(), dbr.bottom()),
            )

        # draw checkbox rect
        cr = self.checkbox_rect
        if cr:
            cr.adjust(
                border_size/2, border_size/2, -border_size/2, -border_size/2
            )
            path = QtGui.QPainterPath()
            path.addRoundedRect(cr, rounding, rounding)
            painter.setClipPath(path)
            fill_color = constants.WHITE
            fill_color.setAlpha(150)
            painter.fillPath(path, QtGui.QBrush(fill_color))
            painter.strokePath(path, painter.pen())

            pen = QtGui.QPen(constants.BLACK, 1)
            painter.setPen(pen)
            checkbox_status = self.checkbox_status
            if checkbox_status == QtWidgets.QStyle.State_NoChange:
                # draw line
                line_left = QtCore.QPointF(
                    cr.left() + cr.width() / 8,
                    cr.top() + cr.width() / 8,
                )
                line_right = QtCore.QPointF(
                    cr.right() - cr.width() / 8,
                    cr.bottom() - cr.width() / 8,
                )
                painter.drawLine(line_left, line_right)
            elif checkbox_status == QtWidgets.QStyle.State_On:
                # draw tick
                tick_left = QtCore.QPointF(
                    cr.left() + cr.width() / 5,
                    cr.bottom() - cr.height() / 3,
                )
                tick_bottom = QtCore.QPointF(
                    cr.left() + cr.width() / 2,
                    cr.bottom() - cr.height() / 8,
                )
                tick_right = QtCore.QPointF(
                    cr.right() - cr.width() / 8,
                    cr.top() + cr.height() / 8,
                )
                painter.drawLine(tick_left, tick_bottom)
                painter.drawLine(tick_bottom, tick_right)


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
