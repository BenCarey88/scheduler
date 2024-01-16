"""Planned item dialog for creating and editing planned items."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.calendar.planned_item import PlannedItem
from scheduler.ui import layout_utils, utils
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
        self.values_cache = {}

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
        # utils.set_style(self, "planned_item_dialog.qss")

        self.task_label = QtWidgets.QLabel()
        self.main_layout.addWidget(self.task_label)
        line_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(line_layout)

        self.le_name = layout_utils.add_text_field(
            line_layout,
            "Name",
            default=(planned_item.name if planned_item else None),
        )
        self.cb_update_task_display_name = layout_utils.add_checkbox_field(
            line_layout,
            "update task display_name",
        )
        self.on_tree_view_changed()

    def on_tree_view_changed(self, new_index=None, old_index=None):
        """Callback for when a new tree item is selected.

        Args:
            new_index (QtCore.QModelIndex or None): new index, if given.
            old_index (QtCore.QModelIndex or None): previous index, if given.
        """
        # cache old values
        if old_index is not None and old_index.isValid():
            old_task = old_index.internalPointer()
            task_dict = {}
            self.values_cache[old_task] = task_dict
            name = self.le_name.text()
            if name and name != old_task.get_display_name():
                task_dict["name"] = name

        # set new values (from cache or existing attributes)
        if self.tree_item:
            new_task = self.tree_item
            task_dict = self.values_cache.get(new_task, {})
            self.task_label.setText(new_task.path)
            self.le_name.setText(
                task_dict.get("name", self.tree_item.get_display_name())                  
            )

    @property
    def planned_item(self):
        """Get the planned item being edited, if one exists.

        Returns:
            (PlannedItem or None): the scheduled item being edited,
                if one exists.
        """
        return self._item

    def get_name(self):
        """Get name value, if it differs from the task display name.

        Returns:
            (str or None): name value if it differs from task display name.
        """
        name = self.le_name.text()
        if (self.tree_item is not None
                and self.tree_item.get_display_name() != name):
            return name or None
        return None

    def accept_and_close(self):
        """Run add or modify scheduled item edit.

        Called when user clicks accept.
        """
        if self.is_editor:
            success = self._planner_manager.modify_planned_item(
                self.planned_item,
                calendar_period=self._calendar_period,
                tree_item=self.tree_item,
                name=self.get_name(),
            )
        else:
            success = self._planner_manager.create_planned_item(
                self._calendar,
                self._calendar_period,
                index=self._index,
                tree_item=self.tree_item,
                name=self.get_name(),
                parent=self._planned_item_parent,
            )
        if self.tree_item and self.cb_update_task_display_name.isChecked():
            self._tree_manager.modify_task_item(
                self.tree_item,
                display_name=self.get_name(),
                stack=success,
            )
        super(PlannedItemDialog, self).accept_and_close()

    def delete_item_and_close(self):
        """Run remove scheduled item edit.

        Called when user clicks delete.
        """
        self._planner_manager.remove_planned_item(self.planned_item)
        super(PlannedItemDialog, self).delete_item_and_close()
