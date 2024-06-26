"""Filter dialog for creating new filters."""

from collections import OrderedDict
from enum import Enum
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import (
    BaseDateTimeWrapper,
    Date,
    DateTime,
    Time,
)
from scheduler.api.enums import (
    CompositionOperator,
    ItemImportance,
    ItemSize,
    ItemStatus,
    OrderedStringEnum,
)
from scheduler.api.filter import FieldFilter, FilterOperator, FilterType
from scheduler.api.filter.tree_filters import (
    NoFilter,
    CompositeTreeFilter,
    TaskImportanceFilter,
    TaskPathFilter,
    TaskSizeFilter,
    TaskStatusFilter,
    TaskTypeFilter,
)
from scheduler.api.tree.task import TaskType
from scheduler.api.utils import fallback_value

from scheduler.ui.utils import (
    set_style,
    simple_message_dialog,
    ValueWidgetWrapper,
)


class FilterDialogError(Exception):
    """Base exception for filter dialog."""


class FilterFieldData(object):
    """Class defining a filter field."""
    def __init__(self, name, filter_class, values=None, value_type=str):
        """Initialise filter field.

        Args:
            name (str): name of field.
            filter_class (class): the corresponding filter class.
            values (OrderedStringEnum, list, or None): enum or list of possible
                predefined values for this field. If not given, it is assumed
                that the field's values are unrestricted.
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
            return (
                FilterOperator.get_base_ops() + FilterOperator.get_string_ops()
            )
        elif issubclass(self.value_type, (float, int, BaseDateTimeWrapper)):
            return (
                FilterOperator.get_base_ops() + FilterOperator.get_maths_ops()
            )
        elif issubclass(self.value_type, OrderedStringEnum):
            return (
                FilterOperator.get_base_ops() + FilterOperator.get_maths_ops()
            )
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
        if (operator in FilterOperator.get_string_ops()
                and issubclass(self.value_type, str)):
            return ValueWidgetWrapper(QtWidgets.QLineEdit())
        elif self.values is None:
            if issubclass(self.value_type, Date):
                return ValueWidgetWrapper(QtWidgets.QDateEdit())
            if issubclass(self.value_type, DateTime):
                return ValueWidgetWrapper(QtWidgets.QDateTimeEdit())
            if issubclass(self.value_type, Time):
                return ValueWidgetWrapper(QtWidgets.QTimeEdit())
            if issubclass(self.value_type, str):
                return ValueWidgetWrapper(QtWidgets.QLineEdit())
        else:
            widget = QtWidgets.QComboBox()
            widget.addItems(self.values)
            return ValueWidgetWrapper(widget)
        raise FilterDialogError(
            "Cannot get widget for field {0} with operator of type {1}"
            "".format(self.name, operator)
        )


class FilterField(Enum):
    """Filter fields"""
    STATUS = FilterFieldData(
        "Status",
        TaskStatusFilter,
        ItemStatus,
        OrderedStringEnum,
    )
    TYPE = FilterFieldData(
        "Type",
        TaskTypeFilter,
        TaskType,
    )
    SIZE = FilterFieldData(
        "Size",
        TaskSizeFilter,
        ItemSize,
        OrderedStringEnum,
    )
    IMPORTANCE = FilterFieldData(
        "Importance",
        TaskImportanceFilter,
        ItemImportance,
        OrderedStringEnum,
    )
    PATH = FilterFieldData(
        "Path",
        TaskPathFilter,
    )

    @classmethod
    def iter_fields(cls):
        """Iterate through fields in enum.

        Yields:
            (FilterFieldData): the filter fields.
        """
        for field in cls.__members__.values():
            yield field.value

    @classmethod
    def get_field(cls, name):
        """Get filter field with given name.

        Args:
            name (str): name of field.

        Returns:
            (FilterFieldData or None): the field with that name, if found.
        """
        for field in cls.__members__.values():
            if field.value.name == name:
                return field.value
        return None

    @classmethod
    def field_names(cls):
        """Get all field names.

        Returns:
            (list(str)): list of field names.
        """
        return [field.value.name for field in cls.__members__.values()]


class FieldWidget(QtWidgets.QWidget):
    """Widget defining a field in the dialog."""
    MAX_COMBOBOX_HEIGHT = 25

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
        self.field_combo_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.field_combo_box.addItems([""] + FilterField.field_names())
        self.main_layout.addWidget(self.field_combo_box)

        self.operator_combo_box = QtWidgets.QComboBox()
        self.operator_combo_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.main_layout.addWidget(self.operator_combo_box)

        self.value_widget_wrapper = self._default_value_widget_wrapper()
        self.value_widget_stack = QtWidgets.QStackedWidget()
        # self.value_widget_stack.setMaximumHeight(self.MAX_COMBOBOX_HEIGHT)
        self.value_widget_stack.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.value_widget_stack.addWidget(self.value_widget)
        self.value_widgets_cache = {("", ""): self.value_widget_wrapper}
        self.main_layout.addWidget(self.value_widget_stack)
        # self.main_layout.addWidget(self.value_widget)

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
        field = FilterField.get_field(field_name)
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
        # self.main_layout.removeWidget(self.value_widget)
        # self.value_widget.deleteLater()
        field_name = self.field_combo_box.currentText()
        field = FilterField.get_field(field_name)
        if not field:
            self.value_widget_wrapper = self.value_widgets_cache[("", "")]
            # self.value_widget_wrapper = self._default_value_widget_wrapper()
            # self.main_layout.addWidget(self.value_widget)
            self.value_widget_stack.setCurrentWidget(self.value_widget)
            return
        operator = fallback_value(
            operator,
            self.operator_combo_box.currentText(),
        )
        # self.value_widget_wrapper = field.get_value_widget_wrapper(operator)
        # self.main_layout.addWidget(self.value_widget)
        self.value_widget_wrapper = self.value_widgets_cache.get(
            (field, operator)
        )
        if self.value_widget_wrapper is None:
            self.value_widget_wrapper = field.get_value_widget_wrapper(
                operator
            )
            self.value_widget_stack.addWidget(self.value_widget)
            self.value_widgets_cache[(field, operator)] = (
                self.value_widget_wrapper
            )
        self.value_widget_stack.setCurrentWidget(self.value_widget)

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
        field = FilterField.get_field(field_name)
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
        for field in FilterField.iter_fields():
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
            composition_operator or CompositionOperator.OR
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
            [CompositionOperator.OR, CompositionOperator.AND]
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
        if not self.subfilters:
            self.add_filter_widget()

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
            operator = CompositionOperator.OR
            if self.composition_operator == CompositionOperator.OR:
                # use opposite operator to current one
                operator = CompositionOperator.AND
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
            return cls([filter_], CompositionOperator.OR)
        return cls()


class FilterDialog(QtWidgets.QDialog):
    """Dialog for creating and editing filters."""
    MINIMUM_WIDTH = 500

    def __init__(
            self,
            filter_manager,
            filter=None,
            parent=None):
        """Initialise dialog.

        Args:
            filter_manager (FilterManager): the task tree manager object.
            filter (BaseFilter or None): filter we're editing if given, else
                we're in create mode.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(FilterDialog, self).__init__(parent=parent)
        set_style(self, "filter_dialog.qss")
        self._filter_manager = filter_manager
        self.is_editor = (filter is not None)
        self.original_name = filter.name if filter is not None else None
        filter_type = filter_manager.filter_type
        if filter is not None:
            filter_type = filter.filter_type

        self.setWindowTitle("Filter Manager")
        flags = QtCore.Qt.WindowFlags(
            QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setMinimumWidth(self.MINIMUM_WIDTH)

        # all layouts
        main_layout = QtWidgets.QVBoxLayout()
        filter_type_layout = QtWidgets.QHBoxLayout()
        name_layout = QtWidgets.QHBoxLayout()
        buttons_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(name_layout)
        main_layout.addLayout(filter_type_layout)
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

        # Filter type layout
        filter_type_layout.addWidget(QtWidgets.QLabel("Filter Type"))
        self.cb_filter_type = QtWidgets.QComboBox()
        self.cb_filter_type.addItems(FilterType.scheduler_filter_types())
        if filter_type is not None:
            self.cb_filter_type.setCurrentText(filter_type)
        filter_type_layout.addWidget(self.cb_filter_type)
        filter_type_layout.addStretch()

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
            if (self.filter_name in self._filter_manager.field_filters_dict
                    and self.filter_name != self.original_name):
                return simple_message_dialog(
                    "Invalid Name",
                    "Cannot change name to {0} - a filter with this name "
                    "already exists".format(self.filter_name),
                )
            self._filter_manager.modify_field_filter(
                [self.original_name],
                self.filter,
            )
        else:
            if self.filter_name in self._filter_manager.field_filters_dict:
                return simple_message_dialog(
                    "Invalid Name",
                    "A filter called {0} already exists".format(
                        self.filter_name
                    )
                )
            self._filter_manager.add_field_filter(
                self.filter,
                [self.filter.name],
            )
        self.accept()
        self.close()

    def delete_filter_and_close(self):
        """Delete filter and close dialog.

        Called when user clicks delete.
        """
        self._filter_manager.remove_field_filter([self.original_name])
        self.reject()
        self.close()
