"""Filter dialog for creating new filters."""

from ast import operator
from collections import OrderedDict
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import (
    BaseDateTimeWrapper,
    Date,
    DateTime,
    Time,
)
from scheduler.api.filter import FieldFilter, FilterOperator
from scheduler.api.filter.tree_filters import (
    NoFilter,
    CompositeTreeFilter,
    TaskPathFilter,
    TaskStatusFilter,
    TaskTypeFilter,
)
from scheduler.api.tree.task import TaskStatus, TaskType
from scheduler.api.utils import fallback_value, OrderedEnum

from scheduler.ui.utils import set_style, simple_message_dialog


class FilterDialogError(Exception):
    """Base exception for filter dialog."""


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


class FilterFieldData(object):
    """Class defining a filter field."""
    def __init__(self, name, filter_class, values=None, value_type=str):
        """Initialise filter field.

        Args:
            name (str): name of field.
            filter_class (class): the corresponding filter class.
            values (list(str) or None): list of possible predefined values
                for this field. If not given, it is assumed that the field's
                values are unrestricted.
            value_type (type): type of value. This defaults to string.
        """
        self.name = name
        self.filter_class = filter_class
        self.values = values
        self.value_type = value_type
        self.operators = self.get_operators()

    def get_operators(self):
        """Get allowed operators for field.

        Returns:
            (list(FilterOperator)): list of allowed operators.
        """
        if issubclass(self.value_type, str):
            return FilterOperator.BASE_OPS + FilterOperator.STRING_OPS
        elif issubclass(self.value_type, float, int, BaseDateTimeWrapper):
            return FilterOperator.BASE_OPS + FilterOperator.MATH_OPS
        else:
            raise FilterDialogError(
                "Value type {0} is not supported for filter fields".format(
                    self.value_type.__name__
                )
            )

    def get_value_widget_wrapper(self, operator):
        """Get widget used to edit this field's value, for the given operator.

        Args:
            operator (FilterOperator) operator to edit with.

        Returns:
            (ValueWidgetWrapper): widget to edit this field.
        """
        if (operator == FilterOperator.MATCHES
                and issubclass(self.value_type, str)):
            widget = QtWidgets.QLineEdit()
            return ValueWidgetWrapper(widget, widget.text, widget.setText)
        elif self.values is None:
            if issubclass(self.value_type, Date):
                widget = QtWidgets.QDateEdit()
                return ValueWidgetWrapper(widget, widget.date, widget.setDate)
            if issubclass(self.value_type, DateTime):
                widget = QtWidgets.QDateTimeEdit()
                return ValueWidgetWrapper(
                    widget,
                    widget.dateTime,
                    widget.setDateTime,
                )
            if issubclass(self.value_type, Time):
                widget = QtWidgets.QTimeEdit()
                return ValueWidgetWrapper(widget, widget.time, widget.setTime)
            if issubclass(self.value_type, str):
                widget = QtWidgets.QLineEdit()
                return ValueWidgetWrapper(widget, widget.text, widget.setText)
        else:
            widget = QtWidgets.QComboBox()
            widget.addItems(self.values)
            return ValueWidgetWrapper(
                widget,
                widget.currentText,
                widget.setCurrentText
            )
        raise FilterDialogError(
            "Cannot get widget for field {0} with operator of type {1}"
            "".format(self.name, operator)
        )


class FilterField(OrderedEnum):
    """Filter fields"""
    STATUS = FilterFieldData("Status", TaskStatusFilter, TaskStatus.VALUES)
    TYPE = FilterFieldData("Type", TaskTypeFilter, TaskType.VALUES)
    PATH = FilterFieldData("Path", TaskPathFilter)

    VALUES = [STATUS, TYPE, PATH]
    VALUES_DICT = OrderedDict([(field.name, field) for field in VALUES])
    FIELD_NAMES = list(VALUES_DICT.keys())


class FieldWidget(QtWidgets.QWidget):
    """Widget defining a field in the dialog."""
    def __init__(
            self,
            field=None,
            field_operator=None,
            field_value=None,
            parent=None):
        """Initialise widget.

        Args:
            field (FilterField or None): the field we're filtering for, if
                given.
            field_operator (FilterOperator or None): operator to apply to
                field, if given.
            field_value (variant or None): value to use with operator, if given.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(FieldWidget, self).__init__(parent=parent)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.main_layout)

        self.field_combo_box = QtWidgets.QComboBox()
        self.field_combo_box.addItems([""] + FilterField.FIELD_NAMES)
        self.main_layout.addWidget(self.field_combo_box)

        self.operator_combo_box = QtWidgets.QComboBox()
        self.main_layout.addWidget(self.operator_combo_box)

        self.value_widget_wrapper = self._default_value_widget_wrapper()
        self.main_layout.addWidget(self.value_widget)

        self.update_operators()
        self.update_values()
        self.field_combo_box.currentTextChanged.connect(
            self.update_operators
        )
        self.operator_combo_box.currentTextChanged.connect(
            self.update_values
        )

        # set initial values
        if field is not None:
            self.field_combo_box.setCurrentText(field.name)
        if field_operator is not None:
            self.operator_combo_box.setCurrentText(field_operator)
        if field_value is not None:
            self.value_widget_wrapper.set_value(field_value)

    def _default_value_widget_wrapper(self):
        """Get empty stand-in widget to use as values widget.

        Returns:
            (ValueWidgetWrapper): default values widget.
        """
        return ValueWidgetWrapper(
            QtWidgets.QComboBox(),
            lambda : None,
            lambda _: None,
        )

    def update_operators(self, field_name=None):
        """Update allowed operators in combobox.

        Args:
            field_name (str): the current field.
        """
        field_name = fallback_value(
            field_name,
            self.field_combo_box.currentText()
        )
        field = FilterField.VALUES_DICT.get(field_name)
        if field is None:
            self.operator_combo_box.setModel(
                QtCore.QStringListModel([])
            )
        else:
            self.operator_combo_box.setModel(
                QtCore.QStringListModel(field.operators)
            )

    def update_values(self, operator=None):
        """Update values widget.

        Args:
            operator (str): the current operator.
        """
        self.value_widget.deleteLater()
        field_name = self.field_combo_box.currentText()
        field = FilterField.VALUES_DICT.get(field_name)
        if not field:
            self.value_widget_wrapper = self._default_value_widget_wrapper()
            self.main_layout.addWidget(self.value_widget)
            return
        operator = fallback_value(
            operator,
            self.operator_combo_box.currentText(),
        )
        self.value_widget_wrapper = field.get_value_widget_wrapper(operator)
        self.main_layout.addWidget(self.value_widget)

    @property
    def value_widget(self):
        """Get the values widget for this field widget.

        Returns:
            (QtWidgets.QWidget): the value widget.
        """
        return self.value_widget_wrapper.widget

    @property
    def operator(self):
        """Get filter operator defined by this widget.

        Returns:
            (FilterOperator or None): filter operator if found.
        """
        return self.operator_combo_box.currentText() or None

    @property
    def filter(self):
        """Get filter defined by this widget.

        Returns:
            (BaseFilter): filter that this dialog defines.
        """
        field_name = self.field_combo_box.currentText()
        field = FilterField.VALUES_DICT.get(field_name)
        operator = self.operator_combo_box.currentText() or None
        value = self.value_widget_wrapper.get_value()
        if field is None or operator is None or value is None:
            return NoFilter()
        return field.filter_class(operator, value)

    @classmethod
    def from_filter(cls, filter_=None):
        """Initialize class from filter.

        Args:
            filter_ (CompositeTreeFilter or None): filter to initialize from.

        Returns:
            (FilterGroupWidget): class instance.
        """
        if not isinstance(filter_, FieldFilter):
            return cls()
        for field in FilterField.VALUES:
            if isinstance(filter_, field.filter_class):
                break
        else:
            return cls()
        return cls(field, filter_.field_operator, filter_.field_value)


class FilterGroupWidget(QtWidgets.QFrame):
    """Widget defining a grouping of different filters."""
    def __init__(
            self,
            subfilters=None,
            composition_operator=None,
            parent=None):
        """Initialize widget.

        Args:
            subfilters_list (list(BaseFilter) or None): list of subfilters.
            composition_operator (str or None): filter composition operator
                (must be AND or OR). If not given, default to OR.
            parent (QtWidgets.QWidget): parent, if given.
        """
        super(FilterGroupWidget, self).__init__(parent=parent)
        self.subfilters = subfilters or []
        self.composition_operator = (
            composition_operator or CompositeTreeFilter.OR
        )
        self.setFrameShape(self.Shape.Box)

        # all layouts
        self.main_layout = QtWidgets.QVBoxLayout()
        operator_layout = QtWidgets.QHBoxLayout()
        self.filters_layout = QtWidgets.QVBoxLayout()
        add_button_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(operator_layout)
        self.main_layout.addLayout(self.filters_layout)
        self.main_layout.addLayout(add_button_layout)
        self.setLayout(self.main_layout)

        # operator layout
        operator_layout.addStretch()
        operator_picker = QtWidgets.QComboBox()
        operator_picker.addItems(
            [CompositeTreeFilter.OR, CompositeTreeFilter.AND]
        )
        operator_picker.setCurrentText(self.composition_operator)
        operator_picker.currentTextChanged.connect(
            self.update_composition_operator
        )
        operator_layout.addWidget(operator_picker)

        # add button layout
        add_button = QtWidgets.QToolButton()
        add_button.setText("+")
        add_group_button = QtWidgets.QToolButton()
        add_group_button.setText("[+]")
        add_button.clicked.connect(self.add_filter_widget)
        add_group_button.clicked.connect(
            partial(self.add_filter_widget, make_group=True)
        )
        add_button_layout.addStretch()
        add_button_layout.addWidget(add_button)
        add_button_layout.addWidget(add_group_button)
        add_button_layout.addStretch()

        # filters layout
        self.filter_widgets = []
        self.delete_buttons = []
        self.filter_widget_layouts = []
        self.label_layouts = []
        self.operator_labels = []
        for filter_ in self.subfilters:
            self.add_filter_widget(filter_)
        # if not self.subfilters:
        #     self.add_filter_widget()

    def add_filter_widget(self, filter_=None, make_group=False):
        """Add filter widget.

        Args:
            filter_ (BaseFilter or None): if given, initialize field widget
                from this filter.
            group (bool): if True, add a group widget, else add a field widget.
                This is ignored if a filter is given, as in that case we work
                out what widget to add from the the filter.
        """
        # If some filter widgets already exist, add label
        if self.filter_widgets:
            label = QtWidgets.QLabel(self.composition_operator)
            label_layout = QtWidgets.QHBoxLayout()
            label_layout.addStretch()
            label_layout.addWidget(label)
            label_layout.addStretch()
            self.filters_layout.addLayout(label_layout)
            self.operator_labels.append(label)
            self.label_layouts.append(label_layout)

        # Add filter widget
        if isinstance(filter_, CompositeTreeFilter):
            filter_widget = FilterGroupWidget.from_filter(filter_)
        elif isinstance(filter_, FieldFilter):
            filter_widget = FieldWidget.from_filter(filter_)
        elif make_group:
            operator = CompositeTreeFilter.OR
            if self.composition_operator == CompositeTreeFilter.OR:
                # use opposite operator to current one
                operator = CompositeTreeFilter.AND
            filter_widget = FilterGroupWidget(composition_operator=operator)
        else:
            filter_widget = FieldWidget()
        filter_widget_layout = QtWidgets.QHBoxLayout()
        filter_widget_layout.addWidget(filter_widget)
        delete_button = QtWidgets.QToolButton()
        delete_button.setText("-")
        delete_button.clicked.connect(
            partial(self.remove_filter_widget, filter_widget)
        )
        self.delete_buttons.append(delete_button)
        filter_widget_layout.addWidget(delete_button)
        self.filter_widget_layouts.append(filter_widget_layout)
        self.filter_widgets.append(filter_widget)
        self.filters_layout.addLayout(filter_widget_layout)

    def remove_filter_widget(self, filter_widget):
        """Remove filter widget at given index.

        Args:
            filter_widget (FieldWidget): filter widget to remove.
        """
        if filter_widget not in self.filter_widgets:
            return
        index = self.filter_widgets.index(filter_widget)
        label_index = None
        if index == 0:
            if len(self.filter_widgets) > 1:
                label_index = 0
        else:
            label_index = index - 1

        # Delete objects and remove from lists
        if label_index is not None:
            for widget_list in (self.operator_labels, self.label_layouts):
                widget_list[label_index].deleteLater()
                del widget_list[label_index]
        for widget_list in (
                self.filter_widget_layouts,
                self.filter_widgets,
                self.delete_buttons):
            widget_list[index].deleteLater()
            del widget_list[index]

    def update_composition_operator(self, new_value):
        """Update composition operator type.

        Args:
            new_value (str): new composition operator.
        """
        self.composition_operator = new_value
        for label in self.operator_labels:
            label.setText(new_value)

    @property
    def filter(self):
        """Get filter defined by this dialog.

        Returns:
            (BaseFilter): filter that this dialog defines.
        """
        subfilters = [fw.filter for fw in self.filter_widgets if fw.filter]
        if len(subfilters) == 1:
            return subfilters[0]
        return CompositeTreeFilter(
            [fw.filter for fw in self.filter_widgets if fw.filter],
            self.composition_operator,
        )

    @classmethod
    def from_filter(cls, filter_=None):
        """Initialize class from filter.

        Args:
            filter_ (CompositeTreeFilter or None): filter to initialize from.

        Returns:
            (FilterGroupWidget): class instance.
        """
        if isinstance(filter_, CompositeTreeFilter):
            return cls(filter_.subfilters, filter_.composition_operator)
        if isinstance(filter_, FieldFilter):
            return cls([filter_], CompositeTreeFilter.OR)
        return cls()


class FilterDialog(QtWidgets.QDialog):
    """Dialog for creating and editing filters."""
    MINIMUM_WIDTH = 500

    def __init__(
            self,
            tree_manager,
            filter=None,
            parent=None):
        """Initialise dialog.

        Args:
            tree_manager (TreeManager): the task tree manager object.
            filter (BaseFilter or None): filter we're editing if given, else
                we're in create mode.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(FilterDialog, self).__init__(parent=parent)
        set_style(self, "filter_dialog.qss")
        self._tree_manager = tree_manager
        self.is_editor = (filter is not None)
        self.original_name = filter.name if filter is not None else None

        self.setWindowTitle("Filter Manager")
        flags = QtCore.Qt.WindowFlags(
            QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setMinimumWidth(self.MINIMUM_WIDTH)

        # all layouts
        main_layout = QtWidgets.QVBoxLayout()
        name_layout = QtWidgets.QHBoxLayout()
        buttons_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(name_layout)
        self.filter_group = FilterGroupWidget.from_filter(filter)
        main_layout.addWidget(self.filter_group)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

        # Name layout
        name_layout.addWidget(QtWidgets.QLabel("Name"))
        self.name_widget = QtWidgets.QLineEdit()
        if self.original_name:
            self.name_widget.setText(self.original_name)
        name_layout.addWidget(self.name_widget)

        if self.is_editor:
            self.delete_button = QtWidgets.QPushButton("Delete Filter")
            buttons_layout.addWidget(self.delete_button)
            self.delete_button.clicked.connect(self.delete_filter_and_close)
        accept_button_text = (
            "Edit Filter" if self.is_editor else "Add Filter"
        )
        self.accept_button = QtWidgets.QPushButton(accept_button_text)
        buttons_layout.addWidget(self.accept_button)
        self.accept_button.clicked.connect(self.accept_and_close)
        self.accept_button.setFocus(True)

    @property
    def filter(self):
        """Get filter defined by this dialog.

        Returns:
            (BaseFilter): filter that this dialog defines.
        """
        filter_ = self.filter_group.filter
        filter_.set_name(self.filter_name)
        return filter_

    @property
    def filter_name(self):
        """Get filter name.

        Returns:
            (str): filter name.
        """
        return self.name_widget.text()

    def accept_and_close(self):
        """Create or modify filter and close dialog.

        Called when user clicks accept.
        """
        if not self.filter_name:
            return simple_message_dialog(
                "Invalid Name",
                "Name field must be filled in",
            )
        if self.is_editor:
            if (self.filter_name != self.original_name and
                    self.filter_name in self._tree_manager.field_filters_dict):
                return simple_message_dialog(
                    "Invalid Name",
                    "Cannot change name to {0} - a filter with this name "
                    "already exists".format(self.filter_name),
                )
            self._tree_manager.modify_field_filter(
                self.original_name,
                self.filter,
            )
        else:
            if self.filter_name in self._tree_manager.field_filters_dict:
                return simple_message_dialog(
                    "Invalid Name",
                    "A filter called {0} already exists".format(self.filter_name)
                )
            self._tree_manager.add_field_filter(self.filter)
        self.accept()
        self.close()

    def delete_filter_and_close(self):
        """Delete filter and close dialog.

        Called when user clicks delete.
        """
        self._tree_manager.remove_field_filter(self.original_name)
        self.reject()
        self.close()
