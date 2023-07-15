"""Planned item dialog for creating and editing planned items."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.calendar.planned_item import PlannedItem
from scheduler.ui import utils
from .item_dialog import ItemDialog


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
            planned_item_parent=None,
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
            planned_item_parent (PlannedItem or None): planned item parent for
                this planned item, if given.
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
        self._planned_item_parent = planned_item_parent

        # TODO: this will be useful once we start adding other fields into
        # this dialog, so then we can uncomment the below
        # if planned_item is None:
        #     # create a temp planned item just to get default values
        #     planned_item = PlannedItem(
        #         self._calendar,
        #         calendar_period,
        #         tree_item,
        #     )
        # tree_item = planned_item.tree_item

        self.setMinimumSize(900, 700)
        utils.set_style(self, "scheduled_item_dialog.qss")

        self.task_label = QtWidgets.QLabel()
        self.main_layout.addWidget(self.task_label)
        self.on_tree_view_changed()

    def on_tree_view_changed(self):
        """Callback for when a new tree item is selected."""
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

    def accept_and_close(self):
        """Run add or modify scheduled item edit.

        Called when user clicks accept.
        """
        if self.is_editor:
            self._planner_manager.modify_planned_item(
                self.planned_item,
                calendar_period=self._calendar_period,
                tree_item=self.tree_item,
            )
        else:
            self._planner_manager.create_planned_item(
                self._calendar,
                self._calendar_period,
                self.tree_item,
                index=self._index,
                parent=self._planned_item_parent,
            )
        super(PlannedItemDialog, self).accept_and_close()

    def delete_item_and_close(self):
        """Run remove scheduled item edit.

        Called when user clicks delete.
        """
        self._planner_manager.remove_planned_item(self.planned_item)
        super(PlannedItemDialog, self).delete_item_and_close()
