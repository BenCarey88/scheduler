"""Utility methods for laying out qt widgets."""

from PyQt5 import QtCore, QtGui, QtWidgets


def add_widgets_horizontally(vertical_layout, *widget_list, frame=False):
    """Layout a list of widgets horizontally and add to a vertical layout.

    Args:
        vertical_layout (QVBoxLayout): layout to add to.
        widget_list (list(QWidget)): widgets to add.
        frame (bool): if True, add a frame.
    """
    horizontal_layout = QtWidgets.QHBoxLayout()
    for widget in widget_list:
        horizontal_layout.addWidget(widget)
    if frame:
        frame_widget = QtWidgets.QFrame()
        frame_widget.setLayout(horizontal_layout)
        vertical_layout.addWidget(frame_widget)
    else:
        vertical_layout.addLayout(horizontal_layout)


def add_field_widget(vertical_layout, field_name, field_widget):
    """Add a label and widget representing a field and its value.

    Args:
        vertical_layout (QVBoxLayout): layout to add to.
        field_name (str): name of field that this widget edits.
        field_widget (QWidget): the widget that edits this field

    Returns:
        (QWidget): the field widget.
    """
    label = QtWidgets.QLabel(field_name)
    add_widgets_horizontally(vertical_layout, label, field_widget)
    return field_widget


def add_checkbox_field(vertical_layout, field_name, default=False, **kwargs):
    """Add a label and checkbox widget.

    Args:
        vertical_layout (QVBoxLayout): layout to add to.
        field_name (str): name of field that this widget edits.
        default (boolean): default value of checkbox.
        kwargs (dict): kwargs to pass to add_field_widget.

    Returns:
        (QComboBox): the combobox widget.
    """
    checkbox = QtWidgets.QCheckBox()
    if default:
        checkbox.setChecked(True)
    return add_field_widget(vertical_layout, field_name, checkbox, **kwargs)


def add_text_field(vertical_layout, field_name, default=None, **kwargs):
    """Add a label and text widget.

    Args:
        vertical_layout (QVBoxLayout): layout to add to.
        field_name (str): name of field that this widget edits.
        default (str or None): if given, set as the combobox default value.
        kwargs (dict): kwargs to pass to add_field_widget.

    Returns:
        (QLineEdit): the line edit widget.
    """
    line_edit = QtWidgets.QLineEdit()
    if default is not None:
        line_edit.setText(default)
    return add_field_widget(vertical_layout, field_name, line_edit, **kwargs)


def add_combobox_field(
        vertical_layout,
        field_name,
        values,
        default=None,
        **kwargs):
    """Add a label and combobox widget.

    Args:
        vertical_layout (QVBoxLayout): layout to add to.
        field_name (str): name of field that this widget edits.
        values (iterable): the possible values of the combobox.
        default (str or None): if given, set as the combobox default value.
        kwargs (dict): kwargs to pass to add_field_widget.

    Returns:
        (QComboBox): the combobox widget.
    """
    combobox = QtWidgets.QComboBox()
    combobox.addItems(values)
    if default is not None:
        combobox.setCurrentText(default)
    return add_field_widget(vertical_layout, field_name, combobox, **kwargs)
