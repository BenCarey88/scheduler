"""Multi-list planner views."""

from PyQt5 import QtCore

from scheduler.api.enums import TimePeriod
from scheduler.api.calendar.planned_item import PlannedItem
from scheduler.api.edit.edit_callbacks import CallbackType
from scheduler.ui.tabs.base_calendar_view import (
    BaseMultiListWeekView,
    BaseMultiListMonthView,
    BaseMultiListYearView,
)
from .planner_list_view import TitledPlannerListView


class BasePlannerMultilist(object):
    """Base functionality for planner multilist views."""
    HOVERED_ITEM_SIGNAL = QtCore.pyqtSignal(PlannedItem)
    HOVERED_ITEM_REMOVED_SIGNAL = QtCore.pyqtSignal()

    def setup(self):
        """Additional setup after tab init."""
        super(BasePlannerMultilist, self).setup()
        for view in self.iter_widgets():
            view.HOVERED_ITEM_SIGNAL.connect(
                self.HOVERED_ITEM_SIGNAL.emit
            )
            view.HOVERED_ITEM_REMOVED_SIGNAL.connect(
                self.HOVERED_ITEM_REMOVED_SIGNAL.emit
            )

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(BasePlannerMultilist, self).post_edit_callback(
            callback_type,
            *args
        )
        if callback_type == CallbackType.TREE_REMOVE:
            self.update_view()


class PlannerMultiListWeekView(BasePlannerMultilist, BaseMultiListWeekView):
    """Multi list week view for planner."""
    def __init__(self, name, project, num_days=7, parent=None):
        """Initialise multi-list planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            num_days (int): number of days to generate for. Defaults to week.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        list_views = [
            TitledPlannerListView(name, project, TimePeriod.DAY)
            for _ in range(num_days)
        ]
        super(PlannerMultiListWeekView, self).__init__(
            name,
            project,
            list_views,
            parent=parent,
        )
        self.hide_day_change_buttons = (num_days == 7)


class PlannerMultiListMonthView(BasePlannerMultilist, BaseMultiListMonthView):
    """Multi list month view for planner."""
    def __init__(self, name, project, parent=None):
        """Initialise multi-list planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        list_views = [
            TitledPlannerListView(name, project, TimePeriod.WEEK)
            for _ in range(5)
        ]
        super(PlannerMultiListMonthView, self).__init__(
            name,
            project,
            list_views,
            parent=parent,
        )


class PlannerMultiListYearView(BasePlannerMultilist, BaseMultiListYearView):
    """Multi list year view for planner."""
    def __init__(self, name, project, parent=None):
        """Initialise multi-list planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        list_views = [
            TitledPlannerListView(name, project, TimePeriod.MONTH)
            for _ in range(12)
        ]
        super(PlannerMultiListYearView, self).__init__(
            name,
            project,
            list_views,
            parent=parent,
        )
