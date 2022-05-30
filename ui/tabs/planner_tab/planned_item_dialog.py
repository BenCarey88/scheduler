"""Scheduled item dialog for creating and editing scheduled items."""

from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, DateTime, Time
from scheduler.api.calendar.planned_item import (
    PlannedItem,
    PlannedItemImportance,
    PlannedItemSize,
)

from scheduler.ui import utils
from scheduler.ui.widgets.item_dialog import ItemDialog


class PlannedItemDialog(ItemDialog):
    """Dialog for creating or editing planned items."""

    def __init__(
            self,
            tree_manager,
            planner_manager,
            calendar_period,
            planned_item=None,
            tree_item=None,
            index=None,
            parent=None):
        """Initialise dialog.

        Args:
            tree_manager (TreeManager): the task tree manager object.
            planner_manager (PlannerManager): the planner manager object.
            calendar_period (BaseCalendarPeriod): calendar period we're
                planning over.
            planned_item (PlannedItem or None): planned item we're editing,
                if this is in edit mode. If None, we're in create mode.
            tree_item (Task or None): tree item to initialize with, if we're
                not passing a planned item.
            index (int or None): index to create at.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(PlannedItemDialog, self).__init__(
            tree_manager,
            "Planned Item",
            item=planned_item,
            tree_item=tree_item,
            parent=parent,
        )
        self._calendar = planner_manager.calendar
        self._calendar_period = calendar_period
        self._planner_manager = planner_manager
        self._index = index

        if planned_item is None:
            # create a temp planned item just to get default values
            planned_item = PlannedItem(
                self._calendar,
                calendar_period,
                tree_item,
            )
        size = planned_item.size
        importance = planned_item.importance
        tree_item = planned_item.tree_item

        self.setMinimumSize(900, 700)
        utils.set_style(self, "scheduled_item_dialog.qss")

        self.task_label = QtWidgets.QLabel()
        self.main_layout.addWidget(self.task_label)

        importance_layout = QtWidgets.QHBoxLayout()
        importance_label = QtWidgets.QLabel("Importance")
        self.importance_combobox = QtWidgets.QComboBox()
        self.importance_combobox.addItem("")
        self.importance_combobox.addItems(PlannedItemImportance.VALUES_LIST)
        importance_layout.addWidget(importance_label)
        importance_layout.addWidget(self.importance_combobox)
        self.main_layout.addLayout(importance_layout)
        if importance is not None:
            self.importance_combobox.setCurrentText(importance)

        size_layout = QtWidgets.QHBoxLayout()
        size_label = QtWidgets.QLabel("Size")
        self.size_combobox = QtWidgets.QComboBox()
        self.size_combobox.addItem("")
        self.size_combobox.addItems(PlannedItemSize.VALUES_LIST)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combobox)
        self.main_layout.addLayout(size_layout)
        if size is not None:
            self.size_combobox.setCurrentText(size)

        self.update()

    def update(self):
        """Update dialog properties."""
        if self.tree_item:
            self.task_label.setText(self.tree_item.path)

    @property
    def planned_item(self):
        """Get the planned item being edited, if one exists.

        Returns:
            (PlannedItem or None): the scheduled item being edited,
                if one exists.
        """
        return self._item

    @property
    def importance(self):
        """Get planned item importance.

        Returns:
            (PlannedItemImportance or None): planned item importance.
        """
        return self.importance_combobox.currentText() or None

    @property
    def size(self):
        """Get planned item size.

        Returns:
            (PlannedItemSize or None): planned item size.
        """
        return self.size_combobox.currentText() or None

    def accept_and_close(self):
        """Run add or modify scheduled item edit.

        Called when user clicks accept.
        """
        if self.is_editor:
            self._planner_manager.modify_planned_item(
                self.planned_item,
                calendar_period=self._calendar_period,
                tree_item=self.tree_item,
                size=self.size,
                importance=self.importance,
            )
        else:
            self._planner_manager.create_planned_item(
                self._calendar,
                self._calendar_period,
                self.tree_item,
                size=self.size,
                importance=self.importance,
                index=self._index,
            )
        super(PlannedItemDialog, self).accept_and_close()

    def delete_item_and_close(self):
        """Run remove scheduled item edit.

        Called when user clicks delete.
        """
        self._planner_manager.remove_planned_item(self.planned_item)
        super(PlannedItemDialog, self).delete_item_and_close()
