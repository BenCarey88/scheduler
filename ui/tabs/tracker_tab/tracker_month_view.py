"""Tracker month table view."""
# TODO: decide whether to change name of this module and class

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, DateTime, Time
from scheduler.api.edit.edit_callbacks import (
    CallbackEditType as CET,
    CallbackItemType as CIT,
)
from scheduler.api.enums import TimePeriod, TrackedValueType

from scheduler.ui.models.table import TrackerMonthModel
from scheduler.ui.tabs.base_calendar_view import (
    BaseMonthTableView,
    BaseTitledView,
)

from scheduler.ui import constants, utils


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
        self.tracker_manager = project.get_tracker_manager()
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

    def paintEvent(self, event):
        """Override paint event to draw item rects and selection rect.

        Args:
            event (QtCore.QEvent): the paint event.
        """
        super(TrackerMonthTableView, self).paintEvent(event)

        # Create painter
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # fill squares
        # rect_width = self.columnWidth(0)
        # rect_height = self.rowHeight(0)
        # zipped_weeks = enumerate(zip(self.full_weeks, self.weeks))
        # for row, (full_week, week) in zipped_weeks:
        #     for date in full_week.dates:
        #         column = (date.weekday() - self.weekday_start) % 7
        #         x_pos = self.columnViewportPosition(column)
        #         y_pos = self.rowViewportPosition(row)
        #         rect = QtCore.QRectF(
        #             x_pos,
        #             y_pos,
        #             rect_width,
        #             rect_height,
        #         )
        #         background_brush = QtGui.QBrush(colors.BG_STANDARD)
        #         foreground_brush = None
        #         add_date_text = True
        #         steps = -1
        #         skipped = self.step_tracker.date_is_skipped(date)
        #         extended = self.step_tracker.get_extension_at_date(date)

        #         # Get colour and rect data
        #         if date not in week.dates:
        #             background_brush = QtGui.QBrush(colors.BG_OUT_OF_MONTH)
        #             add_date_text = False
        #             skipped = False
        #             extended = None

        #         elif (not skipped
        #                 and date >= self.step_tracker.start_date
        #                 and date <= datetime.date.today()):
        #             steps = self.step_tracker.steps_by_target_time(date)
        #             success = self.step_tracker.check_date(date)
        #             if success:
        #                 foreground_brush = QtGui.QBrush(colors.FG_TARGET_MET)
        #             datetime_lim = datetime.datetime.combine(
        #                 datetime.date.today(),
        #                 self.step_tracker.upper_time_limit(date),
        #             )
        #             if (not success and
        #                     (date != datetime.date.today() or
        #                     datetime.datetime.now() >= datetime_lim)):
        #                 foreground_brush = QtGui.QBrush(colors.FG_TARGET_UNMET)

        #         # draw and fill rectangles
        #         pen = QtGui.QPen(colors.GRID_LINES, 1)
        #         painter.setPen(pen)
        #         path = QtGui.QPainterPath()
        #         path.addRect(rect)
        #         painter.drawPath(path)

        #         if background_brush is not None:
        #             painter.setBrush(background_brush)
        #             painter.fillPath(path, painter.brush())

        #         if foreground_brush is not None and steps >= 0:
        #             foreground_rect = QtCore.QRectF(
        #                 x_pos + self.RECT_X_PADDING,
        #                 y_pos + self.RECT_Y_PADDING,
        #                 rect_width - 2 * self.RECT_X_PADDING,
        #                 rect_height - 2 * self.RECT_Y_PADDING,
        #             )
        #             curvature = self.RECT_CURVATURE
        #             path = QtGui.QPainterPath()
        #             path.addRoundedRect(foreground_rect, curvature, curvature)
        #             painter.setBrush(foreground_brush)
        #             painter.fillPath(path, painter.brush())

        #         # date text
        #         if add_date_text:
        #             text_padding = 10
        #             text_height = 11
        #             text_alignment = (
        #                 QtCore.Qt.AlignmentFlag.AlignRight |
        #                 QtCore.Qt.AlignmentFlag.AlignTop
        #             )
        #             font = painter.font()
        #             font.setPointSize(text_height)
        #             font.setBold(True)
        #             painter.setFont(font)
        #             pen = QtGui.QPen(colors.TXT_DATE, text_height)
        #             painter.setPen(pen)
        #             date_rect = QtCore.QRect(
        #                 int(rect.left()) + text_padding,
        #                 int(rect.top()) + text_padding,
        #                 int(rect.width()) - 2 * text_padding,
        #                 text_height * 2,
        #             )
        #             text_alignment = (
        #                 QtCore.Qt.AlignmentFlag.AlignRight |
        #                 QtCore.Qt.AlignmentFlag.AlignTop
        #             )
        #             painter.drawText(
        #                 date_rect,
        #                 text_alignment,
        #                 str(date.day),
        #             )

        #         # variables for steps and extension text
        #         if skipped or steps >= 0 or extended:
        #             text_padding = 10
        #             text_height = 10
        #             text_alignment = (
        #                 QtCore.Qt.AlignmentFlag.AlignHCenter |
        #                 QtCore.Qt.AlignmentFlag.AlignTop
        #             )

        #         # steps text
        #         if skipped or steps >= 0:
        #             color = (
        #                 colors.TXT_SKIPPED if skipped
        #                 else colors.TXT_STEPS
        #             )
        #             font = painter.font()
        #             font.setPointSize(text_height)
        #             font.setBold(True)
        #             pen = QtGui.QPen(color, text_height)
        #             painter.setFont(font)
        #             painter.setPen(pen)
        #             steps_rect = QtCore.QRect(
        #                 int(rect.left()) + text_padding,
        #                 int(rect.bottom()) - 3 * text_height - text_padding,
        #                 int(rect.width()) - 2 * text_padding,
        #                 text_height * 3,
        #             )
        #             text = "[skipped]" if skipped else "{0} Steps".format(
        #                 self.step_tracker.steps_by_target_time(date)
        #             )
        #             painter.drawText(
        #                 steps_rect,
        #                 text_alignment,
        #                 text,
        #             )

        #         # extended text
        #         if steps >= 0 and extended:
        #             time_rect = QtCore.QRect(
        #                 int(rect.left()) + text_padding,
        #                 int(rect.bottom()) - 5 * text_height - text_padding,
        #                 int(rect.width()) - 2 * text_padding,
        #                 text_height * 3,
        #             )
        #             font.setPointSize(9)
        #             color = (
        #                 colors.TXT_SKIPPED if skipped
        #                 else colors.TXT_EXTENDED if extended > 0
        #                 else colors.TXT_REDUCED
        #             )
        #             pen = QtGui.QPen(color, 9)
        #             painter.setPen(pen)
        #             painter.setFont(font)

        #             # time_text = self.step_tracker.upper_time_limit(
        #             #     date,
        #             #     as_string=True,
        #             # )
        #             # ext = self.step_tracker.get_extension_at_date(date)
        #             time_text = "[extended]" if extended > 0 else "[reduced]"
        #             painter.drawText(
        #                 time_rect,
        #                 text_alignment,
        #                 time_text,
        #             )
        # painter.end()


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
        rect = QtCore.QRectF(
            x_pos,
            y_pos,
            rect_width,
            rect_height,
        )
        # TODO: get date from index internalPointer once we've improved model
        date = self.table.model().day_from_row_and_column(row, column).date
        value = None
        target = None
        if task_item is not None:
            value = task_item.get_value_at_date(date)
            target = task_item.get_target_at_date(date)

        # paint backgrounds
        if (target is not None
                and target.time_period == TimePeriod.DAY
                and target.is_met_by(value)):
            path = QtGui.QPainterPath()
            path.addRect(rect)
            painter.fillPath(
                path,
                QtGui.QBrush(constants.TRACKING_TARGET_MET_COLOR),
            )

        # add text
        date_text_alignment = (
            QtCore.Qt.AlignmentFlag.AlignTop |
            QtCore.Qt.AlignmentFlag.AlignLeft
        )
        value_text_alignment = (
            QtCore.Qt.AlignmentFlag.AlignHCenter |
            QtCore.Qt.AlignmentFlag.AlignBottom
        )
        value_str = str(value) if value is not None else ""
        painter.drawText(rect, date_text_alignment, str(date.day))
        painter.drawText(rect, value_text_alignment, value_str)

