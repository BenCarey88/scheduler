"""Base calendar view to view models in calendar tabs."""


from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date


class BaseListView(QtWidgets.QTreeView):
    """Base list view for all list calendar tab views.

    Note that according to qt's framework, this is a tree view, since
    QListViews don't allow headers, which we may want.
    """
    def __init__(
            self,
            name,
            project,
            list_model,
            parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            list_model (BaseListModel): the model we're using for this view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseListView, self).__init__(parent=parent)
        self.tree_manager = project.get_tree_manager(name)
        self.tree_root = self.tree_manager.tree_root
        self.calendar = project.calendar
        self.calendar_period = None
        self.setModel(list_model)
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        self.calendar_period = calendar_period
        self.model().set_calendar_period(calendar_period)

    def update(self):
        """Update view."""
        self.viewport().update()
        self.header().viewport().update()


class BaseTableView(QtWidgets.QTableView):
    """Base table view for all timetable tab views."""
    def __init__(
            self,
            name,
            project,
            timetable_model,
            parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            timetable_model (BaseTableModel): the model we're using for
                this view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTableView, self).__init__(parent=parent)
        self.tree_manager = project.get_tree_manager(name)
        self.tree_root = self.tree_manager.tree_root
        self.calendar = project.calendar
        self.setModel(timetable_model)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        raise NotImplementedError(
            "set to calendar period implemented in BaseTableView subclasses."
        )

    def update(self):
        """Update view."""
        self.viewport().update()
        self.horizontalHeader().viewport().update()


class BaseDayTableView(BaseTableView):
    """Base day table view for timetable tabs."""

    def __init__(
            self,
            name,
            project,
            timetable_day_model,
            parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            timetable_day_model (BaseDayModel): the model we're using for
                this view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseDayTableView, self).__init__(
            name,
            project,
            timetable_day_model,
            parent=parent
        )
        self.calendar_day = self.calendar.get_day(Date.now())
        self.set_to_calendar_period = self.set_to_day

    def set_to_day(self, calendar_day):
        """Set view to given calendar_day.

        Args:
            calendar_day (CalendarDay): calendar day to set to.
        """
        self.calendar_day = calendar_day
        self.model().set_calendar_day(calendar_day)
        self.update()


class BaseWeekTableView(BaseTableView):
    """Base week table view for timetable tabs."""

    def __init__(
            self,
            name,
            project,
            timetable_week_model,
            parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            timetable_week_model (BaseWeekModel): the model we're using for
                this view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseWeekTableView, self).__init__(
            name,
            project,
            timetable_week_model,
            parent=parent
        )
        self.calendar_week = self.calendar.get_current_week()
        self.set_to_calendar_period = self.set_to_week

    def set_to_week(self, calendar_week):
        """Set view to given calendar_week.

        Args:
            calendar_week (CalendarWeek): calendar week to set to.
        """
        self.calendar_week = calendar_week
        self.model().set_calendar_week(calendar_week)
        self.update()
