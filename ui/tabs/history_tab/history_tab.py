"""History tab."""

from collections import OrderedDict

from scheduler.api.filter import FilterType

from scheduler.ui.tabs.base_calendar_tab import BaseCalendarTab
from scheduler.ui.widgets.navigation_panel import DateType, ViewType

from .history_timetable_view import HistoryTimeTableView


class HistoryTab(BaseCalendarTab):
    """History tab."""
    def __init__(self, project, parent=None):
        """Setup history tab.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        name = FilterType.HISTORY
        main_views_dict = OrderedDict([
            (
                (DateType.DAY, ViewType.TIMETABLE),
                HistoryTimeTableView(name, project, num_days=1),
            ),
            (
                (DateType.THREE_DAYS, ViewType.TIMETABLE),
                HistoryTimeTableView(name, project, num_days=3),
            ),
            (
                (DateType.WEEK, ViewType.TIMETABLE),
                HistoryTimeTableView(name, project, num_days=7),
            ),
        ])
        super(HistoryTab, self).__init__(
            name,
            project,
            main_views_dict,
            DateType.WEEK,
            ViewType.TIMETABLE,
            parent=parent,
        )
