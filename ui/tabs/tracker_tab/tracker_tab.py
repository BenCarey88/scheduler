"""Tacker tab."""

from collections import OrderedDict

from scheduler.api.filter import FilterType

from scheduler.ui.tabs.base_calendar_tab import BaseCalendarTab
from scheduler.ui.widgets.navigation_panel import DateType, ViewType
from scheduler.ui import utils

from .tracker_timetable_view import TrackerTimetableView
from .tracker_month_view import TitledTrackerMonthTableView


class TrackerTab(BaseCalendarTab):
    """Tracker tab."""
    def __init__(self, project, parent=None):
        """Setup tracker tab.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        name = FilterType.TRACKER
        main_views_dict = OrderedDict([
            (
                (DateType.DAY, ViewType.TIMETABLE),
                TrackerTimetableView(name, project, num_days=1),
            ),
            (
                (DateType.THREE_DAYS, ViewType.TIMETABLE),
                TrackerTimetableView(name, project, num_days=3),
            ),
            (
                (DateType.WEEK, ViewType.TIMETABLE),
                TrackerTimetableView(name, project),
            ),
            (
                (DateType.MONTH, ViewType.TIMETABLE),
                TitledTrackerMonthTableView(name, project),
            ),
        ])
        super(TrackerTab, self).__init__(
            name,
            project,
            main_views_dict,
            DateType.WEEK,
            ViewType.TIMETABLE,
            parent=parent,
        )
        utils.set_style(self, "tracker.qss")
