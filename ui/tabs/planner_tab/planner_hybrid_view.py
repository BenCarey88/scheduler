"""Hybrid planner views."""

from operator import contains
from PyQt5 import QtWidgets, QtCore, QtGui

from scheduler.api.calendar.planned_item import PlannedItemTimePeriod as PITP
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


class PlannerHybridDayView(BaseHybridView):
    """Hybrid list-timetable view for day planner."""
    def __init__(self, name, project, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        left_view = TitledPlannerListView(name, project, PITP.DAY)
        right_view = SchedulerTimetableView(name, project, num_days=1)
        super(PlannerHybridDayView, self).__init__(
            name,
            project,
            left_view,
            right_view,
            parent=parent,
        )


class PlannerHybridWeekView(BaseHybridView):
    """Hybrid list-multilist view for week planner."""
    def __init__(self, name, project, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        left_view = TitledPlannerListView(name, project, PITP.WEEK)
        right_view = PlannerMultiListWeekView(name, project)
        super(PlannerHybridWeekView, self).__init__(
            name,
            project,
            left_view,
            right_view,
            parent=parent,
        )


class PlannerHybridMonthView(BaseHybridView):
    """Hybrid list-multilist view for month planner."""
    def __init__(self, name, project, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        left_view = TitledPlannerListView(name, project, PITP.MONTH)
        right_view = PlannerMultiListMonthView(name, project)
        super(PlannerHybridMonthView, self).__init__(
            name,
            project,
            left_view,
            right_view,
            parent=parent,
        )


class PlannerHybridYearView(BaseHybridView):
    """Hybrid list-multilist view for year planner."""
    def __init__(self, name, project, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        left_view = TitledPlannerListView(name, project, PITP.YEAR)
        right_view = PlannerMultiListYearView(name, project)
        super(PlannerHybridYearView, self).__init__(
            name,
            project,
            left_view,
            right_view,
            parent=parent,
        )


class OverlayedPlannerHybridYearView(BaseOverlayedView):
    """Hybrid list/multilist view for year planner with overlay."""
    LINE_BUFFER = 20
    RECT_MAX_BUFFER_L = 10
    RECT_MAX_BUFFER_R = 10

    def __init__(self, name, project, parent=None):
        """Initialise hybrid planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        self.hybrid_view = PlannerHybridYearView(name, project)
        super(OverlayedPlannerHybridYearView, self).__init__(
            name,
            project,
            self.hybrid_view,
            parent=parent,
        )
        self.list_view = self.hybrid_view.left_view.planner_list_view
        self.multilist_view = self.hybrid_view.right_view
        self.hovered_parent_item = None
        self.hovered_child_item = None
        self.set_mouse_tracking(True)
        self.list_view.HOVERED_ITEM_SIGNAL.connect(
            self.set_hovered_parent_item
        )
        self.list_view.HOVERED_ITEM_REMOVED_SIGNAL.connect(
            self.set_hovered_parent_item
        )
        self.multilist_view.HOVERED_ITEM_SIGNAL.connect(
            self.set_hovered_child_item
        )
        self.multilist_view.HOVERED_ITEM_REMOVED_SIGNAL.connect(
            self.set_hovered_child_item
        )

    def set_mouse_tracking(self, value):
        """Enable or disable mouse tracking for subviews.

        Args:
            value (bool): whether to enable or disable.
        """
        self.list_view.setMouseTracking(value)
        for subview in self.multilist_view.iter_widgets():
            subview.planner_list_view.setMouseTracking(value)

    def set_hovered_parent_item(self, planned_item=None):
        """Set hovered parent item to given value.

        Args:
            planned_item (PlannedItem or None): new value for parent.
        """
        self.hovered_parent_item = planned_item
        self.overlay.update()

    def set_hovered_child_item(self, planned_item=None):
        """Set hovered child item to given value.

        Args:
            planned_item (PlannedItem or None): new value for child.
        """
        self.hovered_child_item = planned_item
        self.overlay.update()

    def paint_overlay(self, painter):
        """Paint the overlay.

        Args:
            painter (QtGui.QPainter): the overlay painter.
        """
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor(227, 36, 43), 1)
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        brush = QtGui.QBrush(QtGui.QColor(227, 227, 43, 100))
        painter.setPen(pen)

        if self.hovered_parent_item is not None:
            parent_item = self.hovered_parent_item
            parent_rect = self.list_view.get_rect_for_item(
                self.hovered_parent_item,
                self,
                stop_at_text_end=True,
                x_max=(self.list_view.rect().right() + self.RECT_MAX_BUFFER_L)
            )
            if parent_rect is None:
                return
            path = QtGui.QPainterPath()
            path.addRect(parent_rect)
            painter.fillPath(path, brush)

            for child_item in parent_item.get_planned_children(PITP.MONTH):
                item_view = self.multilist_view.get_month_view(
                    child_item.calendar_period
                ).planner_list_view
                child_rect = item_view.get_rect_for_item(
                    child_item,
                    self,
                    stop_at_text_end=True,
                    x_max=(
                        self.list_view.rect().width()
                        + self.multilist_view.rect().right()
                        - self.RECT_MAX_BUFFER_R
                    )
                )
                if child_rect is None:
                    continue

                line_start = (
                    parent_rect.right(),
                    parent_rect.center().y(),
                )
                line_end = (
                    child_rect.left(),
                    child_rect.center().y(),
                )
                painter.drawLine(*line_start, *line_end)
                path = QtGui.QPainterPath()
                path.addRect(child_rect)
                painter.fillPath(path, brush)

        elif self.hovered_child_item is not None:
            child_item = self.hovered_child_item
            item_view = self.multilist_view.get_month_view(
                child_item.calendar_period
            ).planner_list_view
            child_rect = item_view.get_rect_for_item(
                child_item,
                self,
                stop_at_text_end=True,
                x_max=(
                    self.list_view.rect().width()
                    + self.multilist_view.rect().right()
                    - self.RECT_MAX_BUFFER_R
                )
            )
            if child_rect is None:
                return
            path = QtGui.QPainterPath()
            path.addRect(child_rect)
            painter.fillPath(path, brush)

            for parent_item in child_item.get_planned_parents(PITP.YEAR):
                parent_rect = self.list_view.get_rect_for_item(
                    parent_item,
                    self,
                    stop_at_text_end=True,
                    x_max=(
                        self.list_view.rect().right()
                        + self.RECT_MAX_BUFFER_L
                    )
                )
                if parent_rect is None:
                    continue

                line_start = (
                    parent_rect.right(),
                    parent_rect.center().y(),
                )
                line_end = (
                    child_rect.left(),
                    child_rect.center().y(),
                )
                painter.drawLine(*line_start, *line_end)
                path = QtGui.QPainterPath()
                path.addRect(parent_rect)
                painter.fillPath(path, brush)
