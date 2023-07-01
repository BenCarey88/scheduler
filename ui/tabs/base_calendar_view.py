"""Base calendar view to view models in calendar tabs."""


from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.calendar.calendar_period import (
    CalendarDay,
    CalendarWeek,
    CalendarMonth,
    CalendarYear,
)
from scheduler.api.common.date_time import Date
from scheduler.ui import utils
from scheduler.ui.widgets.widget_list_view import WidgetListView
from scheduler.ui.widgets.overlay import OverlayedWidget


class BaseCalendarView(object):
    """Base class for all calendar views."""
    VIEW_UPDATED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, name, project, *args, **kwargs):
        """Initialize.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
        """
        super(BaseCalendarView, self).__init__(*args, **kwargs)
        self.tree_manager = project.get_tree_manager(name)
        self.tree_root = self.tree_manager.tree_root
        self.calendar = project.calendar
        self.calendar_period = None
        self._is_active = False
        # set this attribute to True if we want to remove day change buttons
        self.hide_day_change_buttons = False

    def get_subviews(self):
        """Get any subviews of current view.

        Returns:
            (list(BaseCalendarView)): list of subviews.
        """
        return []

    def setup(self):
        """Any setup that needs to be done after tab init is done here."""
        for subview in self.get_subviews():
            subview.setup()
            subview.VIEW_UPDATED_SIGNAL.connect(self.VIEW_UPDATED_SIGNAL.emit)

    def set_active(self, value):
        """Set view as active/inactive when we switch to/from it.

        Args:
            value (bool): whether to set as active or inactive.
        """
        self._is_active = value
        for subview in self.get_subviews():
            subview.set_active(value)

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Note that we don't apply this automatically to subviews because
        some subviews (eg. multi-lists) use different calendar periods.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        self.calendar_period = calendar_period

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        for subview in self.get_subviews():
            subview.pre_edit_callback(callback_type, *args)

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        for subview in self.get_subviews():
            subview.post_edit_callback(callback_type, *args)

    def on_view_changed(self):
        """Callback for when this view is loaded."""
        for subview in self.get_subviews():
            subview.on_view_changed()

    def on_outliner_filter_changed(self, *args):
        """Callback for what to do when filter is changed in outliner."""
        for subview in self.get_subviews():
            subview.on_outliner_filter_changed()


### LIST ###
class BaseListView(BaseCalendarView, QtWidgets.QTreeView):
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
        super(BaseListView, self).__init__(name, project, parent=parent)
        self.setModel(list_model)
        self.setItemsExpandable(False)
        utils.set_style(self, "base_list_view.qss")

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        self.model().set_calendar_period(calendar_period)
        self.update()
        super(BaseListView, self).set_to_calendar_period(calendar_period)


### MULTI-LIST ###
class BaseMultiListView(BaseCalendarView, WidgetListView):
    """Base multi-list view for calendar views containing multiple lists."""
    def __init__(self, name, project, list_views, parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            list_views (list(BaseCalendarView)): list of subviews. These
                subviews each represent a calendar period below the current
                one.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseMultiListView, self).__init__(
            name,
            project,
            list_views,
            parent=parent,
        )

    def get_subviews(self):
        """Get subviews of current view.

        Returns:
            (list(BaseCalendarView)): list of subviews.
        """
        return [view for view in self.iter_widgets()]

    def setup(self):
        """Any setup that needs to be done after tab initialization."""
        super(BaseMultiListView, self).setup()
        for view in self.iter_widgets():
            view.VIEW_UPDATED_SIGNAL.connect(self.update_view)

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        super(BaseMultiListView, self).post_edit_callback(callback_type, *args)
        self.update_view()

    def on_outliner_filter_changed(self, *args):
        """Callback for what to do when filter is changed in outliner."""
        super(BaseMultiListView, self).on_outliner_filter_changed(*args)
        self.update_view()

    def get_subview(self, calendar_period):
        """Get subview for given period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period contained
                in the current one.

        Returns:
            (BaseCalendarView or None): subview, if found.
        """
        raise NotImplementedError(
            "get_subview must be implemented in subclasses."
        )


class BaseMultiListWeekView(BaseMultiListView):
    """Base view for calendar weeks containing calendar day list views."""
    def __init__(self, name, project, list_views, parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            list_views (list(BaseCalendarView)): list of subviews. These
                subviews each represent a week in the month.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseMultiListWeekView, self).__init__(
            name,
            project,
            list_views,
            parent=parent,
        )

    def set_to_calendar_period(self, calendar_week):
        """Set view to given calendar_period.

        Args:
            calendar_week (CalendarWeek): calendar week to set to.
        """
        calendar_days = list(calendar_week.iter_days())
        for calendar_day, list_view in zip(calendar_days, self.get_widgets()):
            list_view.set_to_calendar_period(calendar_day)
        super(BaseMultiListWeekView, self).set_to_calendar_period(
            calendar_week
        )

    def get_subview(self, calendar_day):
        """Get view for given calendar day.

        Args:
            calendar_day (CalendarDay): calendar day.

        Returns:
            (BaseCalendarView or None): day view, if found.
        """
        if self.calendar_period.contains(calendar_day):
            for i, day in enumerate(self.calendar_period.iter_days()):
                if calendar_day == day:
                    return self.get_widget(i)
        return None


class BaseMultiListMonthView(BaseMultiListView):
    """Base view for calendar month containing calendar week list views."""
    def __init__(self, name, project, list_views, parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            list_views (list(BaseCalendarView)): list of subviews. These
                subviews each represent a week in the month.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        # make sure there's always 5 views (max required)
        if len(list_views) != 5:
            raise Exception(
                "MultiListMonthView class needs exactly 5 list subvies, with "
                "any unused ones hidden."
            )
        super(BaseMultiListMonthView, self).__init__(
            name,
            project,
            list_views,
            parent=parent
        )
        self.calendar_weeks = []

    def set_to_calendar_period(self, calendar_month):
        """Set view to given calendar_month.

        Args:
            calendar_month (CalendarMonth): calendar month to set to.
        """
        self.calendar_weeks = calendar_month.get_calendar_weeks(overspill=True)
        for i in range(5 - len(self.calendar_weeks)):
            # filter out any weeks that don't fit into current month
            self.filter_row(4 - i, update=False)
        row_week_view = zip(range(5), self.calendar_weeks, self.get_widgets())
        for i, calendar_week, view in row_week_view:
            self.unfilter_row(i, update=False)
            view.set_to_calendar_period(calendar_week)
        self.update_view()
        super(BaseMultiListMonthView, self).set_to_calendar_period(
            calendar_month
        )

    def get_subview(self, calendar_week):
        """Get view for given calendar week.

        Args:
            calendar_week (CalendarWeek): calendar week.

        Returns:
            (BaseCalendarView or None): week view, if found.
        """
        if self.calendar_period.contains(calendar_week):
            for i, week in enumerate(self.calendar_weeks):
                if calendar_week == week:
                    return self.get_widget(i)
        return None


class BaseMultiListYearView(BaseMultiListView):
    """Base view for calendar year containing calendar month list views."""
    def __init__(self, name, project, list_views, parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            list_views (list(QtWidgets.QWidget)): list of subviews. These
                subviews each represent a month in the year.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseMultiListYearView, self).__init__(
            name,
            project,
            list_views,
            parent=parent
        )

    def set_to_calendar_period(self, calendar_year):
        """Set view to given calendar_year.

        Args:
            calendar_year (CalendarYear): calendar year to set to.
        """
        calendar_months = list(calendar_year.iter_months())
        for calendar_month, view in zip(calendar_months, self.get_widgets()):
            view.set_to_calendar_period(calendar_month)
        super(BaseMultiListYearView, self).set_to_calendar_period(
            calendar_year
        )

    def get_subview(self, calendar_month):
        """Get view for given calendar month.

        Args:
            calendar_month (CalendarMonth): calendar month.

        Returns:
            (BaseCalendarView or None): monath view, if found.
        """
        if self.calendar_period.contains(calendar_month):
            for i, month in enumerate(self.calendar_period.iter_months()):
                if calendar_month == month:
                    return self.get_widget(i)
        return None


### TABLE ###
class BaseTableView(BaseCalendarView, QtWidgets.QTableView):
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
        super(BaseTableView, self).__init__(name, project, parent=parent)
        self.setModel(timetable_model)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)


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

    def set_to_calendar_period(self, calendar_day):
        """Set view to given calendar_day.

        Args:
            calendar_day (CalendarDay): calendar day to set to.
        """
        self.calendar_day = calendar_day
        self.model().set_calendar_day(calendar_day)
        self.update()
        super(BaseDayTableView, self).set_to_calendar_period(calendar_day)


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

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (CalendarWeek or CalendarDay): calendar week
                to set to. We allow passing in a calendar day object too
                and converting it to a calendar week object of length one,
                so that we can use this view with days.
        """
        if isinstance(calendar_period, CalendarDay):
            # allow using this view with days by using one-day week
            calendar_period = calendar_period.get_as_one_day_week()
        self.calendar_week = calendar_period
        self.model().set_calendar_week(calendar_period)
        self.update()
        super(BaseWeekTableView, self).set_to_calendar_period(
            calendar_period
        )


### HYBRID ###
class BaseHybridView(BaseCalendarView, QtWidgets.QSplitter):
    """Base hybrid view for combo of two other calendar views."""
    def __init__(self, name, project, left_view, right_view, parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            left_view (BaseCalendarView): left view.
            right_view (BaseCalendarView): right view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseHybridView, self).__init__(name, project, parent=parent)
        self.left_view = left_view
        self.right_view = right_view
        self.addWidget(left_view)
        self.addWidget(right_view)
        self.setChildrenCollapsible(False)

    def get_subviews(self):
        """Get subviews of current view.

        Returns:
            (list(BaseCalendarView)): list of subviews.
        """
        return [self.left_view, self.right_view]

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        self.left_view.set_to_calendar_period(calendar_period)
        self.right_view.set_to_calendar_period(calendar_period)
        super(BaseHybridView, self).set_to_calendar_period(calendar_period)


### TITLED ###
class BaseTitledView(BaseCalendarView, QtWidgets.QFrame):
    """Base titled view, consisting of title and a subview."""
    TITLE_SIZE = 22

    def __init__(self, name, project, sub_view, parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            sub_view (BaseCalendarView): view to paint over.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseTitledView, self).__init__(name, project, parent=parent)
        self.sub_view = sub_view
        self.title = QtWidgets.QLabel()
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        font = QtGui.QFont()
        font.setPixelSize(self.TITLE_SIZE)
        self.title.setFont(font)

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self.title)
        main_layout.addWidget(self.sub_view)
        self.setFrameShape(self.Shape.Box)

    def get_subviews(self):
        """Get subviews of current view.

        Returns:
            (list(BaseCalendarView)): list of subviews.
        """
        return [self.sub_view]

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        self.title.setText(self.get_title(calendar_period))
        self.planner_list_view.set_to_calendar_period(calendar_period)
        super(BaseTitledView, self).set_to_calendar_period(calendar_period)

    @staticmethod
    def get_title(calendar_period):
        """Get title for given calendar period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to get title
                for.

        Returns:
            (str): title for given calendar period.
        """
        if isinstance(calendar_period, CalendarDay):
            return "{0} {1}".format(
                calendar_period.date.weekday_string(short=False),
                calendar_period.date.ordinal_string(),
            )
        if isinstance(calendar_period, CalendarWeek):
            return "{0} {1} - {2} {3}".format(
                calendar_period.start_date.weekday_string(short=False),
                calendar_period.start_date.ordinal_string(),
                calendar_period.end_date.weekday_string(short=False),
                calendar_period.end_date.ordinal_string(),
            )
        if isinstance(calendar_period, CalendarMonth):
            return calendar_period.start_day.date.month_string(short=False)
        if isinstance(calendar_period, CalendarYear):
            return str(calendar_period.year)


### OVERLAY ###
class BaseOverlayedView(BaseCalendarView, OverlayedWidget):
    """Base overlayed view for custom painting over a view."""
    def __init__(self, name, project, sub_view, parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            sub_view (BaseCalendarView): view to paint over.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseOverlayedView, self).__init__(
            name,
            project,
            sub_view,
            parent=parent,
        )

    def get_subviews(self):
        """Get subviews of current view.

        Returns:
            (list(BaseCalendarView)): list of subviews.
        """
        return [self.sub_widget]

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        self.sub_widget.set_to_calendar_period(calendar_period)
        super(BaseOverlayedView, self).set_to_calendar_period(calendar_period)
