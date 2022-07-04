"""Planner list view."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.calendar import (
    CalendarDay,
    CalendarWeek,
    CalendarMonth,
    CalendarYear,
)
from scheduler.api.calendar.planned_item import (
    PlannedItemImportance,
    PlannedItemSize,
)
from scheduler.api.utils import fallback_value

from scheduler.ui.models.list import PlannerListModel
from scheduler.ui.tabs.base_calendar_view import (
    BaseCalendarView,
    BaseListView,
)


class TitledPlannerListView(BaseCalendarView, QtWidgets.QFrame):
    """Planner list view with title."""
    TITLE_SIZE = 22

    def __init__(
            self,
            name,
            project,
            time_period,
            parent=None):
        """Initialise planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            time_period (PlannedItemTimePeriod): type of time period to
                view over.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TitledPlannerListView, self).__init__(parent=parent)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.title = QtWidgets.QLabel()
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        font = QtGui.QFont()
        font.setPixelSize(self.TITLE_SIZE)
        self.title.setFont(font)
        main_layout.addWidget(self.title)
        self.planner_list_view = PlannerListView(name, project, time_period)
        main_layout.addWidget(self.planner_list_view)
        self.setFrameShape(self.Shape.Box)
        self.planner_list_view.VIEW_UPDATED_SIGNAL.connect(
            self.VIEW_UPDATED_SIGNAL.emit
        )

    def set_to_calendar_period(self, calendar_period):
        """Set view to given calendar_period.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period to set to.
        """
        self.title.setText(self.get_title(calendar_period))
        self.planner_list_view.set_to_calendar_period(calendar_period)

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


class PlannerListView(BaseListView):
    """Planner list view."""
    def __init__(
            self,
            name,
            project,
            time_period,
            parent=None):
        """Initialise planner view.

        Args:
            name (str): name of tab.
            project (Project): the project we're working on.
            time_period (PlannedItemTimePeriod): type of time period to view
                over.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        self.open_dialog_on_drop_event = False
        self.planner_manager = project.get_planner_manager()
        model = PlannerListModel(
            project.get_tree_manager(name),
            self.planner_manager,
            time_period=time_period,
            open_dialog_on_drop_event=self.open_dialog_on_drop_event,
        )
        super(PlannerListView, self).__init__(
            name,
            project,
            model,
            parent=parent,
        )

        self.setSizeAdjustPolicy(self.SizeAdjustPolicy.AdjustToContents)

        header = self.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)

        for column in range(self.model().columnCount()):
            self.resizeColumnToContents(column)

        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)        
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)

        self.setSortingEnabled(True)

        self.setItemDelegate(
            PlannedItemDelegate(
                self.planner_manager,
                self.tree_manager,
                model,
            )
        )
        self.open_editors()
        model.modelReset.connect(self.update)
        model.modelReset.connect(self.VIEW_UPDATED_SIGNAL.emit)
        model.dataChanged.connect(self.update)
        model.dataChanged.connect(self.VIEW_UPDATED_SIGNAL.emit)
        self.setUniformRowHeights(True)

    def resizeEvent(self, event):
        """Resize event.

        Args:
            event (QtCore.QEvent): the event.
        """
        super(PlannerListView, self).resizeEvent(event)
        # self.open_editors()

    def open_editors(self):
        """Open persistent editors on each column."""
        model = self.model()
        for i in range(model.rowCount()):
            for j in range(model.columnCount()):
                index = model.index(i, j, QtCore.QModelIndex())
                if (model.get_column_name(index) not in
                        [model.IMPORTANCE_COLUMN, model.SIZE_COLUMN]):
                    continue
                if index.isValid():
                    if self.isPersistentEditorOpen(index):
                        self.closePersistentEditor(index)
                    self.openPersistentEditor(index)

    def update(self):
        """Update view."""
        # self.open_editors()
        super(PlannerListView, self).update()

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        modifiers = event.modifiers()

        if not modifiers:
            # del: remove item
            if event.key() == QtCore.Qt.Key_Delete:
                current_index = self.currentIndex()
                if current_index is not None:
                    if self.model().remove_item(current_index, force=False):
                        self.update()

        elif modifiers == QtCore.Qt.ControlModifier:
            # ctrl+del: force remove item
            if event.key() == QtCore.Qt.Key_Delete:
                current_index = self.currentIndex()
                if current_index is not None:
                    if self.model().remove_item(current_index, force=True):
                        self.update()

        super(PlannerListView, self).keyPressEvent(event)

    # def eventFilter(self, obj, event):
    #     """Event filter for when object is resized.

    #     Args:
    #         obj (QtCore.QObject): QObject that event is happening on.
    #         event (QtCore.QEvent): event that is happening.
    #     """
    #     if self.title_widget is None:
    #         return False
    #     if obj == self.title_widget and event.type() == QtCore.QEvent.Resize:
    #         self.title_widget.setMinimumHeight(
    #             event.size().height()
    #         )
    #         print (event.size().height())
    #     return False


class PlannedItemDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for planned items."""
    def __init__(
            self,
            planner_manager,
            tree_manager,
            model,
            parent=None):
        """Initialise planned item delegate item.

        Args:
            planner_manager (PlannerManager): planner manager object.
            tree_manager (TreeManager): tree manager object.
            model (QtCore.QAbstractItemModel): the model this is modelling.
            parent (QtWidgets.QWidget or None): Qt parent of delegate.
        """
        super(PlannedItemDelegate, self).__init__(parent)
        self.model = model
        self.planner_manager = planner_manager
        self.tree_manager = tree_manager

    def createEditor(self, parent, option, index):
        """Create editor widget for edit role.

        Args:
            parent (QtWidgets.QWidget): parent widget.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.

        Returns:
            (QtWidgets.QWidget): editor widget.
        """
        column_name = self.model.get_column_name(index)
        if column_name == self.model.IMPORTANCE_COLUMN:
            editor_widget = QtWidgets.QComboBox(parent=parent)
            editor_widget.addItem("")
            editor_widget.addItems(PlannedItemImportance.VALUES_LIST)
            return editor_widget
        elif column_name == self.model.SIZE_COLUMN:
            editor_widget = QtWidgets.QComboBox(parent=parent)
            editor_widget.addItem("")
            editor_widget.addItems(PlannedItemSize.VALUES_LIST)
            return editor_widget
        return super(PlannedItemDelegate, self).createEditor(
            parent,
            option,
            index,
        )
