"""Hybrid planner views."""

from operator import contains
from PyQt5 import QtWidgets, QtCore, QtGui

from scheduler.api.constants import TimePeriod
from scheduler.ui import constants
from scheduler.ui.tabs.base_calendar_view import (
    BaseHybridView,
    BaseOverlayedView,
)
from scheduler.ui.tabs.scheduler_tab.scheduler_timetable_view import (
    SchedulerTimetableView,
)
from .planner_list_view import TitledPlannerListView
from .planner_multi_list_view import (
    PlannerMultiListWeekView,
    PlannerMultiListMonthView,
    PlannerMultiListYearView,
)


class PlannerHybridView(BaseHybridView):
    """Hybrid list and multilist/timetable view for planner."""
    def __init__(self, name, project, time_period, num_days=7, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            time_period (TimePeriod): time period type of view.
            num_days (int): length of week. Defaults to 7.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        self.time_period = time_period
        nd = num_days

        # left view
        if time_period == TimePeriod.WEEK and nd != 7:
            left_view = PlannerMultiListWeekView(name, project, num_days=nd)
        else:
            left_view = TitledPlannerListView(name, project, time_period)

        # right view
        if time_period == TimePeriod.DAY:
            right_view = SchedulerTimetableView(name, project, num_days=1)
        elif time_period == TimePeriod.WEEK and nd != 7:
            right_view = SchedulerTimetableView(name, project, num_days=nd)
        elif time_period == TimePeriod.WEEK:
            right_view = PlannerMultiListWeekView(name, project)
        elif time_period == TimePeriod.MONTH:
            right_view = PlannerMultiListMonthView(name, project)
        elif time_period == TimePeriod.YEAR:
            right_view = PlannerMultiListYearView(name, project)
        else:
            raise NotImplementedError(
                "Time period {0} not supported for hybrid views".format(
                    time_period
                )
            )

        super(PlannerHybridView, self).__init__(
            name,
            project,
            left_view,
            right_view,
            parent=parent,
        )


class OverlayedPlannerHybridView(BaseOverlayedView):
    """Hybrid view for planner with overlay for custom drawing."""
    LINE_BUFFER = 20
    RECT_MAX_BUFFER_L = 10
    RECT_MAX_BUFFER_R = 10

    def __init__(self, name, project, time_period, num_days=7, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            time_period (TimePeriod): time period type of view.
            num_days (int): length of week. Defaults to 7.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        self.hybrid_view = PlannerHybridView(
            name,
            project,
            time_period,
            num_days=num_days,
            parent=parent,
        )
        self.hide_day_change_buttons = (time_period == TimePeriod.WEEK)
        self.display_connections_on_hover = False
        self.display_all_connections = False
        self.time_period = time_period
        super(OverlayedPlannerHybridView, self).__init__(
            name,
            project,
            self.hybrid_view,
            parent=parent,
        )
        self.planner_manager = project.get_planner_manager(name)
        self.left_view = self.hybrid_view.left_view
        self.right_view = self.hybrid_view.right_view

        # get views and mouse tracking defaults
        self.mouse_track_defaults = {}
        self.list_view = None
        self.left_multilist_view = None
        self.right_multilist_view = None
        self.timetable_view = None
        if time_period == TimePeriod.WEEK and num_days != 7:
            self.left_multilist_view = self.left_view
            for subview in self.left_multilist_view.iter_widgets():
                self.mouse_track_defaults[subview] = subview.hasMouseTracking()
        else:
            self.list_view = self.left_view.planner_list_view
            self.mouse_track_defaults[self.list_view] = (
                self.list_view.hasMouseTracking()
            )
        if (time_period == TimePeriod.DAY or
                time_period == TimePeriod.WEEK and num_days != 7):
            self.timetable_view = self.right_view
            self.mouse_track_defaults[self.timetable_view] = (
                self.timetable_view.hasMouseTracking()
            )
        else:
            self.right_multilist_view = self.right_view
            for subview in self.right_multilist_view.iter_widgets():
                self.mouse_track_defaults[subview] = subview.hasMouseTracking()

        self.hovered_parent_item = None
        self.hovered_child_item = None
        self.set_connections_displayed_on_hover(True)
        self.left_view.HOVERED_ITEM_SIGNAL.connect(
            self.set_hovered_parent_item
        )
        self.left_view.HOVERED_ITEM_REMOVED_SIGNAL.connect(
            self.set_hovered_parent_item
        )
        self.right_view.HOVERED_ITEM_SIGNAL.connect(
            self.set_hovered_child_item
        )
        self.right_view.HOVERED_ITEM_REMOVED_SIGNAL.connect(
            self.set_hovered_child_item
        )
        self.connections_timer_id = None

    def set_connections_displayed_on_hover(self, value):
        """Enable or disable mouse tracking for subviews.

        Args:
            value (bool): whether to enable or disable.
        """
        self.display_connections_on_hover = value
        def get_value(widget):
            return value or self.mouse_track_defaults.get(widget, False)

        if self.list_view is not None:
            self.list_view.setMouseTracking(get_value(self.list_view))
        elif self.left_multilist_view is not None:
            for subview in self.left_multilist_view.iter_widgets():
                subview.planner_list_view.setMouseTracking(get_value(subview))

        if self.right_multilist_view is not None:
            for subview in self.right_multilist_view.iter_widgets():
                subview.planner_list_view.setMouseTracking(get_value(subview))
        elif self.timetable_view is not None:
            self.timetable_view.setMouseTracking(
                get_value(self.timetable_view)
            )

    def set_hovered_parent_item(self, planned_item=None):
        """Set hovered parent item to given value.

        Args:
            planned_item (PlannedItem or None): new value for parent.
        """
        self.hovered_parent_item = planned_item
        self.update()

    def set_hovered_child_item(self, item=None):
        """Set hovered child item to given value.

        Args:
            item (PlannedItem, ScheduledItem or None): new value for child.
        """
        self.hovered_child_item = item
        self.update()

    def get_parent_rect(self, planned_item):
        """Get rectangle representing a planned item in the parent view.

        Args:
            planned_item (PlannedItem): the parent planned item.

        Returns:
            (QtCore.QRectF or None): the rectangle of the item in coordinates
                relative to this widget, if found.
        """
        if self.list_view is not None:
            return self.list_view.get_rect_for_item(
                planned_item,
                self,
                stop_at_text_end=True,
                x_max=(self.list_view.rect().right() + self.RECT_MAX_BUFFER_L)
            )
        elif self.left_multilist_view is not None:
            titled_list_view = self.left_multilist_view.get_subview(
                planned_item.calendar_period
            )
            if titled_list_view is not None:
                list_view = titled_list_view.planner_list_view
                if list_view is not None:
                    return list_view.get_rect_for_item(
                        planned_item,
                        self,
                        stop_at_text_end=True,
                        x_max=(
                            list_view.rect().right() + self.RECT_MAX_BUFFER_L
                        ),
                    )

    def get_child_rect(self, item):
        """Get rectangle representing an item in the child view.

        Args:
            item (PlannedItem or BaseScheduledItem): the child item - either
                a planned item in a multilist view, or a scheduled item in
                a timetable view.

        Returns:
            (QtCore.QRectF or None): the rectangle of the item in coordinates
                relative to this widget, if found.
        """
        if self.right_multilist_view is not None:
            titled_list_view = self.right_multilist_view.get_subview(
                item.calendar_period
            )
            if titled_list_view is not None:
                list_view = titled_list_view.planner_list_view
                if list_view is not None:
                    if self.list_view is not None:
                        left_view_end = self.list_view.rect().width()
                    else:
                        # approximate for now, cba to get it from subview
                        left_view_end = self.left_view.rect().width()
                    x_max=(
                        left_view_end
                        + self.right_multilist_view.rect().right()
                        - self.RECT_MAX_BUFFER_R
                    )
                    return list_view.get_rect_for_item(
                        item,
                        self,
                        stop_at_text_end=True,
                        x_max=x_max,
                    )
        elif self.timetable_view is not None:
            for item_widget in self.timetable_view.scheduled_item_widgets:
                if item == item_widget.scheduled_item:
                    rect = item_widget.rect
                    view = self.timetable_view.viewport()
                    top_left = view.mapTo(self, rect.topLeft().toPoint())
                    bottom_right = view.mapTo(
                        self,
                        rect.bottomRight().toPoint()
                    )
                    return QtCore.QRectF(top_left, bottom_right)
        return None

    def paint_child_connections(
            self,
            painter,
            planned_item,
            connected_only=False):
        """Paint child connections for item.

        Args:
            painter (QtGui.QPainter): the overlay painter.
            planned_item (PlannedItem): the item to paint connections for.
            connected_only (bool): if True, only paint items that have
                connections.
        """
        parent_rect = self.get_parent_rect(planned_item)
        if parent_rect is None:
            return
        if self.timetable_view is not None:
            child_list = planned_item.scheduled_items
        else:
            child_list = planned_item.planned_children
        if not connected_only or child_list:
            path = QtGui.QPainterPath()
            path.addRect(parent_rect)
            painter.fillPath(path, painter.brush())

        for child_item in child_list:
            child_rect = self.get_child_rect(child_item)
            if child_rect is None:
                continue
            path = QtGui.QPainterPath()
            path.addRect(child_rect)
            painter.fillPath(path, painter.brush())
            line_start = (parent_rect.right(), parent_rect.center().y())
            line_end = (child_rect.left(), child_rect.center().y())
            painter.drawLine(*line_start, *line_end)

    def paint_parent_connections(
            self,
            painter,
            item,
            connected_only=False):
        """Paint parent connections for item.

        Args:
            painter (QtGui.QPainter): the overlay painter.
            item (PlannedItem or BaseScheduledItem): the item to paint
                connections for.
            connected_only (bool): if True, only paint items that have
                connections.
        """
        child_rect = self.get_child_rect(item)
        if child_rect is None:
            return
        if self.timetable_view is not None:
            parent_list = item.planned_items
        else:
            parent_list = item.planned_parents
        if not connected_only or parent_list:
            path = QtGui.QPainterPath()
            path.addRect(child_rect)
            painter.fillPath(path, painter.brush())

        for parent_item in parent_list:
            parent_rect = self.get_parent_rect(parent_item)
            if parent_rect is None:
                continue
            path = QtGui.QPainterPath()
            path.addRect(parent_rect)
            painter.fillPath(path, painter.brush())
            line_start = (parent_rect.right(), parent_rect.center().y())
            line_end = (child_rect.left(), child_rect.center().y())
            painter.drawLine(*line_start, *line_end)

    def paint_overlay(self, painter):
        """Paint the overlay.

        Args:
            painter (QtGui.QPainter): the overlay painter.
        """
        if (not self.display_all_connections
                and not self.display_connections_on_hover):
            return
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen = QtGui.QPen(constants.HYBRID_VIEW_CONNECTION_LINE_COLOR, 1)
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        brush = QtGui.QBrush(constants.HYBRID_VIEW_SELECTION_COLOR)
        painter.setPen(pen)
        painter.setBrush(brush)
        if self.display_all_connections:
            planned_items_iterator = self.planner_manager.iter_filtered_items(
                self.calendar_period,
            )
            for planned_item in planned_items_iterator:
            # for planned_item in self.calendar_period.iter_planned_items():
                self.paint_child_connections(
                    painter,
                    planned_item,
                    connected_only=True,
                )
        elif self.hovered_parent_item is not None:
            self.paint_child_connections(painter, self.hovered_parent_item)
        elif self.hovered_child_item is not None:
            self.paint_parent_connections(painter, self.hovered_child_item)

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        modifiers = event.modifiers()
        success = False

        if modifiers == QtCore.Qt.ControlModifier:
            # ctrl+d: toggle display of item connections
            if event.key() == QtCore.Qt.Key_D:
                self.set_connections_displayed_on_hover(
                    not self.display_connections_on_hover
                )
                self.connections_timer_id = self.startTimer(
                    constants.TINY_TIMER_INTERVAL
                )
                self.display_all_connections = True
                self.update()

        super(OverlayedPlannerHybridView, self).keyPressEvent(event)

    def timerEvent(self, event):
        """Called every timer_interval.

        Args:
            event (QtCore.QEvent): the timer event.
        """
        if event.timerId() == self.connections_timer_id:
            self.killTimer(self.connections_timer_id)
            self.connections_timer_id = None
            self.display_all_connections = False
            self.update()
