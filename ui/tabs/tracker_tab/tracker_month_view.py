"""Tracker month table view."""
# TODO: decide whether to change name of this module and class

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date
from scheduler.api.edit.edit_callbacks import (
    CallbackEditType as CET,
    CallbackItemType as CIT,
)
from scheduler.api.enums import ItemStatus, TimePeriod, TrackedValueType as TVT
from scheduler.api.tracker import TargetOperator as TO

from scheduler.ui.models.table import TrackerMonthModel
from scheduler.ui.tabs.base_calendar_view import (
    BaseMonthTableView,
    BaseTitledView,
)

from scheduler.ui import constants


# constants for widgets
RECT_PADDING = 5
TEXT_PADDING = 10
RECT_CURVATURE = 5


class TitledTrackerMonthTableView(BaseTitledView):
    """Tracker month table view with title."""
    def __init__(self, name, project, weekday_start=0, parent=None):
        """Initialise tracker month table view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            weekday_start (int or str): week starting day, ie. day that
                the leftmost column should represent.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        self.tracker_table_view = TrackerMonthTableView(
            name,
            project,
            weekday_start,
        )
        super(TitledTrackerMonthTableView, self).__init__(
            name,
            project,
            self.tracker_table_view,
            parent=parent,
        )

    def get_title(self, calendar_period):
        """Get title - reimplemented from base class.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to get title
                for - unused in this case.

        Returns:
            (str): title.
        """
        tree_item = self.filter_manager.get_current_tree_item()
        if tree_item is not None:
            return tree_item.get_display_name()
        return "No Tree Item"
    
    def on_outliner_current_changed(self, tree_item):
        """Callback for what to do when active tree item is changed.

        Args:
            tree_item (BaseTaskItem): new item selected in outliner.
        """
        self.title.setText(self.get_title(self.calendar_period))
        super(TitledTrackerMonthTableView, self).on_outliner_current_changed(
            tree_item
        )


class TrackerMonthTableView(BaseMonthTableView):
    """Tracker month table view."""
    def __init__(self, name, project, weekday_start=0, parent=None):
        """Initialise tracker month table view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            weekday_start (int or str): week starting day, ie. day that
                the leftmost column should represent.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TrackerMonthTableView, self).__init__(
            name,
            project,
            TrackerMonthModel(project.calendar, weekday_start=weekday_start),
            parent=parent,
        )
        self.weekday_start = weekday_start
        self.tracker_manager = project.get_tracker_manager()
        self.pass_fail_mode = True
        # utils.set_style(self, "tracker_view.qss")
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.verticalHeader().hide()
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.active_tree_item = self.filter_manager.get_current_tree_item()
        self.setItemDelegate(
            TrackerMonthDelegate(
                self,
                self.tracker_manager,
                self.tree_manager,
                self.filter_manager,
            )
        )

    def on_view_changed(self):
        """Callback for when this view is loaded."""
        super(TrackerMonthTableView, self).on_view_changed()
        self.model().beginResetModel()
        self.model().endResetModel()
        self.update()

    def on_outliner_filter_changed(self, *args):
        """Callback for what to do when filter is changed in outliner."""
        super(TrackerMonthTableView, self).on_outliner_filter_changed(*args)
        self.model().beginResetModel()
        self.model().endResetModel()
        self.update()

    def on_outliner_current_changed(self, tree_item):
        """Callback to change active tree item.

        Args:
            tree_item (BaseTaskItem): new item selected in outliner.
        """
        super(TrackerMonthTableView, self).on_outliner_current_changed(
            tree_item,
        )
        self.active_tree_item = self.filter_manager.get_current_tree_item()
        self.viewport().update()

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(TrackerMonthTableView, self).pre_edit_callback(
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
        super(TrackerMonthTableView, self).post_edit_callback(
            callback_type,
            *args,
        )
        if (self._is_active
                and callback_type[0] == CIT.TREE
                and callback_type[1] in [CET.MODIFY, CET.ADD, CET.REMOVE]):
            self.model().endResetModel()
            self.update()

    def get_position_from_date(self, date):
        """Get position on screen representing start of given date.

        Args:
            date (Date): the date.

        Returns:
            (QPoint): the position.
        """
        column = (date.weekday - self.weekday_start) % 7
        if date < self.calendar_month.start_date:
            row = 0
        else:
            start_col = (
                self.calendar_month.start_date.weekday - self.weekday_start
            ) % 7
            if date > self.calendar_month.end_date:
                # for dates after month end, get row from end_date
                date = self.calendar_month.end_date
            row = (date.day - 1) // 7
            if column < start_col:
                row += 1
        x_pos = int(self.columnViewportPosition(column))
        y_pos = int(self.rowViewportPosition(row))
        return QtCore.QPoint(x_pos, y_pos)

    def paintEvent(self, event):
        """Override paint event to draw item rects and selection rect.

        Args:
            event (QtCore.QEvent): the paint event.
        """
        super(TrackerMonthTableView, self).paintEvent(event)
        task = self.active_tree_item
        if task is None or not self.tree_manager.is_task(task):
            return

        # Create painter
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # fill squares
        for week in self.calendar_month.iter_weeks(
                starting_day=self.weekday_start, overspill=True):
            date = week.start_date
            if date > Date.now():
                continue
            end_date = week.end_date
            target = task.get_target_at_date(date)
            if target is None or target.time_period != TimePeriod.WEEK:
                continue
            if not target.is_met_by_task_from_date(task, date):
                if end_date > Date.now() or not self.pass_fail_mode:
                    continue
                rect_color = QtGui.QColor(
                    constants.TRACKING_TARGET_FAILED_COLOR
                )
            else:
                rect_color = QtGui.QColor(
                    constants.TRACKING_TARGET_MET_COLOR
                )
            start_pos = self.get_position_from_date(date)
            full_week_rect = QtCore.QRectF(
                start_pos.x() + RECT_PADDING,
                start_pos.y() + RECT_PADDING,
                7 * self.columnWidth(0) - 3 * RECT_PADDING,
                self.rowHeight(0) - 2 * RECT_PADDING,
            )
            path = QtGui.QPainterPath()
            rect_color.setAlpha(100)
            path.addRoundedRect(full_week_rect, RECT_CURVATURE, RECT_CURVATURE)
            painter.fillPath(path, QtGui.QBrush(rect_color))

        painter.end()

    def keyPressEvent(self, event):
        """Event called when key is pressed.
        
        Args:
            event (QtCore.QEvent): the key event.
        """
        if event.key() == QtCore.Qt.Key.Key_P:
            self.pass_fail_mode = not self.pass_fail_mode
            self.viewport().update()
        return super().keyPressEvent(event)


class TrackerMonthDelegate(QtWidgets.QStyledItemDelegate):
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
        super(TrackerMonthDelegate, self).__init__(parent)
        self.table = table
        self.tracker_manager = tracker_manager
        self.tracker = tracker_manager.tracker
        self.tree_manager = tree_manager
        self.filter_manager = filter_manager

    @property
    def calendar_month(self):
        """Get calendar week.

        Implemented as a property to stay up to date  with parent class.

        Returns:
            (CalendarWeek): calendar week
        """
        return self.table.calendar_month

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

    def paint(self, painter, option, index):
        """Paint item.
        
        Args:
            painter (QPainter): painter object.
            option (QStyleOptionViewItem): item options.
            index (QModelIndex): index of item we're painting.
        """
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        task_item = self.filter_manager.get_current_tree_item()
        column = index.column()
        row = index.row()
        rect_width = self.table.columnWidth(column)
        rect_height = self.table.rowHeight(row)
        x_pos = self.table.columnViewportPosition(column)
        y_pos = self.table.rowViewportPosition(row)
        # TODO: get date from index internalPointer once we've improved model
        date = self.table.model().day_from_row_and_column(row, column).date
        value = None
        target = None
        if task_item is not None and self.tree_manager.is_task(task_item):
            value = task_item.get_value_at_date(date)
            status = task_item.get_status_at_date(date)
            target = task_item.get_target_at_date(date)

        # work out whether to paint foreground and background
        paint_rect_fg = False
        paint_rect_bg = False
        fg_rect_color = constants.TRACKING_TARGET_MET_COLOR
        bg_rect_color = constants.DATE_OUT_OF_MONTH_COLOR

        if not self.calendar_month.contains(date):
            paint_rect_bg = True

        elif target is not None and date <= Date.now():
            if target.time_period == TimePeriod.DAY:
                target_met = target.is_met_by_value(value)
                if date == Date.now():
                    paint_rect_fg = target_met
                else:
                    paint_rect_fg = target_met or not self.table.pass_fail_mode
                if not target_met:
                    fg_rect_color = constants.TRACKING_TARGET_FAILED_COLOR

            elif target.time_period == TimePeriod.WEEK:
                if target.value_type == TVT.COMPLETIONS:
                    paint_rect_fg = (status == ItemStatus.COMPLETE)
                elif target.value_type in (TVT.INT, TVT.FLOAT):
                    paint_rect_fg = {
                        TO.LESS_THAN_EQ: (value > 0),
                        TO.GREATER_THAN_EQ: (value < target.target_value / 7)
                    }.get(target.target_operator, False)

        # paint background
        if paint_rect_bg:
            rect = QtCore.QRectF(x_pos, y_pos, rect_width, rect_height)
            path = QtGui.QPainterPath()
            path.addRect(rect)
            painter.fillPath(path, QtGui.QBrush(bg_rect_color))

        # paint foreground
        if paint_rect_fg:
            rect = QtCore.QRectF(
                x_pos + RECT_PADDING,
                y_pos + RECT_PADDING,
                rect_width - 2 * RECT_PADDING,
                rect_height - 2 * RECT_PADDING,
            )
            path = QtGui.QPainterPath()
            path.addRoundedRect(rect, RECT_CURVATURE, RECT_CURVATURE)
            painter.fillPath(path, QtGui.QBrush(fg_rect_color))

        # add text
        text_rect = QtCore.QRectF(
            x_pos + TEXT_PADDING,
            y_pos + TEXT_PADDING,
            rect_width - 2 * TEXT_PADDING,
            rect_height - 3 * TEXT_PADDING,
        )
        date_text_alignment = (
            QtCore.Qt.AlignmentFlag.AlignTop |
            QtCore.Qt.AlignmentFlag.AlignLeft
        )
        value_text_alignment = (
            QtCore.Qt.AlignmentFlag.AlignHCenter |
            QtCore.Qt.AlignmentFlag.AlignBottom
        )
        value_str = str(value) if value is not None else ""
        non_bold_font = QtGui.QFont()
        bold_font = QtGui.QFont()
        bold_font.setBold(True)
        painter.setFont(non_bold_font)
        painter.drawText(text_rect, date_text_alignment, str(date.day))
        painter.setFont(bold_font)
        painter.drawText(text_rect, value_text_alignment, value_str)
