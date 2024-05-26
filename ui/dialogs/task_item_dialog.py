"""Task dialog for editing tasks and task categories."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common import Date
from scheduler.api.enums import (
    ItemImportance,
    ItemSize,
    TimePeriod,
    TrackedValueType,
)
from scheduler.api.tree.task import TaskType
from scheduler.api.utils import fallback_value

from scheduler.ui import layout_utils
from scheduler.ui.utils import AttributeWidgetWrapper
from scheduler.ui.widgets.task_tracking_widget import TaskTrackingWidget
from .item_dialog import ItemDialog


class TaskItemDialog(ItemDialog):
    """Dialog for editing task items."""
    def __init__(self, tree_manager, task_item, parent=None):
        """Initialise dialog.

        Args:
            tree_manager (TreeManager): the task tree manager object.
            task_item (BaseTaskItem): task item to edit.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(TaskItemDialog, self).__init__(
            tree_manager,
            "Task",
            item=task_item,
            tree_item=task_item,
            parent=parent,
        )
        self.setMinimumSize(900, 700)
        # utils.set_style(self, "task_item_dialog.qss")

        # TODO: feels like we could generalise the cache setups here -
        # both within item_dialog, as I think all item dialogs need to
        # cache by task, but also maybe with a generalised cache utility
        # function or class. Needs to define how to get_values, set_values
        # of widget and also when to trigger, and what to key by. Ideally
        # also needs to allow subcaches that interact with more complex
        # subwidgets and the ability to trigger those subcaches independently
        # when the corresponding subkeys are changed
        self.values_cache = {}
        self.general_field_widgets = []
        self.task_field_widgets = []

        self.task_label = QtWidgets.QLabel()
        self.main_layout.addWidget(self.task_label)

        self.name_field = self.add_field_widget(
            "Name",
            lambda item: item.name,
        )
        self.display_name_field = self.add_field_widget(
            "Display Name",
            lambda item: item.display_name,
        )

        # Task box
        self.task_widgets_box = QtWidgets.QFrame()
        self.task_widgets_layout = QtWidgets.QVBoxLayout()
        self.task_widgets_layout.setContentsMargins(0, 0, 0, 0)
        self.task_widgets_box.setLayout(self.task_widgets_layout)
        self.main_layout.addWidget(self.task_widgets_box)

        # Task fields
        self.type_field = self.add_field_widget(
            "Type",
            lambda task: task.type,
            is_task_field=True,
            possible_values=TaskType,
        )
        self.importance_field = self.add_field_widget(
            "Importance",
            lambda task: task.importance,
            is_task_field=True,
            possible_values=ItemImportance,
        )
        self.size_field = self.add_field_widget(
            "Size",
            lambda task: task.size,
            is_task_field=True,
            possible_values=ItemSize,
        )
        self.is_tracked_field = self.add_field_widget(
            "Track",
            lambda task: task.is_tracked,
            is_task_field=True,
            is_bool_field=True,
        )

        # Tracker widget
        is_task = tree_manager.is_task(task_item)
        self.tracking_widget = TaskTrackingWidget(
            task_item if is_task else None
        )
        self.task_widgets_layout.addWidget(self.tracking_widget)
        self.is_tracked_field.widget.clicked.connect(
            self.tracking_widget.setVisible
        )

        # Hide parts of ui as needed
        if not is_task:
            self.task_widgets_box.hide()

        self.on_tree_view_changed()

    def add_field_widget(
            self,
            name,
            value_getter,
            is_task_field=False,
            is_bool_field=False,
            possible_values=None,
            custom_widget=None,
            layout=None):
        """Add field widget to set values for an attribute.

        Args:
            name (str): the name of the field.
            value_getter (function): function to get the value of the attribute
                from a task item.
            is_task_field (bool): if True, this field only applies to tasks.
            is_bool_field (bool): if True, this field is boolean and needs a
                checkbox.
            possible_values (iterable or None): possible values for the field,
                if they're restricted.
            customWidget (QWidget or None): if given, use this widget for the
                field widget. Otherwise, we make a widget using the
                is_bool_field and possible_values args.
            layout (QBoxLayout or None): layout to add to, if given, otherwise
                work this out from is_task_field arg.

        Returns:
            (AttributeWidgetWrapper): the attribute widget.
        """
        ti = self.tree_item
        set_default = (ti is not None)
        if is_task_field:
            layout = fallback_value(layout, self.task_widgets_layout)
            widget_list = self.task_field_widgets
            set_default = (set_default and self._tree_manager.is_task(ti))
        else:
            layout = fallback_value(layout, self.main_layout)
            widget_list = self.general_field_widgets
        default = value_getter(ti) if set_default else None

        if custom_widget is not None:
            widget = layout_utils.add_field_widget(
                layout,
                name,
                custom_widget,
            )
        elif is_bool_field:
            widget = layout_utils.add_checkbox_field(
                layout,
                name,
                default=default,
            )
        elif possible_values is None:
            widget = layout_utils.add_text_field(
                layout,
                name,
                default=default,
            )
        else:
            widget = layout_utils.add_combobox_field(
                layout,
                name,
                possible_values,
                default=default,
            )
        widget_wrapper = AttributeWidgetWrapper(widget, name, value_getter)
        widget_list.append(widget_wrapper)
        return widget_wrapper

    def _iter_widget_wrappers(self, task_item):
        """Iter attribute widgets for a given task.

        Args:
            task_item (BaseTaskItem): the task item to iterate over.

        Yields:
            (AttributeWidgetWrapper): the attribute widget wrapper instance.
        """
        for widget_wrapper in self.general_field_widgets:
            yield widget_wrapper
        if self._tree_manager.is_task(task_item):
            for widget_wrapper in self.task_field_widgets:
                yield widget_wrapper

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
            for wrapper in self._iter_widget_wrappers(old_task):
                dialog_value = wrapper.get_value()
                if dialog_value != wrapper.get_attribute_value(old_task):
                    task_dict[wrapper.name] = dialog_value

        # set new values (from cache or existing attributes)
        if self.tree_item:
            new_task = self.tree_item
            task_dict = self.values_cache.get(new_task, {})
            self.task_label.setText(new_task.path)
            for widget_wrapper in self._iter_widget_wrappers(new_task):
                item_value = widget_wrapper.get_attribute_value(new_task)
                new_value = task_dict.get(widget_wrapper.name, item_value)
                if widget_wrapper.get_value() != new_value:
                    widget_wrapper.set_value(new_value)

            # update visibilities and enabled properties
            is_task = self._tree_manager.is_task(new_task)
            self.task_widgets_box.setVisible(is_task)
            self.tracking_widget.setVisible(
                is_task and task_dict.get(
                    self.is_tracked_field.name,
                    self.is_tracked_field.get_attribute_value(new_task),
                )
            )

            # if parent is multi, children are automatically tracked
            # TODO: do we even want to keep multi-type? it's a bit weird
            if (is_task
                    and new_task.parent is not None
                    and self._tree_manager.is_tracked_task(new_task.parent)
                    and new_task.parent.value_type == TrackedValueType.MULTI):
                self.is_tracked_field.widget.setEnabled(False)
                self.tracking_widget.setVisible(True)
            else:
                self.is_tracked_field.widget.setEnabled(True)

            # update tracking widget
            if is_task:
                self.tracking_widget.update_task(new_task)

    # TODO: for this dialog, we should add an accept and don't close option
    def accept_and_close(self):
        """Run add or modify scheduled item edit.

        Called when user clicks accept.
        """
        success = self._tree_manager.modify_task_item(
            self.tree_item,
            name=self.name_field.get_value(),
            display_name=self.display_name_field.get_value(),
            type=TaskType(self.type_field.get_value()),
            size=ItemSize(self.size_field.get_value()),
            importance=ItemImportance(self.importance_field.get_value()),
            is_tracked=self.is_tracked_field.get_value(),
            value_type=self.tracking_widget.get_value_type(),
        )

        if self._tree_manager.is_task(self.tree_item):
            # TODO: get_target_at_date(Date.now) should be its own task method
            old_taget = self.tree_item.get_target_at_date(Date.now())
            new_target = self.tracking_widget.get_target()
            if old_taget != new_target and new_target is not None:
                # TODO: use NoTarget to allow removing when new_target is None
                self._tree_manager.update_task(
                    self.tree_item,
                    date_time=Date.now(),
                    target=new_target,
                    ignore_status=True,
                    stack=success,
                )
        super(TaskItemDialog, self).accept_and_close()

    def delete_item_and_close(self):
        """Run remove scheduled item edit.

        Called when user clicks delete.
        """
        self._tree_manager.remove_item(self.tree_item)
        super(TaskItemDialog, self).delete_item_and_close()
