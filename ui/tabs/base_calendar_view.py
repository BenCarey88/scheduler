"""Base calendar view to view models in calendar tabs."""


from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.calendar.calendar_period import CalendarDay
from scheduler.api.common.date_time import Date
from scheduler.ui import utils
from scheduler.ui.widgets.widget_list_view import WidgetListView


class BaseCalendarView(object):
    """Base class for all calendar views."""
    # WIDTH_BUFFER = 10
    VIEW_UPDATED_SIGNAL = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(BaseCalendarView, self).__init__(*args, **kwargs)
        self.width_attr = None

    # def resize_view(self, width):
    #     """Resize view using given width.

    #     Args:
    #         width (int): new pixel width of widget this view is contained in.
    #     """
    #     pass

    def setup(self):
        """Any setup that needs to be done after tab init is done here."""
        pass

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        raise NotImplementedError(
            "set_to_calendar_period must be implemented in subclasses"
        )

    # def resizeEvent(self, event):
    #     size = self.sizeHint()
    #     new_event = QtGui.QResizeEvent(size, event.oldSize())
    #     return super(BaseCalendarView, self).resizeEvent(new_event)

    # def sizeHint(self):
    #     """Get size hint for view."""
    #     size = super(BaseCalendarView, self).sizeHint()
    #     print ("hello")
    #     if self.width_attr is not None:
    #         print ("old_width", size.width(), "new_width", self.width_attr)
    #         return QtCore.QSize(
    #             self.width_attr - self.WIDTH_BUFFER,
    #             size.height(),
    #         )
    #     return size


### LIST ###
class BaseListView(BaseCalendarView, QtWidgets.QTreeView):
    """Base list view for all list calendar tab views.

    Note that according to qt's framework, this is a tree view, since
    QListViews don't allow headers, which we may want.
    """
    # WIDTH_BUFFER = 10

    def __init__(
            self,
            name,
            project,
            list_model,
            enable_custom_resize=False,
            parent=None):
        """Initialize class instance.

        Args:
            name (str): name of tab this is used in.
            project (Project): the project we're working on.
            list_model (BaseListModel): the model we're using for this view.
            enable_custom_resize (bool): if True, use resize_view method
                to resize the view when its parent is resized.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseListView, self).__init__(parent=parent)
        self.tree_manager = project.get_tree_manager(name)
        self.tree_root = self.tree_manager.tree_root
        self.calendar = project.calendar
        self.calendar_period = None
        self.setModel(list_model)
        self.setItemsExpandable(False)
        utils.set_style(self, "base_list_view.qss")
        # self.enable_custom_resize = enable_custom_resize
        # self._width = None
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        self.calendar_period = calendar_period
        self.model().set_calendar_period(calendar_period)
        self.update()

    # def resize_view(self, width):
    #     """Resize view using given width.

    #     Args:
    #         width (int): new pixel width of widget this view is contained in.
    #     """
    #     if self.enable_custom_resize:
    #         self._width = width
    #         self.adjustSize()

    # def sizeHint(self):
        # return super().sizeHint()
    #     """Get size hint for view."""
    #     size = super(BaseListView, self).sizeHint()
    #     if self.enable_custom_resize and self._width is not None:
    #         return QtCore.QSize(
    #             self._width - self.WIDTH_BUFFER,
    #             size.height(),
    #         )
    #     return size


### MULTI-LIST ###
class BaseMultiListView(BaseCalendarView, WidgetListView):
    """Base multi-list view for calendar views containing multiple lists."""
    # LIST_SPACING = 5

    def __init__(self, list_views, parent=None):
        """Initialize class instance.

        Args:
            list_views (list(QtWidgets.QWidget)): list of subviews. These
                subviews each represent a calendar period below the current
                one.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseMultiListView, self).__init__(list_views, parent=parent)
        # for row, view in enumerate(list_views):
        #     view.VIEW_UPDATED_SIGNAL.connect(partial(self.open_editor, row))
        # self.setHorizontalScrollBarPolicy(
        #     QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        # )
        # self.list_views = list_views
        # main_layout = QtWidgets.QVBoxLayout()
        # main_layout.setSizeConstraint(main_layout.SizeConstraint.SetFixedSize)
        # main_widget = QtWidgets.QWidget()
        # main_widget.setLayout(main_layout)
        # for list_view in list_views:
        #     # print (self.viewport().sizeHint().width())
        #     # list_view.setMinimumWidth(self.viewport().sizeHint().width())
        #     main_layout.addWidget(list_view)
        #     main_layout.addSpacing(self.LIST_SPACING)
        # self.setWidget(main_widget)
        # # print (main_widget.width())
        # # main_layout.setSizeConstraint(main_layout.SizeConstraint.SetFixedSize)
        # self.setWidgetResizable(True)
        # self.setSizeAdjustPolicy(self.SizeAdjustPolicy.AdjustToContents)

    def setup(self):
        """Any setup that needs to be done after tab initialization."""
        for view in self.widget_list:
            view.setup()
            view.VIEW_UPDATED_SIGNAL.connect(self.scheduleDelayedItemsLayout)
            view.VIEW_UPDATED_SIGNAL.connect(self.VIEW_UPDATED_SIGNAL.emit)

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        raise NotImplementedError(
            "set to calendar period implemented in BaseTableView subclasses."
        )

    # def resize_view(self, width):
    #     """Resize view using given width.

    #     Args:
    #         width (int): new pixel width of widget this view is contained in.
    #     """
    #     for view in self.list_views:
    #         view.resize_view(width)

    # def resizeEvent(self, event):
    #     for view in self.list_views:
    #         view.width_attr = event.size().width()
    #         view.adjustSize()
    #     return super(BaseMultiListView, self).resizeEvent(event)


class BaseMultiListWeekView(BaseMultiListView):
    """Base view for calendar weeks containing calendar day list views."""
    def __init__(self, list_views, parent=None):
        """Initialize class instance.

        Args:
            list_views (list(QtWidgets.QWidget)): list of subviews. These
                subviews each represent a week in the month.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseMultiListWeekView, self).__init__(list_views, parent=parent)
        self.set_to_calendar_period = self.set_to_calendar_week

    def set_to_calendar_week(self, calendar_week):
        """Set view to given calendar_week.

        Args:
            calendar_week (CalendarWeek): calendar week to set to.
        """
        calendar_days = list(calendar_week.iter_days())
        for calendar_day, list_view in zip(calendar_days, self.widget_list):
            list_view.set_to_calendar_period(calendar_day)


class BaseMultiListMonthView(BaseMultiListView):
    """Base view for calendar month containing calendar week list views."""
    def __init__(self, list_views, parent=None):
        """Initialize class instance.

        Args:
            list_views (list(QtWidgets.QWidget)): list of subviews. These
                subviews each represent a week in the month.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseMultiListMonthView, self).__init__(list_views, parent=parent)
        # make sure there's always 5 views (max required) and hide any unused
        if len(list_views) != 5:
            raise Exception(
                "MultiListMonthView class needs exactly 5 list subvies, with "
                "any unused ones hidden."
            )
        self.set_to_calendar_period = self.set_to_calendar_month

    def set_to_calendar_month(self, calendar_month):
        """Set view to given calendar_month.

        Args:
            calendar_month (CalendarMonth): calendar month to set to.
        """
        calendar_weeks = calendar_month.get_calendar_weeks()
        for i in range(5 - len(calendar_weeks)):
            self.widget_list[-1 -i].setHidden(True)
        for calendar_week, list_view in zip(calendar_weeks, self.widget_list):
            list_view.set_to_calendar_period(calendar_week)
            list_view.setHidden(False)


class BaseMultiListYearView(BaseMultiListView):
    """Base view for calendar year containing calendar month list views."""
    def __init__(self, list_views, parent=None):
        """Initialize class instance.

        Args:
            list_views (list(QtWidgets.QWidget)): list of subviews. These
                subviews each represent a month in the year.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseMultiListYearView, self).__init__(list_views, parent=parent)
        self.set_to_calendar_period = self.set_to_calendar_year

    def set_to_calendar_year(self, calendar_year):
        """Set view to given calendar_year.

        Args:
            calendar_year (CalendarYear): calendar year to set to.
        """
        calendar_months = list(calendar_year.iter_months())
        for calendar_month, list_view in zip(calendar_months, self.widget_list):
            list_view.set_to_calendar_period(calendar_month)


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

    def set_to_week(self, calendar_period):
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


### HYBRID ###
class BaseHybridView(BaseCalendarView, QtWidgets.QSplitter):
    """Base hybrid view for combo of two other calendar views."""
    def __init__(self, left_view, right_view, parent=None):
        """Initialize class instance.

        Args:
            left_view (QtWidgets.QWidget): left view.
            right_view (QtWidgets.QWidget): right view.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(BaseHybridView, self).__init__(parent=parent)
        self.left_view = left_view
        self.right_view = right_view
        self.addWidget(left_view)
        self.addWidget(right_view)
        self.setChildrenCollapsible(False)

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        self.left_view.set_to_calendar_period(calendar_period)
        self.right_view.set_to_calendar_period(calendar_period)

    def setup(self):
        """Any setup that needs to be done after tab initialization."""
        for view in (self.left_view, self.right_view):
            view.setup()
            view.VIEW_UPDATED_SIGNAL.connect(self.VIEW_UPDATED_SIGNAL.emit)
