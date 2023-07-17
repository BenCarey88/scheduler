"""Task dialog for editing tasks and task categories."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.enums import ItemImportance, ItemSize
from scheduler.api.tree.task import TaskType

from scheduler.ui import layout_utils, utils
from .item_dialog import ItemDialog


class AttributeWidgetWrapper(object):
    """Wrapper around a widget that represents a task attribute."""
    def __init__(self, attr_name, widget, value_getter):
        """Initialize class instance.

        Args:
            attr_name (str): name of attribute.
            widget (QWidget): widget representing the task.
            value_getter (function): a method for getting the value of this
                attribute from a given task.
        """
        self.name = attr_name
        self.widget = widget
        self._value_getter = value_getter

    def get_value(self):
        """Get current value of widget.

        Returns:
            (str): current value of widget.
        """
        return utils.get_widget_value(self.widget)

    def set_value(self, value):
        """Set current value of widget.

        Args:
            value (str): value to set for widget.
        """
        return utils.set_widget_value(self.widget, value)
    
    def get_item_value(self, task_item):
        """Get current value of task item attribute.

        Args:
            task_item (BaseTaskItem): the task item to check.

        Returns:
            (str): current value of item.
        """
        return self._value_getter(task_item)


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

        self.task_widgets_box = QtWidgets.QFrame()
        self.task_widgets_layout = QtWidgets.QVBoxLayout()
        self.task_widgets_layout.setContentsMargins(0, 0, 0, 0)
        self.task_widgets_box.setLayout(self.task_widgets_layout)
        self.main_layout.addWidget(self.task_widgets_box)
        is_task = tree_manager.is_task(task_item)
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
        if not is_task:
            self.task_widgets_box.setHidden(True)

        self.on_tree_view_changed()

    def add_field_widget(
            self,
            name,
            value_getter,
            is_task_field=False,
            possible_values=None):
        """Add field widget to set values for an attribute.

        Args:
            name (str): the name of the field.
            value_getter (function): function to get the value of the attribute
                from a task item.
            is_task_field (bool): if True, this field only applies to tasks.
            possible_values (iterable or None): possible values for the field,
                if they're restricted.

        Returns:
            (AttributeWidgetWrapper): the attribute widget.
        """
        ti = self.tree_item
        set_default = (ti is not None)
        if is_task_field:
            layout = self.task_widgets_layout
            widget_list = self.task_field_widgets
            set_default = (set_default and self._tree_manager.is_task(ti))
        else:
            layout = self.main_layout
            widget_list = self.general_field_widgets
        default = value_getter(ti) if set_default else None

        if possible_values is None:
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
        widget_wrapper = AttributeWidgetWrapper(name, widget, value_getter)
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
            for widget_wrapper in self._iter_widget_wrappers(old_task):
                dialog_value = widget_wrapper.get_value()
                if dialog_value != widget_wrapper.get_item_value(old_task):
                    task_dict[widget_wrapper.name] = dialog_value

        # set new values (from cache or existing attributes)
        if self.tree_item:
            new_task = self.tree_item
            task_dict = self.values_cache.get(new_task, {})
            self.task_label.setText(new_task.path)
            for widget_wrapper in self._iter_widget_wrappers(new_task):
                item_value = widget_wrapper.get_item_value(new_task)
                new_value = task_dict.get(widget_wrapper.name, item_value)
                if widget_wrapper.get_value() != new_value:
                    widget_wrapper.set_value(new_value)
            self.task_widgets_box.setHidden(
                not self._tree_manager.is_task(new_task)
            )

    # TODO: for this dialog, we should add an accept and don't close option
    def accept_and_close(self):
        """Run add or modify scheduled item edit.

        Called when user clicks accept.
        """
        self._tree_manager.modify_task_item(
            self.tree_item,
            name=self.name_field.get_value(),
            display_name=self.display_name_field.get_value(),
            type=TaskType(self.type_field.get_value()),
            size=ItemSize(self.size_field.get_value()),
            importance=ItemImportance(self.importance_field.get_value()),
        )
        super(TaskItemDialog, self).accept_and_close()

    def delete_item_and_close(self):
        """Run remove scheduled item edit.

        Called when user clicks delete.
        """
        self._tree_manager.remove_item(self.tree_item)
        super(TaskItemDialog, self).delete_item_and_close()
