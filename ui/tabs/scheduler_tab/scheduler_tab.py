"""Scheduler Tab."""

from collections import OrderedDict

from scheduler.ui.models.table import SchedulerDayModel
from scheduler.ui.tabs.base_calendar_tab import (
    BaseCalendarTab,
    BaseDayTableView,
)
from scheduler.ui.widgets.navigation_panel import DateType, ViewType
from scheduler.ui import utils

from .scheduler_days_view import SchedulerTimetableView


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
                SchedulerTimetableView(name, project)
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
