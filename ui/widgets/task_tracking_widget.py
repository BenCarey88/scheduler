"""Task tracking widget for use in task dialog."""


from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common import Date
from scheduler.api.enums import ItemStatus, TimePeriod, TrackedValueType
from scheduler.api.tracker.target import TargetOperator, TrackerTarget

from scheduler.ui import layout_utils, utils


class TaskTrackingWidget(QtWidgets.QFrame):
    """Widget to define task tracking properties."""
    def __init__(self, task=None, parent=None):
        """Initialise widget.

        Args:
            task (Task or None): task item that this widget is editing.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(TaskTrackingWidget, self).__init__(parent=parent)
        self.setFrameShape(self.Shape.StyledPanel)
        self.setLineWidth(1)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.task = task

        # values_cache stores field values by task. Target values for each task
        # are stored in a subdict keyed by value type so they can vary by both
        # task and value type
        self.values_cache = {}

        self.value_type_field = layout_utils.add_combobox_field(
            self.main_layout,
            "Value Type",
            TrackedValueType,
            wrap=True,
            attribute_getter=(lambda task: task.value_type),
            default_object=task,
        )
        self.set_target_field = layout_utils.add_checkbox_field(
            self.main_layout,
            "Set Target",
            wrap=True,
            attribute_getter=(
                lambda task: (task.get_target_at_date(Date.now()) is not None)
            ),
            default_object=task,
        )
        self.target_field = utils.AttributeWidgetWrapper(
            TargetWidget(task=task),
            "Target",
            attribute_getter=(lambda t: t.get_target_at_date(Date.now())),
            default_object=task,
            add_to_layout=self.main_layout,
        )

        # Connections
        self.set_target_field.widget.clicked.connect(
            self.target_field.widget.setVisible
        )
        self.value_type_field.widget.currentTextChanged.connect(
            self.update_target_field_from_value_type
        )

        # Hide parts of ui as needed
        if task is not None:
            target = task.get_target_at_date(Date.now())
            if target is not None:
                self.target_field.widget.set_value(target)
            else:
                self.target_field.widget.hide()
            self.update_target_field_from_value_type(task.value_type)

    def get_target(self):
        """Get target defined by target widget.

        Returns:
            (TrackerTarget or None): target, if one is defined.
        """
        if not self.set_target_field.get_value():
            return None
        return self.target_field.get_value()
    
    def get_value_type(self):
        """Get value type defined by widget.

        Returns:
            (TrackedValueType): value type.
        """
        return TrackedValueType(self.value_type_field.get_value())

    def update_task(self, new_task):
        """Update to new task item.

        Args:
            new_task (Task): new task to update to.
        """
        # cache old values
        if self.task is not None:
            task_cache = self.values_cache.setdefault(self.task, {})
            value_type = self.value_type_field.get_value()
            set_target = self.set_target_field.get_value()
            target = self.target_field.get_value()

            task_cache[self.value_type_field.name] = value_type
            task_cache[self.set_target_field.name] = set_target
            target_cache = task_cache.setdefault(self.target_field.name, {})
            target_cache[value_type] = target

        # set new values (from cache or existing attributes)
        self.task = new_task
        task_cache = self.values_cache.setdefault(new_task, {})
        value_type = task_cache.get(
            self.value_type_field.name,
            self.value_type_field.get_attribute_value(new_task),
        )
        set_target = task_cache.get(
            self.set_target_field.name,
            self.set_target_field.get_attribute_value(new_task),
        )

        with utils.suppress_signals(self.value_type_field.widget):
            self.value_type_field.set_value(value_type)
        with utils.suppress_signals(self.set_target_field.widget):
            self.set_target_field.set_value(set_target)
        self.update_target_field_from_value_type(value_type, cache=False)

    def update_target_field_from_value_type(self, value_type, cache=True):
        """Update target fields based on value type.

        Args:
            value_type (str): new value type being set. Currently we cannot
                set targets on a none-type, multi-type or string-type.
            cache (bool): if True, update values cache before updating.
        """
        if self.task is None:
            # can't update with empty task (widget is invisible anyway)
            return

        # TODO: it's crucial that this goes at the start of this function or
        # otherwise things don't update right - work out why
        self.target_field.widget.update_value_type(value_type, self.task)

        # cache old values
        target_cache = {}
        if self.task is not None:
            task_cache = self.values_cache.setdefault(self.task, {})
            target_cache = task_cache.setdefault(self.target_field.name, {})
            if cache:
                old_value_type = self.value_type_field.get_value()
                target_cache[old_value_type] = self.target_field.get_value()

        # enable/disable targets
        untargetable_values = (
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
        target = target_cache.get(
            value_type,
            self.target_field.get_attribute_value(self.task),
        )

        if target is not None and target.value_type == value_type:
            self.target_field.set_value(target)


class ValueWidgetWrapper(utils.ValueWidgetWrapper):
    """Extension of ValueWidgetWrapper class for TargetWidget class."""
    @classmethod
    def from_value_type(cls, value_type):
        """Get wrapped value widget from value type.

        Args:
            value_type (TrackedValueType): value type to check.

        Returns:
            (ValueWidgetWrapper): wrapped widget for value.
        """
        widget_class = {
            TrackedValueType.STATUS: QtWidgets.QComboBox,
            TrackedValueType.TIME: QtWidgets.QTimeEdit,
            TrackedValueType.STRING: QtWidgets.QLineEdit,
            TrackedValueType.INT: QtWidgets.QSpinBox,
            TrackedValueType.COMPLETIONS: QtWidgets.QSpinBox,
            TrackedValueType.FLOAT: QtWidgets.QDoubleSpinBox,
        }.get(value_type, None)
        if widget_class is None:
            return cls(
                QtWidgets.QWidget(),
                lambda : None,
                lambda _: None,
            )
        widget = widget_class()
        if value_type == TrackedValueType.STATUS:
            widget.addItems(ItemStatus)
        return cls(widget)


# TODO: update to allow composite targets and different time_periods.
class TargetWidget(utils.BaseValueWidget):
    """Widget defining a tracker target."""
    def __init__(
            self,
            task=None,
            value_type=None,
            target_operator=None,
            target_value=None,
            time_period=None,
            parent=None):
        """Initialise widget.

        Args:
            task (Task or None): task we're editing.
            value_type (TrackedValueType or None): tracked value type of
                associated task, if given.
            target_operator (TargetOperator or None): operator to use with the
                the target value, if given.
            target_value (variant or None): target value, if given.
            time_period ()
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(TargetWidget, self).__init__(parent=parent)
        self.value_type = value_type or TrackedValueType.STATUS
        self.main_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.main_layout)
        self.task = task

        # operator
        self.operator_combo_box = QtWidgets.QComboBox()
        self.operator_combo_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.operator_combo_box.addItems(TargetOperator)
        self.main_layout.addWidget(self.operator_combo_box)

        # value
        self.value_field = None # this gets set below in update_value_type
        self.value_widget_stack = QtWidgets.QStackedWidget()
        self.value_widget_stack.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.main_layout.addWidget(self.value_widget_stack)

        # time period
        self.time_period_combo_box = QtWidgets.QComboBox()
        self.time_period_combo_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.time_period_combo_box.addItems((
            TimePeriod.DAY.get_periodicity_string(),
            TimePeriod.WEEK.get_periodicity_string(),
        ))
        self.main_layout.addWidget(self.time_period_combo_box)

        # cache
        self.value_widgets_cache = {}
        self.operators_cache = {}
        self.time_periods_cache = {}

        # connections
        self.time_period_combo_box.currentTextChanged.connect(
            self.update_time_period
        )

        # set initial values
        self.update_value_type(value_type, cache=False)
        if target_operator is not None:
            self.operator_combo_box.setCurrentText(target_operator)
        if target_value is not None:
            self.value_field.set_value(target_value)
        if time_period is not None:
            self.time_period_combo_box.setCurrentText(
                time_period.get_periodicity_string()
            )

    def update_value_type(self, value_type, new_task=None, cache=True):
        """Update value_type and values widgets when value_type changes.

        Args:
            value_type (TrackedvalueType): the new value type.
            new_task (Task or None): new task, if given.
            cache (bool): if True, update cache for the comboboxes and
                set them from the cache after.
        """
        # cache operators and time period
        if cache and self.task is not None:
            operator_cache = self.operators_cache.setdefault(self.task, {})
            operator_cache[self.value_type] = (
                self.operator_combo_box.currentText()
            )
            periods_cache = self.time_periods_cache.setdefault(self.task, {})
            periods_cache[self.value_type] = (
                self.time_period_combo_box.currentText()
            )

        # cache and set value widget
        self.value_type = value_type
        if new_task is not None:
            self.task = new_task
        if self.task is None:
            # can't update if task is None (widget is invisible anyway)
            return
        task_widgets_cache = self.value_widgets_cache.setdefault(self.task, {})
        self.value_field = task_widgets_cache.get(value_type)
        if self.value_field is None:
            self.value_field = ValueWidgetWrapper.from_value_type(value_type)
            self.value_widget_stack.addWidget(self.value_field.widget)
            task_widgets_cache[value_type] = self.value_field
        self.value_widget_stack.setCurrentWidget(self.value_field.widget)

        # set time period and comboboxes from cache
        if cache and self.task is not None:
            operator_cache = self.operators_cache.setdefault(self.task, {})
            operator_str = operator_cache.get(self.value_type, None)
            if operator_str is not None:
                self.operator_combo_box.setCurrentText(operator_str)
            periods_cache = self.time_periods_cache.setdefault(self.task, {})
            time_period_str = periods_cache.get(self.value_type, None)
            if time_period_str is not None:
                self.time_period_combo_box.setCurrentText(time_period_str)

        # format and hide widgets as needed
        self.time_period_combo_box.setHidden(
            value_type in (TrackedValueType.TIME, TrackedValueType.STATUS)
        )
        self.update_time_period(self.time_period_combo_box.currentText())

    def update_time_period(self, time_period_str):
        """Update widgets based on new time period string.

        Args:
            time_period_str (str): new time period string in time period
                combobox.
        """
        if self.value_type == TrackedValueType.COMPLETIONS:
            if time_period_str == TimePeriod.DAY.get_periodicity_string():
                self.value_field.widget.setRange(0, 1)
            elif time_period_str == TimePeriod.WEEK.get_periodicity_string():
                self.value_field.widget.setRange(0, 7)

    def get_value(self):
        """Get target defined by widget.

        Returns:
            (TrackerTarget): the defined target.
        """
        return TrackerTarget(
            TimePeriod.from_periodicity_string(
                self.time_period_combo_box.currentText()
            ),
            TrackedValueType(self.value_type),
            TargetOperator(self.operator_combo_box.currentText()),
            self.value_field.get_value(),
        )

    def set_value(self, target=None):
        """Set value of widget to given target.

        Args:
            target (TrackerTarget or None): target to represent in widget ui.
                Allows setting to None as well, which just clears the value
                widget.
        """
        if target is None:
            return self.update_value_type(TrackedValueType.STATUS)
        self.update_value_type(target.value_type)
        self.operator_combo_box.setCurrentText(target.target_operator)
        self.value_field.set_value(target.target_value)
        self.time_period_combo_box.setCurrentText(
            target.time_period.get_periodicity_string()
        )
