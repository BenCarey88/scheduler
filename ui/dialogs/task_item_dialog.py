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
from scheduler.api.tracker.target import TargetOperator, TrackerTarget
from scheduler.api.tree.task import TaskType
from scheduler.api.utils import fallback_value

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


# TODO: this is copied from filter_dialog class, maybe break out into
# separate utility class
# although from_value_type method is of course specific to this module
# TODO: maybe this one should be combined with the above class anyway
class ValueWidgetWrapper(object):
    """Wrapper around a value widget."""
    def __init__(self, value_widget, getter, setter):
        """Initialize struct.

        Args:
            value_widget (QtWidgets.QWidget): widget for a field value.
            getter (function): function to return the value.
            setter (function): function to set the value.
        """
        self.widget = value_widget
        self.get_value = getter
        self.set_value = setter

    @classmethod
    def from_value_type(cls, value_type):
        """Get wrapped value widget from value type.

        Args:
            value_type (TrackedValueType): value type to check.

        Returns:
            (ValueWidgetWrapper): wrapped widget for value.
        """
        widget_class = {
            TrackedValueType.TIME: QtWidgets.QTimeEdit,
            TrackedValueType.STRING: QtWidgets.QLineEdit,
            TrackedValueType.INT: QtWidgets.QSpinBox,
            TrackedValueType.FLOAT: QtWidgets.QDoubleSpinBox,
        }.get(value_type, None)
        if widget_class is None:
            return cls(
                QtWidgets.QComboBox(),
                lambda : None,
                lambda _: None,
            )

        widget = widget_class()
        return cls(
            widget,
            partial(utils.get_widget_value, widget),
            partial(utils.set_widget_value, widget),
        )


# TODO: update to allow composite targets too.
class TrackerTargetWidget(utils.BaseValueWidget):
    """Widget defining a tracker target."""
    def __init__(
            self,
            value_type=None,
            target_operator=None,
            target_value=None,
            parent=None):
        """Initialise widget.

        Args:
            value_type (TrackedValueType or None): tracked value type of
                associated task, if given.
            target_operator (TargetOperator or None): operator to use with the
                the target value, if given.
            target_value (variant or None): target value, if given.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(TrackerTargetWidget, self).__init__(parent=parent)
        self.value_type = value_type or TrackedValueType.NONE
        self.main_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.main_layout)

        self.operator_combo_box = QtWidgets.QComboBox()
        self.operator_combo_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.operator_combo_box.addItems(TargetOperator)
        self.main_layout.addWidget(self.operator_combo_box)

        self.value_widget_wrapper = ValueWidgetWrapper.from_value_type(
            TrackedValueType.NONE
        )
        self.value_widget_stack = QtWidgets.QStackedWidget()
        self.value_widget_stack.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.value_widget_stack.addWidget(self.value_widget_wrapper.widget)
        self.value_widgets_cache = {
            TrackedValueType.NONE: self.value_widget_wrapper
        }
        self.main_layout.addWidget(self.value_widget_stack)

        # set initial values
        self.update_value_type(value_type)
        if target_operator is not None:
            self.operator_combo_box.setCurrentText(target_operator)
        if target_value is not None:
            self.value_widget_wrapper.set_value(target_value)

    def update_value_type(self, value_type):
        """Update value_type and values widget when value_type changes.

        Args:
            value_type (TrackedvalueType): the new value type.
            task (Task or None): task, if given.
        """
        self.value_type = value_type
        self.value_widget_wrapper = self.value_widgets_cache.get(
            value_type
        )
        if self.value_widget_wrapper is None:
            self.value_widget_wrapper = ValueWidgetWrapper.from_value_type(
                value_type
            )
            self.value_widget_stack.addWidget(self.value_widget_wrapper.widget)
            self.value_widgets_cache[value_type] = (
                self.value_widget_wrapper
            )
        self.value_widget_stack.setCurrentWidget(
            self.value_widget_wrapper.widget
        )

    def get_value(self):
        """Get target defined by widget.

        Returns:
            (TrackerTarget): the defined target.
        """
        return TrackerTarget(
            TimePeriod.DAY, # this is the only time period option for now
            TrackedValueType(self.value_type),
            TargetOperator(self.operator_combo_box.currentText()),
            self.value_widget_wrapper.get_value(),
        )

    def set_value(self, target=None):
        """Set value of widget to given target.

        Args:
            target (TrackerTarget or None): target to represent in widget ui.
                Allows setting to None as well, which just clears the value
                widget.
        """
        if target is None:
            return self.update_value_type(TrackedValueType.NONE)
        self.update_value_type(target.value_type)
        self.operator_combo_box.setCurrentText(target.target_operator)
        self.value_widget_wrapper.set_value(target.target_value)


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

        # Tracker box
        self.tracking_box = QtWidgets.QFrame()
        self.tracking_box.setFrameShape(self.tracking_box.Shape.StyledPanel)
        self.tracking_box.setLineWidth(1)
        self.tracking_layout = QtWidgets.QVBoxLayout()
        self.tracking_box.setLayout(self.tracking_layout)
        self.task_widgets_layout.addWidget(self.tracking_box)

        # Tracker fields
        self.tracker_value_types_cache = {}
        self.value_type_field = self.add_field_widget(
            "Value Type",
            lambda task: task.value_type,
            is_task_field=True,
            possible_values=TrackedValueType,
            layout=self.tracking_layout,
        )
        self.set_target_field = self.add_field_widget(
            "Set Target",
            lambda task: (task.get_target_at_date(Date.now()) is not None),
            is_task_field=True,
            is_bool_field=True,
            layout=self.tracking_layout,
        )
        self.target_field = AttributeWidgetWrapper(
            "Target",
            TrackerTargetWidget(),
            lambda task: task.get_target_at_date(Date.now()),
        )
        self.tracking_layout.addWidget(self.target_field.widget)
        self.task_field_widgets.append(self.target_field)

        # Connections
        self.is_tracked_field.widget.clicked.connect(
            self.tracking_box.setVisible
        )
        # self.value_type_field.widget.currentTextChanged.connect(
        #     self.target_field.widget.update_value_type
        # )
        self.set_target_field.widget.clicked.connect(
            self.target_field.widget.setVisible
        )
        self.value_type_field.widget.currentTextChanged.connect(
            self.update_target_fields_from_value_type
        )

        # Hide parts of ui as needed
        is_task = tree_manager.is_task(task_item)
        if not is_task:
            self.task_widgets_box.hide()
        else:
            is_tracked = self.is_tracked_field.get_item_value(task_item)
            if not is_tracked:
                self.tracking_box.hide()
            target = task_item.get_target_at_date(Date.now())
            if target is not None:
                self.target_field.widget.set_value(target)
            else:
                self.target_field.widget.update_value_type(
                    task_item.value_type
                )
                self.target_field.widget.hide()
            self.update_target_fields_from_value_type(task_item.value_type)

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

            # update visibilities and enabled properties
            is_task = self._tree_manager.is_task(new_task)
            self.task_widgets_box.setVisible(is_task)
            self.tracking_box.setVisible(
                is_task and task_dict.get(
                    self.is_tracked_field.name,
                    self.is_tracked_field.get_item_value(new_task),
                )
            )
            self.target_field.widget.setVisible(
                is_task and task_dict.get(
                    self.set_target_field.name,
                    self.set_target_field.get_item_value(new_task),
                )
            )
            # if parent is multi, children are automatically tracked
            # TODO: do we even want to keep multi-type? it's a but weird
            if (is_task
                    and new_task.parent is not None
                    and self._tree_manager.is_task(new_task.parent)
                    and new_task.parent.value_type == TrackedValueType.MULTI):
                self.is_tracked_field.widget.setEnabled(False)
                self.tracking_box.setVisible(True)
            else:
                self.is_tracked_field.widget.setEnabled(True)
            if is_task:
                self.update_target_fields_from_value_type(
                    self.value_type_field.get_value()
                )

    # TODO: due to the specific interplay between value_type and target
    # I think it would probably be easier if all the tracking stuff were
    # its own distinct widget class - has gotten very messy now
    def update_target_fields_from_value_type(self, value_type):
        """Update target fields based on value type.

        Args:
            value_type (str): new value type being set. Currently we cannot
                set targets on a none-type, multi-type or string-type
        """
        # TODO: it's crucial that this goes before the line after or otherwise
        # things don't update right - work out why
        # or better yet, majorly overhual this whole page, because it's
        # got really gross now! A separate task_tracking_widget has got to be
        # the way to go.
        self.target_field.widget.update_value_type(value_type)

        # cache old values
        old_value_type = self.value_type_field.get_value()
        self.tracker_value_types_cache[old_value_type] = (
            self.target_field.get_value()
        )

        # enable/disable targets
        untargetable_values = (
            TrackedValueType.NONE,
            TrackedValueType.MULTI,
            TrackedValueType.STRING,
        )
        if value_type in untargetable_values:
            self.set_target_field.widget.setEnabled(False)
            self.target_field.widget.hide()
            return
        self.set_target_field.widget.setEnabled(True)
        self.target_field.widget.setVisible(self.set_target_field.get_value())

        # set new values from cache
        self.target_field.set_value(
            self.tracker_value_types_cache.get(value_type, None)
        )

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
            value_type=TrackedValueType(self.value_type_field.get_value()),
        )

        if self._tree_manager.is_task(self.tree_item):
            # TODO: get_target_at_date(Date.now) should be its own task method
            old_taget = self.tree_item.get_target_at_date(Date.now())
            new_target = (
                None if not self.set_target_field.get_value() else
                self.target_field.get_value()
            )
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
